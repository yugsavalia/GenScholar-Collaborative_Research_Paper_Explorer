
import os
import json 
import traceback
import io
import tempfile
import re
from difflib import SequenceMatcher
from functools import lru_cache
from django.conf import settings
from django.db import models  
from pdfs.models import PDFFile
from workspaces.models import Workspace

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_cohere import CohereEmbeddings 


try:
    print("Loading Embedding Model (Cohere)...")
    EMBEDDINGS = CohereEmbeddings(model="embed-english-v3.0", cohere_api_key=os.getenv("COHERE_API_KEY"))
    print("[OK] Cohere Embedding Model Loaded.")
except Exception as e:
    print(f"[ERROR] Error loading Cohere embedding model: {e}")
    EMBEDDINGS = None

try:
    print("Loading Chat LLM (gemini-flash-latest)...")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("[ERROR] GOOGLE_API_KEY environment variable is not set!")
        LLM = None
    else:
        LLM = ChatGoogleGenerativeAI(
            model="gemini-flash-latest", 
            google_api_key=google_api_key, 
            temperature=0.2,
            timeout=30 
        )
        print("[OK] Google Chat LLM Loaded.")
except Exception as e:
    print(f"[ERROR] Error loading Google Chat LLM: {e}")
    import traceback
    traceback.print_exc()
    LLM = None

PARSER = StrOutputParser()


CLASSIFIER_PROMPT = ChatPromptTemplate.from_template("""
You are a router. Analyze the user query and return a JSON object with two keys: "intent" and "doc_name".

Possible "intent" values:
- "summary": User wants a summary.
- "abstract": User wants an abstract.
- "pdf_question": User wants to ask a Q&A question about the content.
- "off_topic": User is asking a general knowledge question.

For "doc_name":
- If the user specifies a document (e.g., "pdf1", "the paper on optimizers", "EJ1172284"), extract that name or title.
- If the user asks about "both", "all", or "all documents", return "all".
- If the user doesn't specify (e.g., "explain in short"), return "all".

Examples:
Query: "give summary of pdf1 in very very short"
{{"intent": "summary", "doc_name": "pdf1"}}

Query: "give summary of both pdfs"
{{"intent": "summary", "doc_name": "all"}}

Query: "what is a query optimizer?"
{{"intent": "pdf_question", "doc_name": "all"}}

Query: "explain pdf in short"
{{"intent": "summary", "doc_name": "all"}}

Query: "what is the capital of France?"
{{"intent": "off_topic", "doc_name": "none"}}

User Query: "{question}"
JSON Output:
""")
JSON_PARSER = JsonOutputParser()
CLASSIFIER_CHAIN = CLASSIFIER_PROMPT | LLM | JSON_PARSER


QA_PROMPT = ChatPromptTemplate.from_template("""
You are a helpful research assistant. Use the provided context...
...
Context:
{context}

Question:
{question}
""")
QA_CHAIN = QA_PROMPT | LLM | PARSER


# --- HELPERS ---
SUMMARY_PLACEHOLDER = "Please provide the research paper text you would like me to summarize."

SUMMARY_HINT_PATTERN = re.compile(
    r"(?:summary|summaries|summarize|abstract|abstracts)\s+(?:of|for)\s+(.+?)(?:\s+(?:pdf|file|document)s?\b|$)",
    flags=re.IGNORECASE,
)

def _normalize_text(text):
    if not text:
        return ''
    lowered = text.lower()
    cleaned = re.sub(r'[^a-z0-9]+', ' ', lowered)
    return cleaned.strip()

DOCUMENT_MATCH_RATIO_THRESHOLD = 0.65


def _match_pdf_title(workspace, doc_name):
    """
    Return the best PDF and a normalized similarity ratio for the provided name.
    """
    normalized_target = _normalize_text(doc_name)
    if not normalized_target:
        return None, 0.0

    best_pdf = None
    best_ratio = 0.0

    for pdf in PDFFile.objects.filter(workspace=workspace):
        normalized_title = _normalize_text(pdf.title)
        if not normalized_title:
            continue

        if normalized_title == normalized_target or normalized_target in normalized_title or normalized_title in normalized_target:
            return pdf, 1.0

        ratio = SequenceMatcher(None, normalized_target, normalized_title).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_pdf = pdf

    return best_pdf, best_ratio


def _best_matching_pdf(workspace, doc_name):
    matched_pdf, _ = _match_pdf_title(workspace, doc_name)
    return matched_pdf


def _validate_specific_pdf_request(workspace, doc_name):
    
    if not doc_name or doc_name in ('all', 'none'):
        return None

    available_titles = list(workspace.pdf_files.values_list('title', flat=True))
    matched_pdf, ratio = _match_pdf_title(workspace, doc_name)
    print(f"[Guardrail] Requested '{doc_name}'. Available titles: {available_titles}")

    if not matched_pdf:
        print(f"[Guardrail] No matching title found for '{doc_name}'.")
        return None

    if ratio < DOCUMENT_MATCH_RATIO_THRESHOLD:
        print(f"[Guardrail] Best match '{matched_pdf.title}' too weak ({ratio:.2f}).")
        return None

    print(f"[Guardrail] '{doc_name}' resolved to '{matched_pdf.title}' (ratio={ratio:.2f}).")
    return matched_pdf


def _detect_pdf_from_query(workspace, query_text):
    normalized_query = _normalize_text(query_text)
    if not normalized_query:
        return None

    best_ratio = 0.0
    best_pdf = None

    for pdf in PDFFile.objects.filter(workspace=workspace):
        normalized_title = _normalize_text(pdf.title)
        if not normalized_title:
            continue

        if normalized_title in normalized_query or normalized_query in normalized_title:
            print(f"[FuzzyMatch] Substring match: '{pdf.title}' for query '{query_text}'")
            return pdf

        ratio = SequenceMatcher(None, normalized_query, normalized_title).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_pdf = pdf

    if best_ratio >= 0.65:
        print(f"[FuzzyMatch] SequenceMatcher match ({best_ratio:.2f}) for '{best_pdf.title}'")
        return best_pdf

    return None


def _extract_doc_name_from_query(query_text):
    if not query_text:
        return None
    match = SUMMARY_HINT_PATTERN.search(query_text)
    if not match:
        return None

    doc_hint = match.group(1).strip()
    doc_hint = re.sub(r"\b(?:pdf|file|document)s?\b", "", doc_hint, flags=re.IGNORECASE).strip()
    return doc_hint or None


def _resolve_target_pdf(workspace, doc_name_hint, user_query):
    if doc_name_hint and doc_name_hint not in ('all', 'none'):
        matched_pdf, ratio = _match_pdf_title(workspace, doc_name_hint)
        if matched_pdf:
            print(f"[Resolver] doc_name hint matched to '{matched_pdf.title}' (ratio={ratio:.2f})")
            return matched_pdf

    fuzzy_match = _detect_pdf_from_query(workspace, user_query)
    if fuzzy_match:
        print(f"[Resolver] Query-based match selected '{fuzzy_match.title}'")
    return fuzzy_match


def add_pdf_to_workspace_index(pdf_id):
    
    try:
        doc = PDFFile.objects.get(id=pdf_id) 
        workspace = doc.workspace
    except PDFFile.DoesNotExist:
        print(f"Task failed: PDFFile with id {pdf_id} not found.")
        return

    if EMBEDDINGS is None or LLM is None:
        print("Task failed: The Embedding or LLM models are not loaded.")
        workspace.processing_status = Workspace.ProcessingStatus.FAILED
        workspace.save()
        return

    workspace.processing_status = Workspace.ProcessingStatus.PROCESSING
    workspace.save()

    try:
        
        pdf_bytes = doc.file
        pdf_title = doc.title
        pdf_filename = f"{doc.title}.pdf"
        
        source_info = f"Source Document: {pdf_title} (filename: {pdf_filename})\n\nContent follows:\n"
        
        
        print(f"[Task {doc.id}] Loading text from PDF with PDFPlumber from database bytes...")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(pdf_bytes)
            temp_file_path = temp_file.name
        
        try:
            loader = PDFPlumberLoader(temp_file_path)
            pages = loader.load()
        finally:
            
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        if not pages:
             raise ValueError("No text could be extracted by PDFPlumber.")

        # --- Generate Summary & Abstract ---
        full_text = "\n\n".join([page.page_content for page in pages])

        print(f"[Task {doc.id}] Generating summary...")
        summary_prompt = ChatPromptTemplate.from_template("Provide a concise, 3-4 line summary of the following research paper text: {text}")
        summary_chain = summary_prompt | LLM | PARSER
        doc.summary = summary_chain.invoke({"text": full_text})

        print(f"[Task {doc.id}] Extracting abstract...")
        abstract_prompt = ChatPromptTemplate.from_template("Extract the 'abstract' section from this research paper text. Return only the abstract's text. If no abstract is found, just return 'N/A'.: {text}")
        abstract_chain = abstract_prompt | LLM | PARSER
        doc.abstract = abstract_chain.invoke({"text": full_text})

        # --- Inject source info into each page for Q&A indexing ---
        documents_with_source = []
        for page in pages:
            cleaned_content = " ".join(page.page_content.split())
            page_metadata = dict(page.metadata or {})
            page_metadata.update({
                "pdf_title": pdf_title,
                "pdf_id": doc.id,
                "pdf_filename": pdf_filename,
                "workspace_id": workspace.id,
            })
            documents_with_source.append(
                Document(
                    page_content=f"{source_info}{cleaned_content}",
                    metadata=page_metadata
                )
            )

        print(f"[Task {doc.id}] Splitting text into chunks...")
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(documents_with_source)

        if not chunks:
            raise ValueError("Failed to create chunks from documents.")

       
        if not workspace.index_path:
            index_name = f"workspace_index_{workspace.id}"
            index_save_path = os.path.join(settings.MEDIA_ROOT, 'vector_indexes', index_name)
            workspace.index_path = index_save_path
            os.makedirs(index_save_path, exist_ok=True)
        else:
            index_save_path = workspace.index_path

        if os.path.exists(os.path.join(index_save_path, "index.faiss")):
            print(f"[Task {doc.id}] Loading existing index from: {index_save_path}")
            vectorstore = FAISS.load_local(index_save_path, EMBEDDINGS, allow_dangerous_deserialization=True)
            print(f"[Task {doc.id}] Adding {len(chunks)} new chunks to index...")
            vectorstore.add_documents(chunks)
        else:
            print(f"[Task {doc.id}] Creating new index at: {index_save_path}")
            vectorstore = FAISS.from_documents(chunks, EMBEDDINGS)

        vectorstore.save_local(index_save_path)

        
        doc.is_indexed = True
        doc.save() 

        workspace.processing_status = Workspace.ProcessingStatus.READY
        workspace.save() 
        
        print(f"[Task {doc.id}] [OK] Processing complete. Workspace {workspace.id} is READY.")

    except Exception as e:
        print(f"[Task {doc.id}] [ERROR] Processing failed: {e}")
        print(traceback.format_exc())
        workspace.processing_status = Workspace.ProcessingStatus.FAILED
        workspace.save()



@lru_cache(maxsize=10)
def get_cached_vector_store(index_path):
    """ (Unchanged) """
    if not os.path.exists(index_path):
        raise FileNotFoundError("Index path does not exist.")
    print(f"Loading index from disk: {index_path}")
    return FAISS.load_local(index_path, EMBEDDINGS, allow_dangerous_deserialization=True)


def _get_query_classification(user_query):
    """
    (Unchanged)
    NEW internal helper function. Uses the JSON CLASSIFIER_CHAIN.
    """
    print(f"Classifying query: {user_query}")
    if not CLASSIFIER_CHAIN or LLM is None:
        print("Classifier chain not loaded. Defaulting to 'pdf_question'.")
        return {'intent': 'pdf_question', 'doc_name': 'all'}
    
    try:
        print(f"Invoking classifier chain...")
        result = CLASSIFIER_CHAIN.invoke({"question": user_query})
        print(f"Classification result: {result}")
        return result
    except Exception as e:
        print(f"Error in classification: {e}. Defaulting to pdf_question.")
        import traceback
        traceback.print_exc()
        return {'intent': 'pdf_question', 'doc_name': 'all'}


def get_chatbot_response(question, workspace_id):
    
    try:
        workspace = Workspace.objects.get(id=workspace_id)
    except Workspace.DoesNotExist:
        return "Error: This workspace does not exist."

    # --- 1. Handle Workspace Status (Unchanged) ---
    if workspace.processing_status == Workspace.ProcessingStatus.NONE:
        return "No documents have been processed..."
    if workspace.processing_status == Workspace.ProcessingStatus.PROCESSING:
        return "The chatbot is currently processing new documents..."
    if workspace.processing_status == Workspace.ProcessingStatus.FAILED:
        return "Processing failed for one or more documents..."

    # --- 2. Handle READY status (NEW ROUTER LOGIC) ---
    if workspace.processing_status == Workspace.ProcessingStatus.READY:
        
        # Step 1: Classify the user's intent
        classification = _get_query_classification(question)
        intent = classification.get('intent')
        doc_name = classification.get('doc_name')
        
        print(f"Router: Intent='{intent}', DocName='{doc_name}'")
        doc_hint = _extract_doc_name_from_query(question)
        specific_doc_name = None
        if doc_hint:
            specific_doc_name = doc_hint
        elif doc_name and doc_name not in ('all', 'none'):
            specific_doc_name = doc_name

        # --- Route 1: Off-Topic ---
        if intent == 'off_topic':
            return "I cannot find that information in the provided documents."

        # --- Route 2: Summary or Abstract ---
        if intent == 'summary' or intent == 'abstract':
            if specific_doc_name:
                try:
                    requested_pdf = _validate_specific_pdf_request(workspace, specific_doc_name)
                    if not requested_pdf:
                        return "PDF not available"

                    print(f"Best match for '{specific_doc_name}' is PDF: {requested_pdf.title}")

                    content = requested_pdf.summary if intent == 'summary' else requested_pdf.abstract
                    if not content or content == 'N/A' or content == SUMMARY_PLACEHOLDER:
                        return f"A {intent} is not yet available for '{requested_pdf.title}'. Please try again shortly."

                    return content

                except Exception as e:
                    print(f"Error finding specific doc: {e}")
                    return "I had trouble finding that specific document."

            if doc_name == 'all':
                all_pdfs = PDFFile.objects.filter(workspace=workspace)
                if not all_pdfs.exists():
                    return "There are no documents in this workspace."
                
                all_content = []
                for pdf in all_pdfs:
                    content = pdf.summary if intent == 'summary' else pdf.abstract
                    if content and content != 'N/A':
                        all_content.append(f"Document: {pdf.title}\n\n{content}")
                
                if not all_content:
                    return f"No {intent}s have been generated for the documents in this workspace."
                
                if len(all_content) == 1:
                    return all_content[0]
                
                combined_text = "\n\n---\n\n".join(all_content)
                combine_prompt = ChatPromptTemplate.from_template(f"Please create a single, cohesive {intent} based on the following individual document sections:\n\n{{text}}")
                combine_chain = combine_prompt | LLM | PARSER
                return combine_chain.invoke({"text": combined_text})

            return "Please clarify which document you want summarized."
                
                
        # --- Route 3: PDF Question (RAG) ---
        doc_requested = bool(specific_doc_name)
        requested_pdf = _validate_specific_pdf_request(workspace, specific_doc_name) if doc_requested else None

        if doc_requested and not requested_pdf:
            return "PDF not available"

        if intent == 'pdf_question':
            
            if not workspace.index_path:
                return "Error: This workspace is ready but its index path is missing."
            try:
                vectorstore = get_cached_vector_store(workspace.index_path)
                target_pdf = requested_pdf or _resolve_target_pdf(workspace, specific_doc_name, question)
                filter_kwargs = {"pdf_id": target_pdf.id} if target_pdf else None

                if target_pdf:
                    print(f"[RAG] Filtering context for PDF '{target_pdf.title}' (ID {target_pdf.id}).")

                relevant_docs = vectorstore.similarity_search(question, k=5, filter=filter_kwargs)
                
                if not relevant_docs:
                    if target_pdf:
                        return f"I could not find relevant information within '{target_pdf.title}'. Please try another question."
                    return "I could not find any relevant information about that in the workspace documents."

                context_chunks = []
                for chunk in relevant_docs:
                    metadata = getattr(chunk, "metadata", {}) or {}
                    source_label = metadata.get("pdf_title") or metadata.get("pdf_filename") or metadata.get("source") or "Unknown Document"
                    context_chunks.append(f"[{source_label}] {chunk.page_content}")
                context = "\n\n".join(context_chunks)
                print(f"[RAG] Found {len(relevant_docs)} relevant chunks, context length: {len(context)} chars")

                if not QA_CHAIN or LLM is None:
                    return "Error: The chatbot LLM is not initialized."
                
                print(f"[RAG] Invoking QA_CHAIN with question: {question[:100]}...")
                try:
                    answer = QA_CHAIN.invoke({"context": context, "question": question})
                    print(f"[RAG] QA_CHAIN completed, answer length: {len(answer) if answer else 0} chars")
                    return answer
                except Exception as e:
                    print(f"[RAG] Error in QA_CHAIN.invoke: {e}")
                    import traceback
                    traceback.print_exc()
                    return f"Error generating answer: {str(e)}"
            except Exception as e:
                print(f"Error in RAG part: {e}")
                return "An internal error occurred."
    
    return "Error: Workspace is in an unknown state."
