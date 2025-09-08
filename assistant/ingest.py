import os
import json

import logging
# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

import pandas as pd
import minsearch  # your module with Index

from config import SETTINGS

# ---------------- Config ----------------
DATA_PATH = (
    SETTINGS.DATA_PATH
    if os.path.exists('/.dockerenv') else
    "../Data/documents-with-ids.json"
)
logger.info("Loading data from: %s", DATA_PATH)
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Data file not found at {DATA_PATH}")
logger.info("Data file size: %d bytes", os.path.getsize(DATA_PATH))


def load_index(data_path=DATA_PATH):
    """Load documents from JSON and create a MinSearch index."""
    try:
        with open(data_path, 'rt', encoding='utf-8') as f_in:
            documents = json.load(f_in)
        logger.info("Loaded %d documents", len(documents))
    except json.JSONDecodeError as e:
        logger.error("Failed to decode JSON: %s", e)
        raise
    except Exception as e:
        logger.error("Error reading data file: %s", e)
        raise

    # Create a MinSearch index with specified text and keyword fields
    index = minsearch.Index(
        text_fields=['intent', 'question', 'response'],  # full-text searchable fields
        keyword_fields=['id', 'category'],               # exact match fields
    )

    # Fit the index to our document list
    index.fit(documents)
    logger.info("MinSearch index created successfully")

    return index

if __name__ == "__main__":
    idx = load_index()
    logger.info("Index ready for querying")

    # Print first 3 documents for inspection
    sample_docs = idx.docs[:1] if hasattr(idx, "docs") else []
    print("Sample documents in index:")
    for doc in sample_docs:
        print(json.dumps(doc, indent=2, ensure_ascii=False))

