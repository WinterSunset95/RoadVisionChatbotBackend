import uuid
from typing import Dict, List
from sqlalchemy.orm import Session

from app.core.services import llm_model, vector_store
from app.db import crud
from app.config import settings

def send_message_to_chat(db: Session, chat_id: uuid.UUID, user_message: str) -> Dict:
    """
    Handles the RAG pipeline for a user message.
    1. Retrieves context from vector store.
    2. Builds a prompt.
    3. Calls the LLM.
    4. Saves conversation history to DB.
    5. Returns the response.
    """
    # Check if chat exists
    chat = crud.get_chat(db, chat_id)
    if not chat:
        raise ValueError("Chat not found")

    # 1. Retrieve context
    chat_docs = chat.documents
    context_text = ""
    sources = []
    
    if chat_docs:
        collection = vector_store.get_or_create_collection(chat_id)
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
1. Answer using ONLY the information in the context above
2. Be specific and cite which sources support your answer
3. If the context doesn't contain the answer, clearly state: "I don't have that information in the provided documents"
4. Be concise but thorough"""
    else:
        prompt = f"""You are a helpful AI assistant. Please answer: {user_message}"""
        
    # 3. Call LLM
    recent_history = crud.get_chat_messages(db, chat_id)[-10:]
    gemini_history = [{"role": msg.sender, "parts": [{"text": msg.text}]} for msg in recent_history]
    gemini_history.append({"role": "user", "parts": [{"text": prompt}]})
    
    try:
        response = llm_model.generate_content(gemini_history)
        bot_response = response.text if hasattr(response, "text") else "I couldn't generate a response."
    except Exception as api_error:
        print(f"❌ Gemini API error: {api_error}")
        bot_response = f"I encountered an error: {str(api_error)}"

    # 4. Save conversation to DB
    crud.add_message(db, chat_id=chat_id, sender="user", text=user_message)
    crud.add_message(db, chat_id=chat_id, sender="bot", text=bot_response)
    
    # The message count will be retrieved on the next request.
    message_count = len(recent_history) + 2
    
    # 5. Return response
    return {"reply": bot_response, "sources": sources, "message_count": message_count}
