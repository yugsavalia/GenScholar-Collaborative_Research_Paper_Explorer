import os
import base64
from functools import lru_cache
from django.conf import settings

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
from unstructured.partition.pdf import partition_pdf
from langchain_cohere import CohereEmbeddings 


# --- 1. LOAD MODELS (These load ONCE when Django starts) ---

try:
    print("Loading Embedding Model (Cohere)...")
    EMBEDDINGS = CohereEmbeddings(
        model="embed-english-v3.0",
        cohere_api_key=os.getenv("COHERE_API_KEY")
    )
    print(" Cohere Embedding Model Loaded.")
except Exception as e:
    print(f" Error loading Cohere embedding model: {e}")
    EMBEDDINGS = None

# Your CHAT model (Gemini Flash)
try:
    print("Loading Chat LLM (gemini-flash-latest)...")
    LLM = ChatGoogleGenerativeAI(
        model="gemini-flash-latest",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.2,
    )
    print(" Google Chat LLM Loaded.")
except Exception as e:
    print(f" Error loading Google Chat LLM: {e}")
    LLM = None

# Your Q&A Chain (Unchanged)
PROMPT = ChatPromptTemplate.from_template("""
You are a helpful research assistant. Use the provided context from one or more research papers to answer the question.
If the answer is not found in the context, say "I cannot find that information in the provided documents."

Context:
{context}

Question:
{question}
""")
PARSER = StrOutputParser()
QA_CHAIN = PROMPT | LLM | PARSER


# --- 2. PDF PROCESSING FUNCTION (Using unstructured) ---

def add_pdf_to_workspace_index(pdf_id):
    """
    Background task:
    Takes a PDFFile ID, loads its TEXT using unstructured, and adds the text 
    (along with filename/title) to the workspace's FAISS index.
    """
    try:
        doc = PDFFile.objects.get(id=pdf_id)
        workspace = doc.workspace
    except PDFFile.DoesNotExist:
        print(f"Task failed: PDFFile with id {pdf_id} not found.")
        return

    if EMBEDDINGS is None:
        print("Task failed: The Embedding model is not loaded.")
        workspace.processing_status = Workspace.ProcessingStatus.FAILED
        workspace.save()
        return

    workspace.processing_status = Workspace.ProcessingStatus.PROCESSING
    workspace.save()

    try:
        pdf_path = doc.file.path
        
        # --- Get title and filename ---
        pdf_title = doc.title
        pdf_filename = os.path.basename(doc.file.name)
        source_info = f"Source Document Information: Filename is '{pdf_filename}'. Title is '{pdf_title}'.\n\nContent from this source follows:\n"
        
        # 1. Partition the PDF using unstructured (text-only strategy)
        print(f"[Task {doc.id}] Partitioning text from PDF: {pdf_path}...")
   
        elements = partition_pdf(filename=pdf_path, strategy="fast")

        documents_with_source = []
        for element in elements:
            # We only care about text elements
            if element.category == "Text":
                documents_with_source.append(
                    Document(
                        page_content=f"{source_info}{element.text}",
                        metadata={"source": doc.file.name}
                    )
                )

        if not documents_with_source:
             raise ValueError("No text could be extracted by unstructured.")

        # 2. Split all collected text
        print(f"[Task {doc.id}] Splitting text into chunks...")
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(documents_with_source)

        if not chunks:
            raise ValueError("Failed to create chunks from documents.")

        # 3. Define the *workspace's* index path (Unchanged)
        if not workspace.index_path:
            index_name = f"workspace_index_{workspace.id}"
            index_save_path = os.path.join(settings.MEDIA_ROOT, 'vector_indexes', index_name)
            workspace.index_path = index_save_path
            os.makedirs(index_save_path, exist_ok=True)
        else:
            index_save_path = workspace.index_path

        # 4. Load existing index or create new one (Unchanged)
        if os.path.exists(os.path.join(index_save_path, "index.faiss")):
            print(f"[Task {doc.id}] Loading existing index from: {index_save_path}")
            vectorstore = FAISS.load_local(
                index_save_path, 
                EMBEDDINGS, 
                allow_dangerous_deserialization=True
            )
            print(f"[Task {doc.id}] Adding {len(chunks)} new chunks to index...")
            vectorstore.add_documents(chunks)
        else:
            print(f"[Task {doc.id}] Creating new index at: {index_save_path}")
            vectorstore = FAISS.from_documents(chunks, EMBEDDINGS)

        # 5. Save the (new or merged) index back to disk (Unchanged)
        vectorstore.save_local(index_save_path)

        # 6. Update database models (Unchanged)
        doc.is_indexed = True
        doc.save()
        workspace.processing_status = Workspace.ProcessingStatus.READY
        workspace.save()
        
        print(f"[Task {doc.id}] ✅ Processing complete. Workspace {workspace.id} is READY.")

    except Exception as e:
        print(f"[Task {doc.id}] ❌ Processing failed: {e}")
        workspace.processing_status = Workspace.ProcessingStatus.FAILED
        workspace.save()


# --- 3. CHATBOT QUERY FUNCTIONS (This section is 100% UNCHANGED) ---
# (get_cached_vector_store and get_chatbot_response are the same as before)

@lru_cache(maxsize=10)
def get_cached_vector_store(index_path):
    if not os.path.exists(index_path):
        raise FileNotFoundError("Index path does not exist.")
    print(f"Loading index from disk: {index_path}")
    return FAISS.load_local(
        index_path, 
        EMBEDDINGS, 
        allow_dangerous_deserialization=True
    )

def get_chatbot_response(question, workspace_id):
    try:
        workspace = Workspace.objects.get(id=workspace_id)
    except Workspace.DoesNotExist:
        return "Error: This workspace does not exist."

    if workspace.processing_status == Workspace.ProcessingStatus.NONE:
        return "No documents have been processed for this workspace yet."
    if workspace.processing_status == Workspace.ProcessingStatus.PROCESSING:
        return "The chatbot is currently processing new documents. Please wait a moment and try again."
    if workspace.processing_status == Workspace.ProcessingStatus.FAILED:
        return "Processing failed for one or more documents. The bot may have incomplete knowledge."
    if not workspace.index_path:
        return "Error: This workspace is ready but its index path is missing."

    try:
        vectorstore = get_cached_vector_store(workspace.index_path)
        relevant_docs = vectorstore.similarity_search(question, k=5)
        
        if not relevant_docs:
            return "I could not find any relevant information about that in the workspace documents."

        context = "\n\n".join([doc.page_content for doc in relevant_docs])

        if not QA_CHAIN:
            return "Error: The chatbot LLM is not initialized."
            
        answer = QA_CHAIN.invoke({"context": context, "question": question})
        return answer
        
    except FileNotFoundError:
        return "Error: The index file for this workspace is missing. Please try re-uploading a document."
    except Exception as e:
        print(f"Error in get_chatbot_response: {e}")
        return "An internal error occurred while getting the answer."
