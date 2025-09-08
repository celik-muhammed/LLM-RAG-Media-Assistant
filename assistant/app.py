import os
import uuid
import logging

from flask import Flask, request, jsonify

import db
from config import SETTINGS
from rag import rag

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------- Flask App ----------------
app = Flask(__name__)


@app.route("/")
def home():
    # return "Welcome to the Media Assist API"
    return jsonify({
        "message": "Welcome to the Media Assist API",
        "status": "ok"
    }), 200


@app.route("/question", methods=["POST"])
def handle_question():
    try:
        conversation_id = str(uuid.uuid4())

        # data = request.json
        data = request.get_json(force=True, silent=True) or {}
        logger.info(f"Incoming question request: {data}")

        question = data.get("question")
        if not question:
            return jsonify({"error": "Question must be a non-empty string"}), 400

        # Call RAG model
        try:
            answer_data = rag(question)
            if not isinstance(answer_data, dict) or "answer" not in answer_data:
                logger.error(f"Invalid rag() response: {answer_data}")
                return jsonify({"error": "Invalid response from RAG"}), 502
        except Exception as e:  # requests.exceptions.RequestException:
            logger.exception("Error calling rag()")
            return jsonify({"error": "RAG runner not available"}), 503

        result = {
            "conversation_id": conversation_id,
            "question": question,
            "answer": answer_data["answer"],
            # "model_used": answer_data.get("model_used", "unknown"),
        }

        # Save conversation to DB
        try:
            db.save_conversation(
                conversation_id=conversation_id,
                question=question,
                answer_data=answer_data,
            )
        except Exception as e:
            logger.exception("Error saving conversation to DB")
            return jsonify({"error": "Database error"}), 500

        return jsonify(result), 200

    except Exception as e:
        logger.exception("Unexpected error in /question")
        return jsonify({"error": str(e)}), 500


@app.route("/feedback", methods=["POST"])
def handle_feedback():
    try:
        data = request.get_json(force=True, silent=True) or {}
        logger.info(f"Incoming feedback: {data}")

        conversation_id = data.get("conversation_id")
        feedback_raw = data.get("feedback")

        # Validate feedback value
        try:
            feedback = int(feedback_raw)
        except (ValueError, TypeError):
            return jsonify({"error": "Feedback must be an integer (1 or -1)."}), 400

        if not conversation_id or feedback not in [1, -1]:
            return jsonify({"error": "Invalid input"}), 400

        # Save feedback in DB
        db.save_feedback(
            conversation_id=conversation_id,
            feedback=feedback,
        )
        result = {
            "message": f"✅ Feedback received for conversation {conversation_id}: {feedback}"
        }
        return jsonify(result), 200

    except Exception as e:
        logger.exception("Error saving feedback to DB")
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    # ✅ Check flask health check
    status = {"flask": "ok"}

    # ✅ Check PostgreSQL health check
    try:
        conn = db.get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        status["postgres"] = "ok"
    except Exception as e:
        status["postgres"] = f"error: {str(e)}"

    # ✅ Check Ollama LLM health check
    try:
        import requests
        payload = {
            "model": SETTINGS.MODEL_CHAT,
            "messages": [{"role": "user", "content": "ping"}]
        }
        headers = {"Content-Type": "application/json"}

        # Optional: List models to check availability
        r = requests.get(
            f"{SETTINGS.BASE_URL}models",
            # timeout=3,
        )
        # print(r.json())  # see if phi3 is available
        logger.info(f"Ollama models: {r.json()}")

        # Send a lightweight ping to the LLM
        r = requests.post(
            f"{SETTINGS.BASE_URL}chat/completions",
            json=payload,
            headers=headers,
            # timeout=5,
        )
        if r.status_code == 200:
            status["ollama"] = "ok"
        else:
            status["ollama"] = f"error: {r.status_code}"
    except Exception as e:
        status["ollama"] = f"error: {str(e)}"

    # ✅ Check RAG runner (rag service)
    # try:
    #     # For example, hit a simple endpoint or do a lightweight call
    #     import requests
    #     r = requests.get("http://localhost:5000/health", timeout=5)
    #     if r.status_code == 200:
    #         status["localhost"] = "ok"
    #     else:
    #         status["localhost"] = f"error: {r.status_code}"
    # except Exception as e:
    #     status["localhost"] = f"error: {str(e)}"

    # Determine overall HTTP status
    http_status = 200 if all(v == "ok" for v in status.values()) else 503
    return jsonify(status), http_status


if __name__ == "__main__":
    print("🔄 Flask starting...")
    app.run(host='0.0.0.0', port=5000, debug=True)
