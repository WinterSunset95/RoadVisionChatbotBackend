import re
import uuid
import traceback
from typing import List, Tuple, Dict

import weaviate
import weaviate.classes.config as wvc
from weaviate.collections.collection import Collection
from app.config import settings

class VectorStoreManager:
    """Manages Weaviate collections"""
    
    def __init__(self, weaviate_client, embedding_model):
        self.client = weaviate_client
        self.embedding_model = embedding_model
    
    def get_or_create_collection(self, chat_id: str) -> Collection:
        """Get or create collection for chat in Weaviate."""
        if not self.client:
            raise Exception("Weaviate client not initialized")
        # Weaviate collection names must start with an uppercase letter and cannot contain hyphens.
        collection_name = f"Chat_{chat_id.replace('-', '')}"
        
        if self.client.collections.exists(collection_name):
            print(f"📂 Retrieved Weaviate collection: {collection_name}")
            return self.client.collections.get(collection_name)
        
        print(f"📂 Creating Weaviate collection: {collection_name}")
        # Note: 'page' is stored as TEXT because it can be 'unknown'.
        return self.client.collections.create(
            name=collection_name,
            properties=[
                wvc.Property(name="content", data_type=wvc.DataType.TEXT),
                wvc.Property(name="source", data_type=wvc.DataType.TEXT),
                wvc.Property(name="page", data_type=wvc.DataType.TEXT),
                wvc.Property(name="doc_id", data_type=wvc.DataType.TEXT),
                wvc.Property(name="doc_type", data_type=wvc.DataType.TEXT),
                wvc.Property(name="type", data_type=wvc.DataType.TEXT),
            ],
            vectorizer_config=wvc.Configure.Vectorizer.none(),
        )
    
    def add_chunks(self, collection: Collection, chunks: List[Dict]) -> int:
        """Add chunks to Weaviate collection"""
        if not self.client or not chunks:
            return 0
        
        try:
            data_objects = []
            for chunk in chunks:
                properties = {
                    "content": chunk["content"],
                    "source": chunk["metadata"].get("source", "unknown"),
                    "page": str(chunk["metadata"].get("page", "0")),
                    "doc_id": chunk["metadata"].get("doc_id", "unknown"),
                    "doc_type": chunk["metadata"].get("doc_type", "unknown"),
                    "type": chunk["metadata"].get("type", "unknown"),
                }
                data_objects.append(properties)
            
            content_for_embedding = [obj["content"] for obj in data_objects]
            vectors = self.embedding_model.encode(content_for_embedding, show_progress_bar=True, batch_size=32)

            with collection.batch.dynamic() as batch:
                for i, data_obj in enumerate(data_objects):
                    batch.add_object(
                        properties=data_obj,
                        vector=vectors[i]
                    )
            
            print(f"✅ Added {len(data_objects)} chunks to Weaviate collection {collection.name}")
            return len(data_objects)

        except Exception as e:
            print(f"❌ Error adding chunks to Weaviate: {e}")
            traceback.print_exc()
            return 0
    
    def query(self, collection: Collection, query: str, n_results: int = settings.RAG_TOP_K) -> List[Tuple]:
        """Query Weaviate collection"""
        if not self.client:
            return []
            
        try:
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            response = collection.query.near_vector(
                near_vector=query_embedding[0],
                limit=n_results,
                include_vector=False
            )
            
            results_list = []
            seen_content = set()
            
            for obj in response.objects:
                doc = obj.properties.get("content", "")
                content_hash = doc[:100]
                if content_hash in seen_content: continue
                seen_content.add(content_hash)
                
                # Weaviate `distance` is cosine distance. Similarity = 1 - distance.
                similarity = 0
                if obj.metadata and obj.metadata.distance is not None:
                    similarity = 1 - obj.metadata.distance
                
                results_list.append((doc, obj.properties, similarity))

            results_list.sort(key=lambda x: x[2], reverse=True)
            return results_list
            
        except Exception as e:
            print(f"❌ Weaviate query error: {e}")
            traceback.print_exc()
            return []
    
    def delete_collection(self, chat_id: str):
        """Delete Weaviate collection"""
        if not self.client:
            return
        collection_name = f"Chat_{chat_id.replace('-', '')}"
        try:
            if self.client.collections.exists(collection_name):
                self.client.collections.delete(collection_name)
                print(f"🗑️  Deleted Weaviate collection: {collection_name}")
        except Exception as e:
            print(f"⚠️  Error deleting Weaviate collection: {e}")

    # --- Renamed ChromaDB Methods for Backup ---
    
    def get_or_create_collection_chroma(self, chat_id: str):
        """Get or create collection for chat"""
        # This is a backup of the old method and should not be used.
        # It references self.collections which is no longer part of __init__
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
        
        # self.collections[chat_id] = collection # This line would now fail
        return collection
    
    def add_chunks_chroma(self, collection, chunks: List[Dict]) -> int:
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
    
    def query_chroma(self, collection, query: str, n_results: int = settings.RAG_TOP_K) -> List[Tuple]:
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
    
    def delete_collection_chroma(self, chat_id: str):
        """Delete collection"""
        try:
            collection_name = f"chat_{chat_id}"
            self.client.delete_collection(collection_name)
            # if chat_id in self.collections: # This line would fail
            #     del self.collections[chat_id]
            print(f"🗑️  Deleted collection: {collection_name}")
        except Exception as e:
            print(f"⚠️  Error deleting collection: {e}")
