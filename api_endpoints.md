# DocuMind API Endpoints

The API is structured around two main models: **Documents** (`/api/documents`) and **Chat** (`/api/chat`).
Below are the live endpoints and their respective request/response payload structures based on the defined Pydantic schemas.

---

## 1. Documents API
**Base Path:** `/api/documents`

### 1.1 Upload PDF
Uploads a new PDF document.

- **Endpoint:** `POST /upload`
- **Request:**
  - `Content-Type: multipart/form-data`
  - **Body Format (Form-Data):**
    - [file](file:///f:/Bacancy/DocuMind/app/routers/document/routes.py#41-50) (UploadFile, required)
  - **Query Parameters:**
    - `user_id` (string, default: `"default_user"`)
- **Response:** `201 Created`
  ```json
  {
    "id": "string",
    "name": "string",
    "status": "string",
    "message": "Upload successful. Processing started."
  }
  ```

### 1.2 List PDFs
Retrieves all PDFs belonging to a user.

- **Endpoint:** `GET /`
- **Request:**
  - **Query Parameters:**
    - `user_id` (string, default: `"default_user"`)
- **Response:** `200 OK`
  ```json
  {
    "pdfs": [
      {
        "id": "string",
        "name": "string",
        "file_size": 1024, // integer or null
        "total_pages": 12, // integer or null
        "pdf_type": "string | null",
        "ocr_applied": true,
        "status": "string",
        "created_at": "2026-03-06T17:41:32"
      }
    ],
    "total": 1
  }
  ```

### 1.3 Get PDF Status
Gets the processing status of a specific PDF.

- **Endpoint:** `GET /{pdf_id}/status`
- **Path Parameters:** `pdf_id`
- **Response:** `200 OK`
  ```json
  {
    "id": "string",
    "name": "string",
    "status": "queued | processing | ready | failed",
    "progress": 100, // 0-100
    "message": "string | null",
    "pdf_type": "string | null",
    "total_pages": 12 // integer or null
  }
  ```

### 1.4 Get PDF Metadata
Retrieves full metadata for a specific PDF.

- **Endpoint:** `GET /{pdf_id}`
- **Path Parameters:** `pdf_id`
- **Response:** `200 OK`
  ```json
  {
    "id": "string",
    "name": "string",
    "file_size": 1024,
    "total_pages": 12,
    "pdf_type": "string | null",
    "ocr_applied": true,
    "status": "string",
    "created_at": "2026-03-06T17:41:32"
  }
  ```

### 1.5 Get PDF File
Serves the raw PDF file (intended specifically for frontend viewers like react-pdf).

- **Endpoint:** `GET /{pdf_id}/file`
- **Path Parameters:** `pdf_id`
- **Response:** `200 OK`
  - **Content-Type:** `application/pdf`
  - **Body:** Binary PDF File Stream

### 1.6 Delete PDF
Deletes a specific PDF from storage and the database.

- **Endpoint:** `DELETE /{pdf_id}`
- **Path Parameters:** `pdf_id`
- **Response:** `204 No Content` (Empty Response Body)

---

## 2. Chat API
**Base Path:** `/api/chat`

### 2.1 Send Chat Message
Sends a message and returns an AI response with citations. Omit `session_id` to start a new session.

- **Endpoint:** `POST /{pdf_id}`
- **Path Parameters:** `pdf_id`
- **Request:** `application/json`
  ```json
  {
    "message": "string",
    "session_id": "string | null", // optional
    "user_id": "default_user"     // optional, defaults to "default_user"
  }
  ```
- **Response:** `200 OK`
  ```json
  {
    "session_id": "string",
    "message_id": "string",
    "answer": "string",
    "mode": "rag | continuation",
    "follow_up": "string | null",
    "citations": [
      {
        "id": "string",
        "chunk_id": "string | null",
        "page_number": 1,
        "bbox": {
          "x0": 0.0,
          "y0": 0.0,
          "x1": 100.0,
          "y1": 50.0
        },
        "cited_text": "string",
        "relevance_score": 0.95, // float | null
        "is_primary": true
      }
    ]
  }
  ```

### 2.2 Get Chat History
Returns the full conversation history for a specific chat session, including citations.

- **Endpoint:** `GET /{pdf_id}/history/{session_id}`
- **Path Parameters:** `pdf_id`, `session_id`
- **Response:** `200 OK`
  ```json
  {
    "session_id": "string",
    "pdf_id": "string",
    "messages": [
      {
        "id": "string",
        "role": "user | assistant",
        "content": "string",
        "mode": "rag | continuation | null",
        "follow_up": "string | null",
        "citations": [
          // Same structure as the citations object above
        ],
        "created_at": "2026-03-06T17:41:32"
      }
    ]
  }
  ```

### 2.3 Clear Chat History
Clears all messages in an active session (the session frame itself is kept alive).

- **Endpoint:** `DELETE /{pdf_id}/history/{session_id}`
- **Path Parameters:** `pdf_id`, `session_id`
- **Response:** `200 OK`
  ```json
  {
    "success": true,
    "message": "Chat history cleared"
  }
  ```
