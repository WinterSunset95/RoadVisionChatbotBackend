# Backend Migration & Overhaul Plan

This document outlines the plan to migrate our RAG chatbot backend from a single-file Flask proof-of-concept to a scalable, robust, and maintainable production-grade system using FastAPI and other industry-standard technologies.

## Guiding Principles

- **Zero Downtime for Frontend**: All API endpoints must remain 100% backward compatible throughout the migration. The contract (URLs, request methods, request bodies, and response structures) must not change.
- **Phased Approach**: The migration will be executed in distinct phases to minimize risk and allow for testing at each stage.
- **Scalability & Reliability**: The new architecture must be designed to handle increased load, provide better error handling, and be more resilient.
- **Maintainability**: The codebase will be refactored into logical modules to improve readability and make future development easier.

---

## Phase 1: Framework Migration (Flask to FastAPI)

**Goal**: Replace the web framework without altering the core application logic. This provides immediate benefits like automatic API documentation and improved performance.

1.  **Backup Legacy App**: Rename the current `app.py` to `app_legacy_flask.py`. This file will serve as a reference for API behavior and logic.
2.  **Setup FastAPI**: Create a new `app.py` with a basic FastAPI application.
3.  **Dependency Management**: Add FastAPI, Uvicorn, and Pydantic to `requirements.txt`.
4.  **Re-implement Endpoints**:
    -   Create FastAPI routers to organize endpoints logically (e.g., `chats.py`, `documents.py`).
    -   Re-implement every endpoint from `app_legacy_flask.py`.
    -   Use Pydantic models to define request and response schemas, which enables automatic validation and documentation.
5.  **API Contract Conformance**:
    -   Rigorously test the new FastAPI endpoints against the old ones to ensure the data format and behavior are identical. The auto-generated `/docs` page will be invaluable here.
    -   The core business logic (e.g., how PDFs are processed, how ChromaDB is queried) will be copied directly from the old application for now.

---

## Phase 2: Database & State Management Overhaul

**Goal**: Replace fragile file-based storage and in-memory state with a robust database system.

1.  **Introduce PostgreSQL**:
    -   Set up a PostgreSQL database.
    -   Use SQLAlchemy as the ORM to interact with the database.
    -   Define models for `Chat`, `Message`, `Document`, and `ProcessingJob`.
    -   Integrate Alembic for managing database schema migrations.
2.  **Migrate Data**:
    -   Replace all calls to `load_json` and `save_json` (for `chat_history.json` and `memory_*.json`) with SQLAlchemy database operations.
    -   Create a one-time migration script to transfer existing chat data from JSON files into the PostgreSQL database.
3.  **Introduce Redis**:
    -   Set up a Redis instance.
    -   Replace the global `upload_jobs` dictionary with Redis. This makes the state of upload jobs persistent and accessible across multiple server instances.

---

## Phase 3: Asynchronous Task Processing with Celery

**Goal**: Move heavy document processing out of the main application thread to improve API responsiveness and reliability.

1.  **Integrate Celery**:
    -   Add Celery to the project.
    -   Configure Redis as the Celery message broker.
2.  **Create Celery Tasks**:
    -   Move the entire `process_pdf` function (including text extraction, chunking, embedding, and vector store insertion) into a dedicated Celery task.
3.  **Update Upload Endpoint**:
    -   The `/upload-pdf` endpoint will now simply create a record in the `ProcessingJob` table (in PostgreSQL) and queue the Celery task.
    -   The task status endpoint (`/api/upload-status/<job_id>`) will now query the job status from the PostgreSQL database, which will be updated by the Celery worker upon completion or failure.

---

## Phase 4: RAG Orchestration Refactor

**Goal**: Simplify the RAG pipeline code by leveraging a specialized framework.

1.  **Integrate LangChain (or LlamaIndex)**:
    -   Choose and add the preferred orchestration framework to the project.
2.  **Refactor Core Logic**:
    -   Replace the manual implementation in `PDFProcessor` and `VectorStoreManager` with high-level abstractions from the chosen framework.
    -   Use the framework's document loaders, text splitters, embedding integrations, and vector store integrations.
3.  **Benefits**: This will significantly reduce boilerplate code, make the RAG pipeline more modular, and allow for easy experimentation with different models, chunking strategies, or vector databases in the future.

---

## Phase 5: Production Readiness

**Goal**: Prepare the application for deployment and scaling.

1.  **Managed Vector Database**:
    -   Evaluate and potentially migrate from local ChromaDB to a managed or more scalable solution like Pinecone, Weaviate, or PostgreSQL with the `pgvector` extension. This choice depends on performance, cost, and operational requirements.
2.  **Containerization**:
    -   Create a `Dockerfile` to containerize the application, including the FastAPI server and Celery workers.
    -   Use `docker-compose.yml` to define the full stack (app, workers, PostgreSQL, Redis) for local development and testing.
3.  **CI/CD Pipeline**:
    -   Set up a CI/CD pipeline (e.g., using GitHub Actions) to automate testing and deployment.
