from uuid import UUID
from typing import Dict, List
from pymongo.database import Database

from app.core.services import llm_model, vector_store
from app.modules.askai.models.chat import Chat, EmbeddedMessage
from app.config import settings
from app.utils import get_consistent_timestamp

def send_message_to_chat(db: Database, chat_id: UUID, user_message: str) -> Dict:
    """
    Handles the RAG pipeline for a user message.
    1. Retrieves context from vector store.
    2. Builds a prompt.
    3. Calls the LLM.
    4. Saves conversation history to DB.
    5. Returns the response.
    """
    # Check if chat exists
    chat_doc = db["chats"].find_one({"_id": chat_id})
    if not chat_doc:
        raise ValueError("Chat not found")
    
    chat = Chat.model_validate(chat_doc)

    # 1. Retrieve context
    chat_docs = chat.documents
    context_text = ""
    sources = []
    
    if chat_docs:
        collection = vector_store.get_or_create_collection(str(chat_id))
        results = vector_store.query(collection, user_message, n_results=settings.RAG_TOP_K)
        
        if results:
            context_parts = []
            for idx, (doc, meta, score) in enumerate(results, 1):
                doc_type = meta.get('doc_type', 'unknown')
                source = meta.get('source', 'Unknown')
                
                if doc_type == 'pdf':
                    page = meta.get('page', 'unknown')
                    content_type = meta.get('type', 'text')
                    location = f"Page {page}"
                    if content_type == 'table': location += ", Table"
                else:
                    location = "Unknown location"
                    content_type = meta.get('type', 'unknown')
                
                context_parts.append(f"[Source {idx}: {source} - {location}]\n{doc}\n")
                
                sources.append({
                    "id": idx, "source": source, "location": location, "doc_type": doc_type,
                    "content_type": content_type, "content": doc[:800], "full_content": doc,
                    "page": meta.get('page', 'unknown')
                })
            
            context_text = "\n\n".join(context_parts)
            print(f"🔍 Retrieved {len(sources)} relevant sources")

    # 2. Build prompt
    if context_text:
        prompt = f"""You are a helpful AI assistant that answers questions based on provided document context.

CONTEXT:
{context_text}

USER QUESTION: {user_message}

INSTRUCTIONS:
1. Answer using the information in the context above
2. Be specific and cite which sources support your answer
3. If the context doesn't contain the answer, feel free to add information from other sources, but be sure to cite them and clearly state
that you are using information from other sources and not the context
4. Be concise but thorough
5. Use github markdown formatting for everything"""
    else:
        prompt = f"""You are a helpful AI assistant. Please answer: {user_message}"""
        
    # 3. Call LLM
    recent_history = chat.messages[-10:]
    gemini_history = [{"role": "model" if msg.sender == "bot" else "user", "parts": [{"text": msg.text}]} for msg in recent_history]
    gemini_history.append({"role": "user", "parts": [{"text": prompt}]})
    
    try:
        response = llm_model.generate_content(gemini_history)
        bot_response = response.text if hasattr(response, "text") else "I couldn't generate a response."
    except Exception as api_error:
        print(f"❌ Gemini API error: {api_error}")
        bot_response = f"I encountered an error: {str(api_error)}"

    # 4. Save conversation to DB
    now = get_consistent_timestamp()
    user_msg_doc = EmbeddedMessage(sender="user", text=user_message, timestamp=now)
    bot_msg_doc = EmbeddedMessage(sender="bot", text=bot_response, timestamp=now)
    
    db["chats"].update_one(
        {"_id": chat_id},
        {
            "$push": {"messages": {"$each": [
                user_msg_doc.model_dump(), 
                bot_msg_doc.model_dump()
            ]}},
            "$set": {"updated_at": now}
        }
    )
    
    # Auto-generate a title if this is the first message from the user
    if len(chat.messages) == 0:
        try:
            title_prompt = f"Generate ONE short, concise title (4-5 words, NO extra text, straight to the title) for the following conversation: \n\nUser: {user_message}\n\nAssistant: {bot_response}"
            title_response = llm_model.generate_content(title_prompt)
            new_title = title_response.text.strip().replace('"', '')
            if new_title:
                db["chats"].update_one({"_id": chat_id}, {"$set": {"title": new_title, "updated_at": now}})
                print(f"✅ Updated title to: {new_title}")
        except Exception as api_error:
            print(f"❌ Could not Auto-generate title for chat {chat_id}: {api_error}")
    
    # 5. Return response
    message_count = len(chat.messages) + 2
    return {"reply": bot_response, "sources": sources, "message_count": message_count}
