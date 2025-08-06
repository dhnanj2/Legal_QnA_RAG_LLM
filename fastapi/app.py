from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import shutil
from fastapi.responses import JSONResponse
from utils import (
    load_or_build_cuad_index,
    process_pdf_to_index,
    retrieve_top_k,
    generate_answer
)

app = FastAPI()

# Session state
session_state = {}

@app.on_event("startup")
def load_indices():
    # Load or build CUAD index
    print("🔄 Loading CUAD index...")
    idx, chunks = load_or_build_cuad_index("../data/full_contracts_txt")
    session_state["cuad_index"] = idx
    session_state["cuad_chunks"] = chunks
    print("✅ CUAD index loaded.")

@app.get("/")
def root():
    return {"message": "Welcome to Legal Document Question-Answering System"}

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Save the uploaded file
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Call your utility to process it
    try:
        session_state["pdf_index"], session_state["pdf_chunks"] = process_pdf_to_index(file_location)
        session_state["active_index"] = "pdf"
        return {"message": f"{file.filename} uploaded and indexed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
def ask_question(
    question: str = Form(...),
    session_id: str = Form(None)  # ← Accept session ID from frontend
):
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID.")

    # Create a session if it doesn't exist
    if session_id not in session_state:
        session_state[session_id] = {
            "active_index": "cuad",
            "pdf_index": None,
            "pdf_chunks": [],
        }

    # 🔑 Here's your current_session
    current_session = session_state[session_id]

    # Decide which index and chunks to use
    if current_session["active_index"] == "pdf" and current_session["pdf_index"]:
        index = current_session["pdf_index"]
        chunks = current_session["pdf_chunks"]
    elif session_state.get("cuad_index") and session_state.get("cuad_chunks"):
        index = session_state["cuad_index"]
        chunks = session_state["cuad_chunks"]
    else:
        raise HTTPException(status_code=500, detail="No valid index available.")

    # Do the actual RAG QA
    top_chunks = retrieve_top_k(question, index, chunks)
    answer = generate_answer(question, top_chunks)

    return {
        "answer": answer,
        "source_chunks": top_chunks
    }
