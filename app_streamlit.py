import streamlit as st
import requests
import uuid

FASTAPI_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Legal Document QA", layout="wide")
st.title("📄 Legal Document Question-Answering System")

# 🔑 Create unique session ID
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

st.caption(f"Session ID: `{st.session_state['session_id']}`")

# 📤 Upload PDF
st.subheader("1. Upload a PDF")
uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

if uploaded_file:
    with st.spinner("Uploading..."):
        files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
        response = requests.post(f"{FASTAPI_URL}/upload_pdf", files=files)

    if response.status_code == 200:
        st.success("✅ PDF uploaded and indexed successfully.")
    else:
        st.error(f"❌ Upload failed: {response.json().get('detail')}")

# ❓ Ask a question
st.subheader("2. Ask a Legal Question")
question = st.text_input("Enter your legal question:")

if st.button("Submit Question") and question:
    with st.spinner("Getting answer..."):
        response = requests.post(f"{FASTAPI_URL}/ask",data={"question": question,"session_id": st.session_state["session_id"]})

    if response.status_code == 200:
        result = response.json()

        # Confidence Score
        confidence = result.get("confidence_score", None)
        if confidence is not None:
            st.metric("🔒 Confidence Score", f"{confidence * 100:.1f}%")
        
        # Display Answer
        st.markdown("### 🤖 Answer")
        st.success(result["answer"])

        # Show top retrieved chunks
        if "source_chunks" in result:
            st.markdown("### 📑 Top 3 Relevant Contexts")
            for i, chunk in enumerate(result["source_chunks"], 1):
                with st.expander(f"Evidence Chunk {i}"):
                    st.write(chunk)
    else:
        st.error(f"❌ Error: {response.json().get('detail')}")