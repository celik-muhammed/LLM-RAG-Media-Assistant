import logging
from datetime import datetime

import psycopg2

import db  # your module with get_db_connection
from config import SETTINGS

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def add_sample_data():
    """Add a sample conversation entry to the database."""
    conn = None
    try:
        conn = db.get_db_connection()
        logger.info("Database connection successful.")

        with conn.cursor() as cur:
            # Sample data for the conversations table
            cur.execute(
                """
                INSERT INTO conversations (
                    id, question, response, model_used, response_time,
                    relevance, relevance_explanation, prompt_tokens, completion_tokens, total_tokens,
                    eval_prompt_tokens, eval_completion_tokens, eval_total_tokens, timestamp
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    "test_conversation_1",  # id
                    "What is the return policy?",  # question
                    "Our return policy lasts 30 days...",  # response
                    f"{SETTINGS.MODEL_CHAT}",  # model_used chat
                    0.5,  # response_time
                    "RELEVANT",  # relevance
                    "The answer accurately addresses the question.",  # relevance_explanation
                    10,  # prompt_tokens
                    15,  # completion_tokens
                    25,  # total_tokens
                    5,  # eval_prompt_tokens
                    10,  # eval_completion_tokens
                    15,  # eval_total_tokens
                    datetime.now()  # timestamp
                )
            )
            conn.commit()
            logger.info("Sample data added to conversations table.")
    except Exception as e:
        logger.error("Failed to add sample data: %s", e)
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")


if __name__ == "__main__":
    add_sample_data()
