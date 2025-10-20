import re
import uuid
import traceback
from typing import List, Tuple, Dict

from app.config import settings

class VectorStoreManager:
    """Manages ChromaDB collections"""
    
    def __init__(self, chroma_client, embedding_model):
        self.client = chroma_client
        self.embedding_model = embedding_model
        self.collections = {}
    
    def get_or_create_collection(self, chat_id: str):
        """Get or create collection for chat"""
        if chat_id in self.collections:
            return self.collections[chat_id]
        
        collection_name = f"chat_{chat_id}"
        
        try:
            collection = self.client.get_collection(collection_name)
            print(f"📂 Retrieved collection: {collection_name}")
        except:
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"chat_id": chat_id}
            )
            print(f"📂 Created collection: {collection_name}")
        
        self.collections[chat_id] = collection
        return collection
    
    def add_chunks(self, collection, chunks: List[Dict]) -> int:
        """Add chunks to collection"""
        if not chunks:
            return 0
        
        try:
            documents = [chunk["content"] for chunk in chunks]
            metadatas = []
            
            for chunk in chunks:
                meta = chunk["metadata"].copy()
                cleaned_meta = {}
                for k, v in meta.items():
                    str_val = str(v)
                    str_val = re.sub(r'[^\w\s\-\.\,\/]', '_', str_val).strip()
                    cleaned_meta[k] = str_val if str_val else "unknown"
                metadatas.append(cleaned_meta)
            
            ids = []
            for i, chunk in enumerate(chunks):
                doc_id = chunk['metadata'].get('doc_id', 'unknown')[:8]
                safe_id = f"doc_{doc_id}_chunk_{i}_{uuid.uuid4().hex[:6]}"
                safe_id = re.sub(r'[^\w\-]', '_', safe_id)
                ids.append(safe_id)
            
            embeddings = self.embedding_model.encode(documents, show_progress_bar=True, batch_size=32)
            
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                end_idx = min(i + batch_size, len(documents))
                collection.add(
                    documents=documents[i:end_idx],
                    metadatas=metadatas[i:end_idx],
                    ids=ids[i:end_idx],
                    embeddings=embeddings[i:end_idx].tolist()
                )
            
            print(f"✅ Added {len(documents)} chunks to {collection.name}")
            return len(documents)
            
        except Exception as e:
            print(f"❌ Error adding chunks: {e}")
            if 'metadatas' in locals() and metadatas: print(f"   Sample metadata: {metadatas[0]}")
            if 'ids' in locals() and ids: print(f"   Sample ID: {ids[0]}")
            traceback.print_exc()
            return 0
    
    def query(self, collection, query: str, n_results: int = settings.RAG_TOP_K) -> List[Tuple]:
        """Query collection"""
        try:
            query_embedding = self.embedding_model.encode([query])
            results = collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            results_list = []
            seen_content = set()
            
            for doc, meta, dist in zip(documents, metadatas, distances):
                content_hash = doc[:100]
                if content_hash in seen_content: continue
                seen_content.add(content_hash)
                
                similarity = 1 - (dist / 2)
                results_list.append((doc, meta, similarity))
            
            results_list.sort(key=lambda x: x[2], reverse=True)
            return results_list
            
        except Exception as e:
            print(f"❌ Query error: {e}")
            return []
    
    def delete_collection(self, chat_id: str):
        """Delete collection"""
        try:
            collection_name = f"chat_{chat_id}"
            self.client.delete_collection(collection_name)
            if chat_id in self.collections:
                del self.collections[chat_id]
            print(f"🗑️  Deleted collection: {collection_name}")
        except Exception as e:
            print(f"⚠️  Error deleting collection: {e}")
