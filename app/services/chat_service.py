import uuid
from typing import List, Dict

from app.db import file_store
from app.utils import get_consistent_timestamp
from app.core.services import vector_store, active_conversations

def get_all_chats() -> List[Dict]:
    """Get all chats, sorted by last updated"""
    chat_history = file_store.load_chat_history()
    return sorted(
        chat_history,
        key=lambda c: c.get('updated_at', '1970'),
        reverse=True
    )

def create_new_chat() -> Dict:
    """Create a new chat session"""
    chat_history = file_store.load_chat_history()
    chat_id = str(uuid.uuid4())
    
    new_chat = {
        "id": chat_id,
        "title": f"New Chat {len(chat_history) + 1}",
        "created_at": get_consistent_timestamp(),
        "updated_at": get_consistent_timestamp(),
        "message_count": 0,
        "has_pdf": False,
        "pdf_count": 0,
        "pdf_list": []
    }
    
    chat_history.insert(0, new_chat)
    file_store.save_chat_history(chat_history)
    file_store.save_conversation(chat_id, [])
    active_conversations[chat_id] = []
    
    return new_chat

def get_chat_messages(chat_id: str) -> List[Dict]:
    """Get all messages for a specific chat"""
    conversation = file_store.load_conversation(chat_id)
    messages = []
    
    for msg in conversation:
        sender = "user" if msg["role"] == "user" else "bot"
        messages.append({
            "id": str(uuid.uuid4()),
            "text": msg["parts"][0],
            "sender": sender,
            "timestamp": msg.get("timestamp", get_consistent_timestamp())
        })
    return messages

def delete_chat_by_id(chat_id: str):
    """Delete a chat session and its associated data"""
    chat_history = file_store.load_chat_history()
    
    if not any(c["id"] == chat_id for c in chat_history):
        return False

    chat_history = [c for c in chat_history if c["id"] != chat_id]
    
    if chat_id in active_conversations:
        del active_conversations[chat_id]
    
    vector_store.delete_collection(chat_id)
    file_store.delete_conversation_file(chat_id)
    file_store.save_chat_history(chat_history)
    
    return True

def rename_chat_by_id(chat_id: str, new_title: str):
    """Rename a chat session"""
    chat_history = file_store.load_chat_history()
    chat_found = False
    for chat in chat_history:
        if chat["id"] == chat_id:
            chat["title"] = new_title
            chat["updated_at"] = get_consistent_timestamp()
            chat_found = True
            break
    
    if chat_found:
        file_store.save_chat_history(chat_history)
    
    return chat_found
