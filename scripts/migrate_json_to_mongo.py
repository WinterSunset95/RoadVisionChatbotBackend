import os
import sys
import json
from datetime import datetime
from pathlib import Path
from uuid import UUID
from pymongo import MongoClient

# Add project root to path to allow importing app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings

def migrate():
    """
    Migrates data from legacy JSON files (chat_history.json, memory_*.json)
    to the MongoDB database.
    """
    try:
        client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
        client.admin.command('ismaster')
    except Exception as e:
        print(f"❌ Could not connect to MongoDB. Please ensure it is running.")
        print(f"   Connection String: {settings.MONGODB_URL}")
        print(f"   Error: {e}")
        return

    db = client[settings.MONGODB_DB]
    chats_collection = db["chats"]

    print("--- Starting Data Migration to MongoDB ---")

    # 1. Clear existing data to ensure a clean migration
    result = chats_collection.delete_many({})
    print(f"🧹 Cleared {result.deleted_count} existing documents from 'chats' collection.")

    # 2. Load chat history
    chat_history_path = settings.DATA_DIR / "chat_history.json"
    if not chat_history_path.exists():
        print(f"⚠️  {chat_history_path} not found. No data to migrate.")
        return

    with open(chat_history_path, 'r') as f:
        chat_history = json.load(f)

    migrated_count = 0
    # 3. Iterate over each chat and migrate its data
    for chat_meta in chat_history:
        chat_id_str = chat_meta["id"]
        print(f" migrating chat '{chat_meta['title']}' ({chat_id_str})...")

        # Load corresponding conversation messages
        messages = []
        conversation_path = settings.DATA_DIR / f"memory_{chat_id_str}.json"
        if conversation_path.exists():
            with open(conversation_path, 'r') as f:
                conversation = json.load(f)
            
            for msg in conversation:
                messages.append({
                    "id": UUID(msg.get("id", str(uuid.uuid4()))),
                    "sender": "user" if msg["role"] == "user" else "bot",
                    "text": msg["parts"][0],
                    "timestamp": msg.get("timestamp", get_consistent_timestamp())
                })
        
        # Prepare documents sub-array from pdf_list
        documents = []
        for doc_meta in chat_meta.get("pdf_list", []):
            documents.append({
                "id": uuid.uuid4(),
                "filename": doc_meta.get("name"),
                "doc_type": "pdf",
                "file_hash": "unknown_migrated",
                "file_size": 0,
                "chunks_count": doc_meta.get("chunks_added", 0),
                "status": doc_meta.get("status", "active"),
                "uploaded_at": doc_meta.get("upload_time"),
                "processing_stats": {}
            })
            
        # Create the new chat document for MongoDB
        chat_document = {
            "_id": UUID(chat_id_str),  # Use the existing UUID as the primary key
            "title": chat_meta["title"],
            "created_at": chat_meta["created_at"],
            "updated_at": chat_meta["updated_at"],
            "documents": documents,
            "messages": messages
        }

        # Insert into MongoDB
        chats_collection.insert_one(chat_document)
        migrated_count += 1
    
    print("\n--- Migration Complete ---")
    print(f"✅ Migrated {migrated_count} chat documents to MongoDB.")
    print(f"Database: '{settings.MONGODB_DB}', Collection: 'chats'")
    client.close()

if __name__ == "__main__":
    def get_consistent_timestamp():
        return datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
    migrate()
