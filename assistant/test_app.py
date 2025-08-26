import uuid
import logging

from flask import Flask, request, jsonify

import db
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
    return jsonify({
        "message": "Welcome to the Customer Assist API",
        "status": "ok"
    }), 200


@app.route("/question", methods=["POST"])
def handle_question():
    try:
        data = request.get_json(force=True, silent=True) or {}
        logger.info(f"Incoming question: {data}")

        question = data.get("question")
        if not question or not isinstance(question, str):
            return jsonify({"error": "Question must be a non-empty string"}), 400

        conversation_id = str(uuid.uuid4())

        # Call RAG model
        answer_data = rag(question)
        if not isinstance(answer_data, dict) or "answer" not in answer_data:
            logger.error(f"Invalid rag() response: {answer_data}")
            return jsonify({"error": "Invalid response from RAG"}), 502

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

        result = {
            "conversation_id": conversation_id,
            "question": question,
            "answer": answer_data["answer"],
            # "model_used": answer_data.get("model_used", "unknown"),
        }

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

        try:
            feedback = int(feedback_raw)
        except (ValueError, TypeError):
            return jsonify({"error": "Feedback must be an integer (1 or -1)."}), 400

        if not conversation_id or feedback not in [1, -1]:
            return jsonify({"error": "Invalid input"}), 400

        db.save_feedback(conversation_id=conversation_id, feedback=feedback)

        return jsonify({
            "message": f"✅ Feedback received for conversation {conversation_id}: {feedback}"
        }), 200

    except Exception as e:
        logger.exception("Unexpected error in /feedback")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    logger.info("🔄 Flask test app starting...")
    app.run(host='0.0.0.0', port=5000, debug=True)
