import json
from pathlib import Path
from typing import List, Dict, Union
from app.config import settings

# This is a temporary file-based storage to mimic the old system.
# It will be replaced by a proper database in Phase 2.

CHAT_HISTORY_FILE = settings.DATA_DIR / "chat_history.json"

def save_json(path: Path, data: Union[List, Dict]):
    """Saves data to a JSON file."""
    try:
        settings.DATA_DIR.mkdir(exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"⚠️  Failed to save {path}: {e}")
        return False

def load_json(path: Path) -> Union[List, Dict]:
    """Loads data from a JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return [] if "history" in path.name else {}
    except Exception as e:
        print(f"⚠️  Failed to load {path}: {e}")
        return [] if "history" in path.name else {}

def load_chat_history() -> List[Dict]:
    """Loads the main chat history list."""
    data = load_json(CHAT_HISTORY_FILE)
    return data if isinstance(data, list) else []

def save_chat_history(chat_history: List[Dict]):
    """Saves the main chat history list."""
    save_json(CHAT_HISTORY_FILE, chat_history)

def load_conversation(chat_id: str) -> List[Dict]:
    """Loads the message history for a specific chat."""
    conv_file = settings.DATA_DIR / f"memory_{chat_id}.json"
    data = load_json(conv_file)
    return data if isinstance(data, list) else []

def save_conversation(chat_id: str, conversation: List[Dict]):
    """Saves the message history for a specific chat."""
    conv_file = settings.DATA_DIR / f"memory_{chat_id}.json"
    save_json(conv_file, conversation)

def delete_conversation_file(chat_id: str):
    """Deletes the message history file for a specific chat."""
    conv_file = settings.DATA_DIR / f"memory_{chat_id}.json"
    if conv_file.exists():
        conv_file.unlink()
