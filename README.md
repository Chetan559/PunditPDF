# 📄 PunditPDF: AI-powered Document Intelligence

**PunditPDF** is a full-stack RAG (Retrieval-Augmented Generation) application that allows users to upload PDF documents and have natural language conversations with their content. Built with a high-performance **FastAPI** backend and a responsive **React** frontend.

---

## 🏗️ System Architecture

The application follows a modern decoupled architecture:

- **Frontend:** React.js (Vite) for a seamless UI/UX.
- **Backend:** FastAPI for high-speed asynchronous API processing.
- **AI Engine:** LangChain for document chunking and LLM orchestration.
- **Vector Store:** FAISS / ChromaDB for efficient similarity search.

---

## ✨ Key Features

- **Asynchronous Processing:** Handle large PDFs without freezing the UI.
- **Persistent Chat History:** Context-aware conversations.
- **Citations & References:** See exactly where the AI found the information.
- **RESTful API:** Clean separation between the data layer and the presentation layer.

---

## 🚀 Getting Started

### 1. Backend Setup (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Create .env with your OPENAI_API_KEY
uvicorn main:app --reload
```

### folder structure

```text
project_root/
│
├── main.py                 # Entry point of the FastAPI application.
├── requirements.txt        # Lists project dependencies.
│
├── middlewares/            # Contains middleware logic like logging, CORS, or request processing.
├── repos/                  # Handles direct database operations (CRUD queries).
├── routers/                # Defines API endpoints and handles HTTP requests.
├── schemas/                # Contains Pydantic models for request and response validation.
├── services/               # Contains business logic and application rules.
└── utils/                  # Helper functions like security, hashing, JWT creation.
```
