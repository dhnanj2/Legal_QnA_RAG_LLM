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
session_state = {
    "active_index": "cuad",
    "cuad_index": None,
    "pdf_index": None,
    "cuad_chunks": [],
    "pdf_chunks": []
}

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
    session_id: str = Form(None)  # session ID from frontend
):
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID.")

    # Create a session if it doesn't exist
    if session_state["active_index"] == "pdf":
        chunks = session_state["pdf_chunks"]
        index = session_state["pdf_index"]
    else:
        chunks = session_state["cuad_chunks"]
        index = session_state["cuad_index"]

    # actual RAG QA
    top_chunks, confidence_score = retrieve_top_k(question, index, chunks)
    answer = generate_answer(question, top_chunks)

    return {
        "answer": answer,
        "source_chunks": top_chunks,
        "confidence_score": round(confidence_score, 3)
    }
