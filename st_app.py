import os
import uuid
import requests
import streamlit as st
import logging

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------- Config ----------------
BASE_URL = f"http://{('app' if os.path.exists('/.dockerenv') else 'localhost')}:5000"
logger.info(f"Backend API: {BASE_URL}")

st.set_page_config(page_title="Media Assist API", page_icon="🤖", layout="wide")
st.title("🤖 Media Assist")

# ---------------- Session State Initialize/Store----------------
# For question, answer, and conversation ID
if "question" not in st.session_state:
    st.session_state.question = ""
if "answer" not in st.session_state:
    st.session_state.answer = ""
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = ""
if "model" not in st.session_state:
    st.session_state.model = "phi3:latest"

# ---------------- API Helpers ----------------
def get_models(url):
    """Fetch available models from backend or Ollama."""
    try:
        resp = requests.get(f"{url}/models", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return [m["id"] for m in data.get("data", [])]
    except Exception as e:
        logger.warning(f"Could not fetch models, using fallback. Error: {e}")
        return ["phi3:latest", "gpt-oss:20b"]

# Function to ask a question to the API
def ask_question(url, question):
    try:
        resp = requests.post(
            f"{url}/question",
            json={"question": question},
            # timeout=120
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        return {"answer": "⚠️ API request timed out."}
    except requests.exceptions.RequestException as e:
        logger.exception("Error calling API")
        return {"answer": f"❌ API error: {e}"}

def ask_question_model(url, question, model):
    try:
        resp = requests.post(
            f"{url}/question",
            json={"question": question, "model": model},
            # timeout=120
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        return {"answer": "⚠️ API request timed out."}
    except requests.exceptions.RequestException as e:
        logger.exception("Error calling API")
        return {"answer": f"❌ API error: {e}"}

# Function to send feedback to the API
def send_feedback(url, conversation_id, feedback):
    try:
        resp = requests.post(
            f"{url}/feedback",
            json={"conversation_id": conversation_id, "feedback": feedback},
            # timeout=30
        )
        resp.raise_for_status()
        return resp.status_code
    except Exception as e:
        logger.exception("Error sending feedback")
        return f"Error: {e}"

# ---------------- UI ----------------
# Model selector
available_models = get_models(BASE_URL)
with st.sidebar:
    st.session_state.model = st.selectbox(
        "(Placeholder) Choose a model:",
        available_models,
        index=available_models.index(st.session_state.model)
        if st.session_state.model in available_models else 0
    )

# Question input
st.session_state.question = st.text_input(
    "Enter your question:", value=st.session_state.question
)
if st.button("Get Answer"):
    if st.session_state.question.strip():
        # with st.spinner(f"Querying {st.session_state.model}..."):
        with st.spinner("Querying API..."):
            # response = ask_question(BASE_URL, st.session_state.question, st.session_state.model)
            response = ask_question(BASE_URL, st.session_state.question)
        st.session_state.answer = response.get("answer", "No answer provided")
        st.session_state.conversation_id = response.get("conversation_id", str(uuid.uuid4()))
    else:
        st.warning("❗ Please enter a question.")

# Show answer + feedback
if st.session_state.answer:
    st.subheader("Answer:")
    st.write(st.session_state.answer)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👍 Positive"):
            with st.spinner("Sending feedback..."):
                status = send_feedback(BASE_URL, st.session_state.conversation_id, 1)
            st.success(f"Positive feedback sent (status {status}).")

    with col2:
        if st.button("👎 Negative"):
            with st.spinner("Sending feedback..."):
                status = send_feedback(BASE_URL, st.session_state.conversation_id, -1)
            st.error(f"Negative feedback sent (status {status}).")

    with col3:
        if st.button("⏭️ Skip feedback"):
            st.info("Feedback skipped.")

