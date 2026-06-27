import json
import logging
import os

LOGS_DIR = os.path.dirname(os.path.abspath(__file__))
CLASSIFICATIONS_FILE = os.path.join(LOGS_DIR, "classifications.jsonl")

logger = logging.getLogger(__name__)


def save_classification_log(entry: dict) -> None:
    try:
        with open(CLASSIFICATIONS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.error("Failed to persist classification log: %s", exc)


def get_recent_logs(limit: int = 200) -> list[dict]:
    if not os.path.exists(CLASSIFICATIONS_FILE):
        return []
    try:
        with open(CLASSIFICATIONS_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return [json.loads(line) for line in lines[-limit:] if line.strip()]
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Failed to read classification logs: %s", exc)
        return []
