import requests
import time
import os

FASTAPI_URL = "http://127.0.0.1:8000" 
SESSION_ID = "evaluation-session"

test_questions = [
    "What is the governing law in this contract?",
    "What are the obligations of the seller?",
    "What rights does the buyer have under this agreement?",
    "Who are the parties to this contract?",
    "What is the term or duration of this agreement?",
    "What are the payment terms outlined in the contract?",
    "Does the contract mention any late payment penalties?",
    "Is there an audit clause mentioned?",
    "What confidentiality obligations are imposed?",
    "Is there a non-disclosure clause in this agreement?",
    "Who owns the intellectual property developed under this contract?",
    "How can the agreement be terminated?",
    "What happens upon termination of the agreement?",
    "Is there a dispute resolution clause?",
    "What representations and warranties are provided?",
    "Are there any limitations on liability?",
    "What deliverables are expected from the vendor?",
    "Is there a defined scope of work?",
    "Does the contract allow for assignment to third parties?",
    "Are there any indemnification obligations?"
]

# Metrics
latencies = []
confidences = []

# upload pdf to the FastAPI server
def upload_pdf(file_path):
    with open(file_path, 'rb') as file:
        response = requests.post(
            f"{FASTAPI_URL}/upload_pdf",
            files={"file": file},
            data={"session_id": SESSION_ID}
        )
    return response

# Upload the PDF file
pdf_file_path = "./data/CUAD_v1/full_contract_pdf/Part_I/Affiliate_Agreements/sample.pdf"

upload_response = upload_pdf(pdf_file_path)
if upload_response.status_code == 200:
    print("✅ PDF uploaded successfully.")
else:
    print(f"❌ PDF upload failed: {upload_response.json().get('detail')}")
    os._exit(1)

# Evaluate the model with test questions
for i, question in enumerate(test_questions, 1):
    print(f"\n🔹 Question {i}: {question}")

    start = time.time()
    response = requests.post(
        f"{FASTAPI_URL}/ask",
        data={
            "question": question,
            "session_id": SESSION_ID
        }
    )
    end = time.time()
    latency = end - start
    latencies.append(latency)

    if response.status_code == 200:
        result = response.json()
        confidence = result.get("confidence_score", None)
        confidences.append(confidence)

        print(f"🔒 Confidence Score: {confidence * 100:.2f}%")
        print(f"⏱️ Latency: {latency:.2f} seconds")
    else:
        print(f"❌ Error: {response.json().get('detail')}")
        confidences.append(0.0)

# 📊 Summary
if test_questions:
    avg_conf = sum(confidences) / len(confidences)
    avg_latency = sum(latencies) / len(latencies)
    print("\n" + "="*50)
    print(f"📈 Average Confidence Score: {avg_conf * 100:.2f}%")
    print(f"⏱️ Average Latency: {avg_latency:.2f} seconds")
else:
    print("❗ No test questions provided.")
