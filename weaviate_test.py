from pathlib import Path
from typing import Optional

from weaviate.client import WeaviateClient
from weaviate.classes.generate import GenerativeConfig
from app.modules.askai.models.document import ProcessingStage, ProcessingStatus, UploadJob
from app.services.document_service import PDFProcessor
from app.core.services import embedding_model, tokenizer
from app.core.global_stores import upload_jobs

import weaviate
import weaviate.classes.config as wvc
import dotenv
import os
import uuid

dotenv.load_dotenv()

# weaviate_url = os.getenv("WEAVIATE_URL")
# weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
weaviate_url = None
weaviate_api_key = None

client: Optional[WeaviateClient] = None

collection_name = "PdfChunks"

def add_pdf():
    if client is None:
        raise Exception("Weaviate client not initialized.")

    if client.collections.exists(collection_name):
        client.collections.delete(collection_name)
        print(f"Deleted existing '{collection_name}' collection")

    client.collections.create(
        name=collection_name,
        properties=[
            wvc.Property(name="content", data_type=wvc.DataType.TEXT),
            wvc.Property(name="source", data_type=wvc.DataType.TEXT),
            wvc.Property(name="page_number", data_type=wvc.DataType.INT),
        ],
        vector_config = wvc.Configure.Vectors.self_provided(),
    )
    print(f"Created '{collection_name}' collection")

    pdf_path = "./test2.pdf"
    if not Path(pdf_path).exists():
        raise Exception("PDF file not found. Please ensure it exists at path: " + pdf_path)
    
    upload_jobs["test-job"] = UploadJob(
        job_id="test-job",
        filename=Path(pdf_path).name,
        chat_id="test-chat",
        finished_at="",
        chunks_added=0,
        status=ProcessingStatus.QUEUED,
        stage=ProcessingStage.NOT_PROCESSING,
        progress=0,
        error=None
    )
    pdf_processor = PDFProcessor(
        embedding_model=embedding_model,
        tokenizer=tokenizer,
    )
    chunks, _ = pdf_processor.process_pdf(
        job_id="test-job",
        pdf_path=pdf_path,
        doc_id=str(uuid.uuid4()),
        filename=Path(pdf_path).name
    )

    if not chunks:
        raise Exception("Failed to process PDF. No chunks found.")

    print(f"Extracted {len(chunks)} chunks from PDF.")
    data_objects = []
    for chunk in chunks:
        properties = {
            "content": chunk["content"],
            "source": chunk["metadata"]["source"],
            "page_number": int(chunk["metadata"].get("page", 0)),
        }
        data_objects.append(properties)

    content_for_embedding = [obj["content"] for obj in data_objects]
    vectors = embedding_model.encode(content_for_embedding, show_progress_bar=True)

    pdf_chunks_collection = client.collections.get(collection_name)
    with pdf_chunks_collection.batch.dynamic() as batch:
        for i, data_obj in enumerate(data_objects):
            batch.add_object(
                properties=data_obj,
                vector=vectors[i],
            )

    print("✅ Data added to Weaviate.")
    count = pdf_chunks_collection.aggregate.over_all(total_count=True)
    print(f"Collection count: {count.total_count}")
    pass

def ask_questions():
    if client is None:
        raise Exception("Weaviate client not initialized.")

    pdf_chunks_collection = client.collections.get(collection_name)

    print("Enter you questions. Type 'exit' to quit.")

    while True:
        user_query = input("\n> ")
        if user_query.lower() == "exit":
            break

        question_vector = embedding_model.encode(user_query).tolist()
        response = pdf_chunks_collection.generate.near_vector(
            near_vector=question_vector,
            limit=5,
            grouped_task="Answer based mostly on the provided context. If the answer is not in the context, say that you don't know.",
            generative_provider=GenerativeConfig.google(model="gemini-2.0-flash-exp"),
        )

        if response.generated:
            print("\nAnswer:")
            print(response.generated)
        else:
            print("\nNo answer found.")

        print("\nSources:")
        if response.objects:
            for i, obj in enumerate(response.objects):
                print(f"    {i+1}. Source: {obj.properties['source']}, Page: {obj.properties['page_number']}")
        else:
            print("    No sources found.")

try:
    if weaviate_url and weaviate_api_key:
        print("Connecting to Weaviate Cloud Services (WCS)")
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=weaviate.auth.Auth.api_key(weaviate_api_key),
        )
        print("""✅ Connected to Weaviate Cloud Services (WCS)""")
    else:
        print("Connecting to local weaviate instance via docker")
        client = weaviate.connect_to_local()
        print("""✅ Connected to local weaviate instance via docker""")

    if not client.is_ready():
        raise Exception("Weaviate is not ready. Please check if it is running.")

    print("✅ Weaviate connection established.")
    option = int(input("Choose an option:\n1. Add PDF\n2. Ask questions\n"))
    if option == 1:
        add_pdf()
    elif option == 2:
        ask_questions()
    else:
        raise Exception("Invalid option selected.")

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    if client:
        client.close()
        print("✅ Weaviate connection closed.")
