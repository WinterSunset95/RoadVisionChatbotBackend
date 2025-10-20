from typing import Dict, List

from app.core.services import (
    llm_model, vector_store, document_store, active_conversations
)
from app.db import file_store
from app.utils import get_consistent_timestamp
from app.config import settings

def send_message_to_chat(chat_id: str, user_message: str) -> Dict:
    """
    Handles the RAG pipeline for a user message.
    1. Retrieves context from vector store.
    2. Builds a prompt.
    3. Calls the LLM.
    4. Saves conversation history.
    5. Returns the response.
    """
    if chat_id not in active_conversations:
        active_conversations[chat_id] = file_store.load_conversation(chat_id)
    conversation = active_conversations[chat_id]

    # 1. Retrieve context
    chat_docs = document_store.get_chat_documents(chat_id)
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
    recent_history = conversation[-10:]
    gemini_history = [{"role": msg["role"], "parts": [{"text": msg["parts"][0]}]} for msg in recent_history]
    gemini_history.append({"role": "user", "parts": [{"text": prompt}]})
    
    try:
        response = llm_model.generate_content(gemini_history)
        bot_response = response.text if hasattr(response, "text") else "I couldn't generate a response."
    except Exception as api_error:
        print(f"❌ Gemini API error: {api_error}")
        bot_response = f"I encountered an error: {str(api_error)}"
    
    # 4. Save conversation
    conversation.append({"role": "user", "parts": [user_message], "timestamp": get_consistent_timestamp()})
    conversation.append({"role": "model", "parts": [bot_response], "timestamp": get_consistent_timestamp()})
    file_store.save_conversation(chat_id, conversation)
    
    # Update chat metadata
    chat_history = file_store.load_chat_history()
    for chat in chat_history:
        if chat["id"] == chat_id:
            chat["message_count"] = len(conversation)
            chat["updated_at"] = get_consistent_timestamp()
            break
    file_store.save_chat_history(chat_history)
    
    # 5. Return response
    return {"reply": bot_response, "sources": sources, "message_count": len(conversation)}
