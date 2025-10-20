from collections import defaultdict
from typing import List, Dict
import uuid
from app.utils import get_consistent_timestamp

class DocumentStore:
    """Manages document metadata in-memory (to be replaced by a database)."""
    
    def __init__(self):
        self.documents: Dict[str, Dict] = {}
        self.chat_documents: Dict[str, List[str]] = defaultdict(list)
    
    def add_document(self, chat_id: str, doc_metadata: Dict) -> str:
        """Add document and return its unique ID."""
        doc_id = str(uuid.uuid4())
        doc_metadata['doc_id'] = doc_id
        doc_metadata['chat_id'] = chat_id
        doc_metadata['added_at'] = get_consistent_timestamp()
        
        self.documents[doc_id] = doc_metadata
        self.chat_documents[chat_id].append(doc_id)
        
        return doc_id
    
    def get_chat_documents(self, chat_id: str) -> List[Dict]:
        """Get all documents for a specific chat."""
        doc_ids = self.chat_documents.get(chat_id, [])
        return [self.documents[doc_id] for doc_id in doc_ids if doc_id in self.documents]
    
    def remove_document(self, chat_id: str, doc_id: str):
        """Remove document from tracking. (Future implementation)."""
        pass

# Singleton instance for now. Will be managed by dependency injection later.
document_store = DocumentStore()
