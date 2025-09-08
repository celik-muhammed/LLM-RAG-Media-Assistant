# import os
# import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import psycopg2
from psycopg2.extras import DictCursor

import logging

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

from config import SETTINGS, DB_CONFIG

# ---------------- Config ----------------
# Use environment variables to set timezone and db credentials
# tz = ZoneInfo("Europe/Istanbul")
tz = ZoneInfo(SETTINGS.TZ_INFO)
# timestamp = datetime.now(tz)
# timestamp = datetime.now(timezone.utc)


# Get database connection details from environment variables
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


# def create_table():
#     """
#     Creates a table for storing embeddings and associated text chunks.
#     Uses vector column for storing 1536-dim embeddings (Postgres pgvector extension).
#     """
#     with get_db_connection() as conn, conn.cursor() as cur:
#         cur.execute(f'''
#             -- Create schema if needed
#             CREATE SCHEMA IF NOT EXISTS public;

#             -- Create conversations table
#             CREATE TABLE IF NOT EXISTS {SETTINGS.POSTGRES_TABLE} (
#                 id TEXT PRIMARY KEY,
#                 question TEXT NOT NULL,
#                 response TEXT NOT NULL,
#                 model_used TEXT NOT NULL,
#                 response_time FLOAT NOT NULL,
#                 relevance TEXT NOT NULL,
#                 relevance_explanation TEXT NOT NULL,
#                 prompt_tokens INTEGER NOT NULL,
#                 completion_tokens INTEGER NOT NULL,
#                 total_tokens INTEGER NOT NULL,
#                 eval_prompt_tokens INTEGER NOT NULL,
#                 eval_completion_tokens INTEGER NOT NULL,
#                 eval_total_tokens INTEGER NOT NULL,
#                 timestamp TIMESTAMP WITH TIME ZONE NOT NULL
#             );

#             -- Create feedback table
#             CREATE TABLE IF NOT EXISTS {SETTINGS.POSTGRES_TABLE1} (
#                 id SERIAL PRIMARY KEY,
#                 conversation_id TEXT REFERENCES {SETTINGS.POSTGRES_TABLE}(id),
#                 feedback INTEGER NOT NULL,
#                 timestamp TIMESTAMP WITH TIME ZONE NOT NULL
#             );
#         ''')
#         conn.commit()
#         logger.info(f"{SETTINGS.POSTGRES_TABLE} Table created if not exist!")


# Initialize the database schema (drop and create)
def init_db():
    conn = get_db_connection()
    print("Database connection successful!")
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS feedback")
            cur.execute("DROP TABLE IF EXISTS conversations")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    response TEXT NOT NULL,
                    model_used TEXT NOT NULL,
                    response_time FLOAT NOT NULL,
                    relevance TEXT NOT NULL,
                    relevance_explanation TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    eval_prompt_tokens INTEGER NOT NULL,
                    eval_completion_tokens INTEGER NOT NULL,
                    eval_total_tokens INTEGER NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    conversation_id TEXT REFERENCES conversations(id),
                    feedback INTEGER NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
        conn.commit()
    finally:
        conn.close()


# Save conversation data to the database
def save_conversation(conversation_id, question, answer_data, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now(tz)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversations 
                (id, question, response, model_used, response_time, relevance, 
                relevance_explanation, prompt_tokens, completion_tokens, total_tokens,
                eval_prompt_tokens, eval_completion_tokens, eval_total_tokens, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    conversation_id,
                    question,
                    answer_data["answer"],
                    answer_data["model_used"],
                    answer_data["response_time"],
                    answer_data["relevance"],
                    answer_data["relevance_explanation"],
                    answer_data["prompt_tokens"],
                    answer_data["completion_tokens"],
                    answer_data["total_tokens"],
                    answer_data["eval_prompt_tokens"],
                    answer_data["eval_completion_tokens"],
                    answer_data["eval_total_tokens"],
                    timestamp
                ),
            )
        conn.commit()
    finally:
        conn.close()


# Save feedback data to the database
def save_feedback(conversation_id, feedback, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now(tz)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO feedback
                (conversation_id, feedback, timestamp)
                VALUES (%s, %s, COALESCE(%s, CURRENT_TIMESTAMP))
                """,
                (
                    conversation_id,
                    feedback,
                    timestamp,
                ),
            )
        conn.commit()
    finally:
        conn.close()


# Retrieve recent conversations and feedback data
def get_recent_conversations(limit=5, relevance=None):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            query = """
                SELECT c.*, f.feedback
                FROM conversations c
                LEFT JOIN feedback f ON c.id = f.conversation_id
            """
            if relevance:
                query += f" WHERE c.relevance = '{relevance}'"
            query += " ORDER BY c.timestamp DESC LIMIT %s"

            cur.execute(query, (limit,))
            return cur.fetchall()
    finally:
        conn.close()


# Get feedback statistics (thumbs up, thumbs down)
def get_feedback_stats():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT 
                    SUM(CASE WHEN feedback > 0 THEN 1 ELSE 0 END) as thumbs_up,
                    SUM(CASE WHEN feedback < 0 THEN 1 ELSE 0 END) as thumbs_down
                FROM feedback
            """)
            return cur.fetchone()
    finally:
        conn.close()


# Check timezone information and insert a test entry
def check_timezone():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SHOW timezone;")
            db_timezone = cur.fetchone()[0]
            print(f"Database timezone: {db_timezone}")

            cur.execute("SELECT current_timestamp;")
            db_time_utc = cur.fetchone()[0]
            print(f"Database current time (UTC): {db_time_utc}")

            db_time_local = db_time_utc.astimezone(tz)
            print(f"Database current time ({SETTINGS.TZ_INFO}): {db_time_local}")

            py_time = datetime.now(tz)
            print(f"Python current time: {py_time}")

            # Insert test entry into the database
            cur.execute("""
                INSERT INTO conversations 
                (id, question, response, model_used, response_time, relevance, 
                relevance_explanation, prompt_tokens, completion_tokens, total_tokens,
                eval_prompt_tokens, eval_completion_tokens, eval_total_tokens, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING timestamp;
            """, 
            ('test', 'test question', 'test answer', 'test model', 0.0, 'test relevance', 
            'test explanation', 0, 0, 0, 0, 0, 0, py_time))

            inserted_time = cur.fetchone()[0]
            print(f"Inserted time (UTC): {inserted_time}")
            print(f"Inserted time ({SETTINGS.TZ_INFO}): {inserted_time.astimezone(tz)}")

            cur.execute("SELECT timestamp FROM conversations WHERE id = 'test';")
            selected_time = cur.fetchone()[0]
            print(f"Selected time (UTC): {selected_time}")
            print(f"Selected time ({SETTINGS.TZ_INFO}): {selected_time.astimezone(tz)}")

            # Clean up the test entry
            cur.execute("DELETE FROM conversations WHERE id = 'test';")
            conn.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

# def wait_for_postgres(max_retries=30, delay=5):
#     for i in range(max_retries):
#         try:
#             conn = psycopg2.connect(
#                 dbname="llm_rag",
#                 user="admin",
#                 password="admin",
#                 host="localhost",
#                 port=5432
#             )
#             conn.close()
#             print("✅ Postgres ready")
#             return
#         except Exception as e:
#             print(f"⏳ Waiting for Postgres... {e}")
#             time.sleep(delay)
#     raise RuntimeError("Postgres not available after retries")


# Check if timezone should be checked
if SETTINGS.RUN_TIMEZONE_CHECK:
    # init_db()
    check_timezone()
