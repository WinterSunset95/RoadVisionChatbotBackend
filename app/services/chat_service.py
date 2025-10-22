from uuid import UUID
from typing import List
from pymongo.database import Database

from app.core.services import vector_store
from app.models.chat import Chat, ChatMetadata, Message
from app.utils import get_consistent_timestamp

def get_all_chats(db: Database) -> List[ChatMetadata]:
    """Get all chats from MongoDB, converting them to Pydantic models for the API response."""
    chat_docs = list(db["chats"].find().sort("updated_at", -1))
    response_chats = []
    for chat_doc in chat_docs:
        chat = Chat.model_validate(chat_doc)
        pdf_list = [
            {
                "name": doc.filename,
                "upload_time": doc.uploaded_at,
                "chunks_added": doc.chunks_count,
                "status": doc.status,
            }
            for doc in chat.documents
        ]
        response_chats.append(
            ChatMetadata(
                id=str(chat.id),
                title=chat.title,
                created_at=chat.created_at,
                updated_at=chat.updated_at,
                message_count=len(chat.messages),
                has_pdf=len(chat.documents) > 0,
                pdf_count=len(chat.documents),
                pdf_list=pdf_list,
            )
        )
    return response_chats

def create_new_chat(db: Database) -> ChatMetadata:
    """Create a new chat session in MongoDB."""
    chat_count = db["chats"].count_documents({})
    now = get_consistent_timestamp()
    new_chat = Chat(
        title=f"New Chat {chat_count + 1}",
        created_at=now,
        updated_at=now,
    )
    
    db["chats"].insert_one(new_chat.model_dump(by_alias=True))
    
    # Convert to API response model
    return ChatMetadata(
        id=str(new_chat.id),
        title=new_chat.title,
        created_at=new_chat.created_at,
        updated_at=new_chat.updated_at,
        message_count=0,
        has_pdf=False,
        pdf_count=0,
        pdf_list=[],
    )

def get_chat_messages(db: Database, chat_id: UUID) -> List[Message]:
    """Get all messages for a specific chat from MongoDB."""
    chat_doc = db["chats"].find_one({"_id": chat_id})
    if not chat_doc:
        return []
    
    chat = Chat.model_validate(chat_doc)
    return [
        Message(id=str(msg.id), text=msg.text, sender=msg.sender, timestamp=msg.timestamp)
        for msg in chat.messages
    ]

def delete_chat_by_id(db: Database, chat_id: UUID) -> bool:
    """Delete a chat session and its associated data from MongoDB."""
    result = db["chats"].delete_one({"_id": chat_id})
    if result.deleted_count == 0:
        return False
    
    vector_store.delete_collection(str(chat_id))
    return True

def rename_chat_by_id(db: Database, chat_id: UUID, new_title: str) -> bool:
    """Rename a chat session in MongoDB."""
    result = db["chats"].update_one(
        {"_id": chat_id},
        {"$set": {"title": new_title, "updated_at": get_consistent_timestamp()}},
    )
    return result.modified_count > 0
