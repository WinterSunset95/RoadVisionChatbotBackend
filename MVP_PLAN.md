# Ceigall AI Platform - MVP Development Plan

This document outlines the Minimum Viable Product (MVP) features for each of the seven core modules of the Ceigall AI Platform, along with a proposed development timeline.

---

## MVP Features Per Module

### 1. Authentication (SSO) Module MVP
**Focus:** Establish a secure foundation for user registration and login.
- **User Registration:** Endpoint to register users via `@ceigall.com` email and password.
- **User Login:** Endpoint to authenticate users and return a JWT access token.
- **Security:** Implement a token validation dependency to protect all module endpoints.
- **Database:** Create the `Users` table with essential fields (id, email, hashed\_password, role).

### 2. Ask CeigallAI Module MVP
**Focus:** Integrate the existing chatbot functionality with the new authentication system.
- **Authentication Integration:** Secure all existing `askai` endpoints.
- **User-Scoped Data:** Associate `Chats`, `Messages`, and `Documents` with the logged-in `user_id`.
- **Core RAG Functionality:** Retain the ability to create a chat, upload a single PDF, and query its content.

### 3. TenderIQ Module MVP
**Focus:** Deliver the core value proposition of AI-powered analysis for a single tender document.
- **Manual Tender Creation:** Endpoint to create a new tender record.
- **Document Upload:** Endpoint to upload a single tender document (PDF) and associate it with a tender.
- **Core AI Analysis:** A service to extract and save an executive summary, eligibility criteria, and key deadlines.
- **API Endpoints:** Endpoints to list tenders and retrieve the analysis for a single tender.

### 4. LegalIQ Module MVP
**Focus:** Establish the central case management system.
- **Case Management (CRUD):** Endpoints to create, read, update, and delete a legal case.
- **Document Association:** An endpoint to upload and link a document to a specific case.
- **API Endpoints:** Endpoints to list all cases and retrieve the details of a single case.

### 5. Dashboard Module MVP
**Focus:** Provide the necessary data for a basic user dashboard.
- **API Endpoint:** A single endpoint to provide data for summary cards (e.g., Total Active Users, Tenders Analyzed).
- **Recent Activity:** An endpoint to return the last 5 activities for the logged-in user.

### 6. DMSIQ Module MVP
**Focus:** Establish the integration point for a future Document Management System.
- **API Endpoint:** A mock endpoint (`/import-from-dms`) that simulates adding a document to an `Ask CeigallAI` chat context.

### 7. DesignIQ Module MVP
**Focus:** Register the module for future development.
- **Module Scaffolding:** Create the `app/modules/designiq` directory structure.
- **Placeholder Endpoint:** A single, secured endpoint returning a mock success message.

---

## Proposed Timeline

This timeline is structured in phases to deliver foundational components first and build upon them.

### Phase 1: Foundation - SSO & Core Setup (4-6 weeks)
- **Implement:** The Authentication (SSO) Module MVP.
- **Define:** The initial database schemas for all 7 modules using Alembic.
- **Integrate:** JWT-based security across all module routers.

### Phase 2: Core AI & UI Data - Ask CeigallAI & Dashboard (3-5 weeks)
- **Implement:** The Ask CeigallAI Module MVP, integrating it with the new authentication system.
- **Implement:** The Dashboard Module MVP to provide data for the main user dashboard.

### Phase 3: New Business Modules - TenderIQ & LegalIQ (8-10 weeks)
- **Implement:** The TenderIQ Module MVP.
- **Implement:** The LegalIQ Module MVP.

### Phase 4: Placeholder Integrations - DMSIQ & DesignIQ (2-3 weeks)
- **Implement:** The DMSIQ Module MVP.
- **Implement:** The DesignIQ Module MVP.
