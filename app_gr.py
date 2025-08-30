import os
import uuid
import requests
import logging

# https://www.gradio.app/guides/quickstart
import gradio as gr

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------- Config ----------------
BASE_URL = f"http://{('app' if os.path.exists('/.dockerenv') else 'localhost')}:5000"
logger.info(f"Backend API: {BASE_URL}")

# ---------------- API Helpers ----------------
def ask_question(question, model="phi3:latest"):
    """Send question to API and return (answer, conversation_id)."""
    try:
        resp = requests.post(
            f"{BASE_URL}/question",
            # json={"question": question, "model": model},
            json={"question": question},
            # timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("answer", "No answer provided."), data.get("conversation_id", str(uuid.uuid4()))
    except requests.exceptions.Timeout:
        return "⚠️ API request timed out.", str(uuid.uuid4())
    except requests.exceptions.RequestException as e:
        logger.exception("Error calling API")
        return f"❌ API error: {e}", str(uuid.uuid4())

def send_feedback(conversation_id, feedback):
    """Send feedback score to backend."""
    try:
        resp = requests.post(
            f"{BASE_URL}/feedback",
            json={"conversation_id": conversation_id, "feedback": feedback},
            timeout=15,
        )
        resp.raise_for_status()
        return f"✅ Feedback sent (status {resp.status_code})."
    except Exception as e:
        logger.exception("Error sending feedback")
        return f"❌ Error sending feedback: {e}"

def get_models():
    """Fetch available models from backend or fallback."""
    # try:
    #     resp = requests.get(f"{BASE_URL}/models", timeout=15)
    #     resp.raise_for_status()
    #     data = resp.json()
    #     return [m["id"] for m in data.get("data", [])]
    # except Exception as e:
    #     logger.warning(f"Could not fetch models, using fallback. Error: {e}")
    return ["phi3:latest", "gpt-oss:20b"]

# ---------------- Gradio App ----------------
with gr.Blocks(title="Media Assist API") as demo:
    gr.Markdown("## 🤖 Media Assist")

    with gr.Row():
        with gr.Column(scale=1):
            model_dropdown = gr.Dropdown(
                choices=get_models(),
                value="phi3:latest",
                label="(Placeholder) Choose a model"
            )
            question_box = gr.Textbox(
                placeholder="Enter your question...",
                label="Question",
                lines=2
            )
            ask_btn = gr.Button("Get Answer", variant="primary")

        with gr.Column(scale=2):
            answer_box = gr.Markdown("**Answer will appear here.**")
            feedback_info = gr.Label(label="Feedback Status")

            with gr.Row():
                feedback_pos = gr.Button("👍 Positive")
                feedback_neg = gr.Button("👎 Negative")
                feedback_skip = gr.Button("⏭️ Skip")

    # ---- State ----
    conversation_id_state = gr.State("")

    # ---- Events ----
    def handle_question(question, model):
        if not question.strip():
            return "❗ Please enter a question.", ""
        answer, conv_id = ask_question(question, model)
        return answer, conv_id

    ask_btn.click(
        handle_question,
        inputs=[question_box, model_dropdown],
        outputs=[answer_box, conversation_id_state]
    )

    feedback_pos.click(
        lambda conv_id: send_feedback(conv_id, 1),
        inputs=[conversation_id_state],
        outputs=[feedback_info]
    )

    feedback_neg.click(
        lambda conv_id: send_feedback(conv_id, -1),
        inputs=[conversation_id_state],
        outputs=[feedback_info]
    )

    feedback_skip.click(
        lambda: "Feedback skipped.",
        outputs=[feedback_info]
    )

# Run app
if __name__ == "__main__":
    # Option 1: Use Gradio’s built-in share=True, For quick sharing: use share=True.
    # Adds a temporary public URL like https://xxxxx.gradio.live
    # Option 2: Expose via your own server (production-friendly)
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
