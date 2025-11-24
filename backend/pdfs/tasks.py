from background_task import background
# --- UPDATED IMPORT ---
from chatbot.engine import add_pdf_to_workspace_index

# This registers our function as a background task
@background(schedule=5) # 5-second delay
def process_pdf_task(pdf_document_id):
    """
    A simple wrapper task that calls the main processing function
    from our chatbot engine.
    """
    print(f"Background task received for PDF ID: {pdf_document_id}")
    
    # --- UPDATED FUNCTION CALL ---
    # Call the new function that adds the PDF to the *workspace* index
    add_pdf_to_workspace_index(pdf_document_id)