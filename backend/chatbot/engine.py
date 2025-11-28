# import os
# import base64
# from functools import lru_cache
# from django.conf import settings

# # Import models from other apps
# from pdfs.models import PDFFile
# from workspaces.models import Workspace

# # LangChain/AI Imports
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.vectorstores import FAISS
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.documents import Document

# # --- UPDATED IMPORTS ---
# # We are now using unstructured
# from unstructured.partition.pdf import partition_pdf
# # Using Cohere as requested
# from langchain_cohere import CohereEmbeddings 


# # --- 1. LOAD MODELS (These load ONCE when Django starts) ---

# # Your embedding model (Cohere)
# try:
#     print("Loading Embedding Model (Cohere)...")
#     EMBEDDINGS = CohereEmbeddings(
#         model="embed-english-v3.0",
#         cohere_api_key=os.getenv("COHERE_API_KEY")
#     )
#     print("✅ Cohere Embedding Model Loaded.")
# except Exception as e:
#     print(f"❌ Error loading Cohere embedding model: {e}")
#     EMBEDDINGS = None

# # Your CHAT model (Gemini Flash)
# try:
#     print("Loading Chat LLM (gemini-flash-latest)...")
#     LLM = ChatGoogleGenerativeAI(
#         model="gemini-flash-latest",
#         google_api_key=os.getenv("GOOGLE_API_KEY"),
#         temperature=0.2,
#     )
#     print("✅ Google Chat LLM Loaded.")
# except Exception as e:
#     print(f"❌ Error loading Google Chat LLM: {e}")
#     LLM = None

# # Your Q&A Chain (Unchanged)
# PROMPT = ChatPromptTemplate.from_template("""
# You are a helpful research assistant. Use the provided context from one or more research papers to answer the question.
# If the answer is not found in the context, say "I cannot find that information in the provided documents."

# Context:
# {context}

# Question:
# {question}
# """)
# PARSER = StrOutputParser()
# QA_CHAIN = PROMPT | LLM | PARSER


# # --- 2. PDF PROCESSING FUNCTION (Using unstructured) ---

# def add_pdf_to_workspace_index(pdf_id):
#     """
#     Background task:
#     Takes a PDFFile ID, loads its TEXT using unstructured, and adds the text 
#     (along with filename/title) to the workspace's FAISS index.
#     """
#     try:
#         doc = PDFFile.objects.get(id=pdf_id)
#         workspace = doc.workspace
#     except PDFFile.DoesNotExist:
#         print(f"Task failed: PDFFile with id {pdf_id} not found.")
#         return

#     if EMBEDDINGS is None:
#         print("Task failed: The Embedding model is not loaded.")
#         workspace.processing_status = Workspace.ProcessingStatus.FAILED
#         workspace.save()
#         return

#     workspace.processing_status = Workspace.ProcessingStatus.PROCESSING
#     workspace.save()

#     try:
#         pdf_path = doc.file.path
        
#         # --- Get title and filename ---
#         pdf_title = doc.title
#         pdf_filename = os.path.basename(doc.file.name)
#         source_info = f"Source Document Information: Filename is '{pdf_filename}'. Title is '{pdf_title}'.\n\nContent from this source follows:\n"
        
#         # --- THIS IS THE FIX ---
#         # 1. Partition the PDF using unstructured (text-only strategy)
#         print(f"[Task {doc.id}] Partitioning text from PDF: {pdf_path}...")
#         # strategy="fast" is text-only and does not require Poppler
#         elements = partition_pdf(filename=pdf_path, strategy="fast")

#         documents_with_source = []
#         for element in elements:
#             # We only care about text elements
#             if element.category == "Text":
#                 documents_with_source.append(
#                     Document(
#                         page_content=f"{source_info}{element.text}",
#                         metadata={"source": doc.file.name}
#                     )
#                 )

#         if not documents_with_source:
#              raise ValueError("No text could be extracted by unstructured.")

#         # 2. Split all collected text
#         print(f"[Task {doc.id}] Splitting text into chunks...")
#         splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
#         chunks = splitter.split_documents(documents_with_source)

#         if not chunks:
#             raise ValueError("Failed to create chunks from documents.")

#         # 3. Define the *workspace's* index path (Unchanged)
#         if not workspace.index_path:
#             index_name = f"workspace_index_{workspace.id}"
#             index_save_path = os.path.join(settings.MEDIA_ROOT, 'vector_indexes', index_name)
#             workspace.index_path = index_save_path
#             os.makedirs(index_save_path, exist_ok=True)
#         else:
#             index_save_path = workspace.index_path

#         # 4. Load existing index or create new one (Unchanged)
#         if os.path.exists(os.path.join(index_save_path, "index.faiss")):
#             print(f"[Task {doc.id}] Loading existing index from: {index_save_path}")
#             vectorstore = FAISS.load_local(
#                 index_save_path, 
#                 EMBEDDINGS, 
#                 allow_dangerous_deserialization=True
#             )
#             print(f"[Task {doc.id}] Adding {len(chunks)} new chunks to index...")
#             vectorstore.add_documents(chunks)
#         else:
#             print(f"[Task {doc.id}] Creating new index at: {index_save_path}")
#             vectorstore = FAISS.from_documents(chunks, EMBEDDINGS)

#         # 5. Save the (new or merged) index back to disk (Unchanged)
#         vectorstore.save_local(index_save_path)

#         # 6. Update database models (Unchanged)
#         doc.is_indexed = True
#         doc.save()
#         workspace.processing_status = Workspace.ProcessingStatus.READY
#         workspace.save()
        
#         print(f"[Task {doc.id}] ✅ Processing complete. Workspace {workspace.id} is READY.")

#     except Exception as e:
#         print(f"[Task {doc.id}] ❌ Processing failed: {e}")
#         workspace.processing_status = Workspace.ProcessingStatus.FAILED
#         workspace.save()


# # --- 3. CHATBOT QUERY FUNCTIONS (This section is 100% UNCHANGED) ---
# # (get_cached_vector_store and get_chatbot_response are the same as before)

# @lru_cache(maxsize=10)
# def get_cached_vector_store(index_path):
#     if not os.path.exists(index_path):
#         raise FileNotFoundError("Index path does not exist.")
#     print(f"Loading index from disk: {index_path}")
#     return FAISS.load_local(
#         index_path, 
#         EMBEDDINGS, 
#         allow_dangerous_deserialization=True
#     )

# def get_chatbot_response(question, workspace_id):
#     try:
#         workspace = Workspace.objects.get(id=workspace_id)
#     except Workspace.DoesNotExist:
#         return "Error: This workspace does not exist."

#     if workspace.processing_status == Workspace.ProcessingStatus.NONE:
#         return "No documents have been processed for this workspace yet."
#     if workspace.processing_status == Workspace.ProcessingStatus.PROCESSING:
#         return "The chatbot is currently processing new documents. Please wait a moment and try again."
#     if workspace.processing_status == Workspace.ProcessingStatus.FAILED:
#         return "Processing failed for one or more documents. The bot may have incomplete knowledge."
#     if not workspace.index_path:
#         return "Error: This workspace is ready but its index path is missing."

#     try:
#         vectorstore = get_cached_vector_store(workspace.index_path)
#         relevant_docs = vectorstore.similarity_search(question, k=5)
        
#         if not relevant_docs:
#             return "I could not find any relevant information about that in the workspace documents."

#         context = "\n\n".join([doc.page_content for doc in relevant_docs])

#         if not QA_CHAIN:
#             return "Error: The chatbot LLM is not initialized."
            
#         answer = QA_CHAIN.invoke({"context": context, "question": question})
#         return answer
        
#     except FileNotFoundError:
#         return "Error: The index file for this workspace is missing. Please try re-uploading a document."
#     except Exception as e:
#         print(f"Error in get_chatbot_response: {e}")
#         return "An internal error occurred while getting the answer."


import os
import json 
import traceback
import io
import tempfile
from functools import lru_cache
from django.conf import settings
from django.db import models  # <--- THIS IS THE FIX

# Import models from other apps
from pdfs.models import PDFFile
from workspaces.models import Workspace

# LangChain/AI Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_cohere import CohereEmbeddings 


# --- 1. LOAD MODELS (Unchanged) ---
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
            timeout=30  # 30 second timeout for API calls
        )
        print("[OK] Google Chat LLM Loaded.")
except Exception as e:
    print(f"[ERROR] Error loading Google Chat LLM: {e}")
    import traceback
    traceback.print_exc()
    LLM = None

PARSER = StrOutputParser()

# --- 2. UPDATED CLASSIFIER CHAIN (Unchanged) ---
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


# Your Q&A Chain (Unchanged)
QA_PROMPT = ChatPromptTemplate.from_template("""
You are a helpful research assistant. Use the provided context...
...
Context:
{context}

Question:
{question}
""")
QA_CHAIN = QA_PROMPT | LLM | PARSER


# --- 3. PDF PROCESSING FUNCTION (Unchanged) ---

def add_pdf_to_workspace_index(pdf_id):
    """
    Background task:
    Saves summary/abstract to the *PDFFile model* itself.
    """
    try:
        doc = PDFFile.objects.get(id=pdf_id) # 'doc' is the PDFFile object
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
        # Get PDF bytes from BinaryField
        pdf_bytes = doc.file
        pdf_title = doc.title
        pdf_filename = f"{doc.title}.pdf"
        # Use the PDF's *own title* in the source info
        source_info = f"Source Document: {pdf_title} (filename: {pdf_filename})\n\nContent follows:\n"
        
        # Create a temporary file to store PDF bytes (PDFPlumberLoader needs a file path)
        print(f"[Task {doc.id}] Loading text from PDF with PDFPlumber from database bytes...")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(pdf_bytes)
            temp_file_path = temp_file.name
        
        try:
            loader = PDFPlumberLoader(temp_file_path)
            pages = loader.load()
        finally:
            # Clean up temporary file
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
            page.page_content = f"{source_info}{cleaned_content}"
            documents_with_source.append(page)

        print(f"[Task {doc.id}] Splitting text into chunks...")
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(documents_with_source)

        if not chunks:
            raise ValueError("Failed to create chunks from documents.")

        # ... (Rest of the FAISS index creation is UNCHANGED) ...
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

        # --- Update database models ---
        doc.is_indexed = True
        doc.save() # <-- This now saves the summary/abstract to the PDFFile
        
        workspace.processing_status = Workspace.ProcessingStatus.READY
        workspace.save() # <-- This just saves the workspace status
        
        print(f"[Task {doc.id}] [OK] Processing complete. Workspace {workspace.id} is READY.")

    except Exception as e:
        print(f"[Task {doc.id}] [ERROR] Processing failed: {e}")
        print(traceback.format_exc())
        workspace.processing_status = Workspace.ProcessingStatus.FAILED
        workspace.save()


# --- 4. CHATBOT QUERY FUNCTIONS (Unchanged, but now fixed) ---

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
        # Fallback if the LLM doesn't return valid JSON
        return {'intent': 'pdf_question', 'doc_name': 'all'}


def get_chatbot_response(question, workspace_id):
    """
    (Unchanged)
    UPDATED: This router is now document-aware.
    """
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

        # --- Route 1: Off-Topic ---
        if intent == 'off_topic':
            return "I cannot find that information in the provided documents."

        # --- Route 2: Summary or Abstract ---
        if intent == 'summary' or intent == 'abstract':
            
            # --- Sub-Route A: Summary/Abstract of ALL docs (Unchanged) ---
            if doc_name == 'all':
                all_pdfs = PDFFile.objects.filter(workspace=workspace)
                if not all_pdfs.exists():
                    return "There are no documents in this workspace."
                
                # Gather all summaries or abstracts
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

            # ---
            # --- Sub-Route B: Summary/Abstract of a SPECIFIC doc (THIS IS THE FIX) ---
            # ---
            else:
                try:
                    # --- NEW "BEST MATCH" KEYWORD SEARCH ---
                    
                    # Get all PDFs in the workspace first
                    all_pdfs = PDFFile.objects.filter(workspace=workspace)
                    if not all_pdfs.exists():
                        return "There are no documents in this workspace."

                    # Clean the doc_name into search terms
                    keywords = doc_name.lower().split()
                    stop_words = {'pdf', 'paper', 'document', 'summary', 'abstract', 'of', 'in', 'short'}
                    search_terms = [k for k in keywords if k not in stop_words]

                    if not search_terms: # User just said "pdf" or "summary"
                         return "Please be more specific about which document you mean."

                    best_match = None
                    best_score = 0

                    # Loop through each PDF and "score" it against the search terms
                    for pdf in all_pdfs:
                        # Create a single string of all searchable text for this PDF
                        search_corpus = " ".join(filter(None, [
                            pdf.title,
                            f"{pdf.title}.pdf",  # Use title as filename since file is BinaryField
                            pdf.summary,
                            pdf.abstract
                        ])).lower()
                        
                        current_score = 0
                        for term in search_terms:
                            if term in search_corpus:
                                current_score += 1 # Add 1 point for each matching keyword
                        
                        if current_score > best_score:
                            best_score = current_score
                            best_match = pdf

                    # We require at least one keyword to match
                    if not best_match:
                        return f"I could not find a document closely matching '{doc_name}'."
                    
                    # We found the best matching PDF. Now get its content.
                    print(f"Keyword search for '{doc_name}' matched PDF: {best_match.title}")
                    
                    content = best_match.summary if intent == 'summary' else best_match.abstract
                    if not content or content == 'N/A':
                        return f"A {intent} has not been generated (or was not found) for {best_match.title}."
                    
                    return content
                    
                except Exception as e:
                    print(f"Error finding specific doc: {e}")
                    return "I had trouble finding that specific document."
                
        # --- Route 3: PDF Question (RAG) ---
        if intent == 'pdf_question':
            # (This is the original RAG logic, unchanged)
            if not workspace.index_path:
                return "Error: This workspace is ready but its index path is missing."
            try:
                vectorstore = get_cached_vector_store(workspace.index_path)
                relevant_docs = vectorstore.similarity_search(question, k=5)
                
                if not relevant_docs:
                    return "I could not find any relevant information about that in the workspace documents."

                context = "\n\n".join([doc.page_content for doc in relevant_docs])
                print(f"[RAG] Found {len(relevant_docs)} relevant documents, context length: {len(context)} chars")

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