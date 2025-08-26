import os
import json
import uuid
import argparse
import logging

import requests
import questionary
import pandas as pd
# import backoff  # optional: if you want retries

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------
BASE_URL = f"http://{('app' if os.path.exists('/.dockerenv') else 'localhost')}:5000"
CSV_FILE = "./Data/ground-truth-data.csv"

# You can expand this list based on what `ollama list` shows
AVAILABLE_MODELS = [
    "phi3:latest",
    "llama3:latest",
    "mistral:latest",
]

logger.info(f"Using API base URL: {BASE_URL}")


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def get_random_question(file_path: str) -> str:
    """Pick a random question from CSV."""
    df = pd.read_csv(file_path)
    return df.sample(n=1).iloc[0]["question"]


def ask_question(url: str, question: str) -> dict:
    """Send a question to the backend API and return the response JSON."""
    try:
        response = requests.post(
            f"{url}/question",
            json={"question": question},
            # timeout=333,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error("⏳ API request timed out")
        return {"answer": "The API request timed out."}
    except requests.exceptions.RequestException as e:
        logger.exception(f"❌ Error calling API: {e}")
        return {"answer": f"Error: {str(e)}"}


def send_feedback(url: str, conversation_id: str, feedback: int) -> int:
    """Send user feedback (+1 / -1) for a given conversation_id."""
    try:
        response = requests.post(
            f"{url}/feedback",
            json={"conversation_id": conversation_id, "feedback": feedback},
            timeout=30,
        )
        response.raise_for_status()
        return response.status_code
    except requests.exceptions.Timeout:
        logger.error("⏳ Feedback request timed out")
    except requests.exceptions.RequestException as e:
        logger.exception(f"❌ Feedback request failed: {e}")
    return 500


# ----------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Interactive CLI app for continuous Q&A with feedback"
    )
    parser.add_argument(
        "--random", "-r",
        action="store_true",
        help="Use random questions from the CSV file instead of manual input",
    )
    args = parser.parse_args()

    print("Welcome to the interactive question-answering app!")
    print("You can exit the program at any time when prompted.")

    while True:
        # Get question (random or typed)
        if args.random:
            question = get_random_question(CSV_FILE)
            print(f"\nRandom question: {question}")
        else:
            question = questionary.text("Enter your question:").ask()
            if not question:  # empty input = exit
                print("Exiting... Goodbye!")
                break

        # Ask API
        response = ask_question(BASE_URL, question)
        print("\nAnswer:", response.get("answer", "No answer provided"))

        # Track conversation
        conversation_id = response.get("conversation_id", str(uuid.uuid4()))

        # Ask for feedback
        feedback = questionary.select(
            "How would you rate this response?",
            choices=["+1 (Positive)", "-1 (Negative)", "Pass (Skip feedback)"],
        ).ask()

        if feedback and feedback != "Pass (Skip feedback)":
            feedback_value = 1 if feedback.startswith("+1") else -1
            status = send_feedback(BASE_URL, conversation_id, feedback_value)
            print(f"Feedback sent. Status code: {status}")
        else:
            print("Feedback skipped.")

        # Continue?
        if not questionary.confirm("Do you want to continue?").ask():
            print("Thank you for using the app. Goodbye!")
            break


if __name__ == "__main__":
    main()
