import logging
# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

import db  # your module with init_db


def main():
    logger.info("Starting database initialization...")
    try:
        db.init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error("Database initialization failed: %s", e)


if __name__ == "__main__":
    main()
