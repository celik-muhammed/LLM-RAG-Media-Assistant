import requests
import pandas as pd


# Load test data
df = pd.read_csv("./Data/ground-truth-data.csv")

# Pick a random question
row = df.sample(n=1).iloc[0]
question = row["question"]

print("Question:", question)

# API endpoint
url = "http://localhost:5000/question"

# Pick a model (must match what your backend / Ollama supports)
model = "phi3:latest"

# Send request
data = {
    "question": question,
    # "model": model,
}
response = requests.post(
    url,
    json=data,
    # timeout=120,
)
# print(response.content)

try:
    result = response.json()
except Exception as e:
    print("⚠️ Could not parse response:", e)
    print("Raw:", response.text)
    raise

print("Answer:", result.get("answer"))
print("Conversation ID:", result.get("conversation_id"))
