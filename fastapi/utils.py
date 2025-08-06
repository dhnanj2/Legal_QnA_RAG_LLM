import fitz
import faiss
import numpy as np
from pathlib import Path
import pickle
from dotenv import load_dotenv

from sentence_transformers import SentenceTransformer
from langchain.text_splitter import CharacterTextSplitter

import google.generativeai as genai
import os

# Global shared components
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables!")
genai.configure(api_key=api_key)

def load_or_build_cuad_index(txt_dir="../data/full_contracts_txt"):
    if Path("cuad_index.faiss").exists() and Path("cuad_chunks.pkl").exists():
        idx = faiss.read_index("cuad_index.faiss")
        with open("cuad_chunks.pkl", "rb") as f:
            chunks = pickle.load(f)
        return idx, chunks

    all_chunks = []
    for file in Path(txt_dir).glob("*.txt"):
        text = Path(file).read_text(encoding="utf-8")
        all_chunks.extend(splitter.split_text(text))

    embeddings = embedding_model.encode(all_chunks, show_progress_bar=True)
    idx = faiss.IndexFlatL2(embeddings.shape[1])
    idx.add(np.array(embeddings))

    faiss.write_index(idx, "cuad_index.faiss")
    with open("cuad_chunks.pkl", "wb") as f:
        pickle.dump(all_chunks, f)

    return idx, all_chunks

def process_pdf_to_index(pdf_path):
    doc = fitz.open(pdf_path)
    text = "".join(page.get_text() for page in doc)
    chunks = splitter.split_text(text)
    embeddings = embedding_model.encode(chunks, show_progress_bar=True)
    idx = faiss.IndexFlatL2(embeddings.shape[1])
    idx.add(np.array(embeddings))
    return idx, chunks

def retrieve_top_k(query, index, texts, k=3):
    query_embedding = embedding_model.encode([query])
    distances, indices = index.search(np.array(query_embedding), k)
    return [texts[i] for i in indices[0]]

def generate_answer(question, top_chunks):
    context = "\n\n".join(top_chunks)
    prompt = f"""You are a legal contract assistant. Answer the question below using only the given context.

Context:
{context}

Question: {question}

Answer:"""

    # Initialize model
    llm = genai.GenerativeModel("gemini-2.5-pro")

    response = llm.generate_content(prompt)
    return response.text
