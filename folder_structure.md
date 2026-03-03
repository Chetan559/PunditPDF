app/
│
├── main.py
│
├── core/
│ ├── config.py
│ ├── database.py
│ ├── dependencies.py
│ └── exceptions.py
│
├── middlewares/
│ ├── cors.py
│ ├── logging.py
│ └── rate_limit.py
│
├── models/
│ ├── user.py
│ ├── pdf.py
│ ├── chunk.py
│ ├── chat.py
│ ├── citation.py
│ └── quiz.py
│
├── routers/
│ ├── document/
│ │ └── routes.py
│ ├── chat/
│ │ └── routes.py
│ ├── quiz/
│ │ └── routes.py
│ ├── citation/
│ │ └── routes.py
│ └── health.py
│
├── schemas/
│ ├── document/
│ │ ├── request.py
│ │ └── response.py
│ ├── chat/
│ │ ├── request.py
│ │ └── response.py
│ ├── quiz/
│ │ ├── request.py
│ │ └── response.py
│ └── common.py
│
├── services/
│ ├── document/
│ │ ├── document_service.py
│ │ ├── ingestion_service.py
│ │ └── indexing_service.py
│ ├── rag/
│ │ ├── rag_service.py
│ │ ├── retriever.py
│ │ ├── intent_service.py
│ │ └── citation_service.py
│ ├── quiz/
│ │ ├── generator_service.py
│ │ ├── session_service.py
│ │ ├── grading_service.py
│ │ ├── evaluation_service.py
│ │ └── recommendation_service.py
│ ├── prompts/
│ │ ├── rag_prompts.py
│ │ ├── quiz_prompts.py
│ │ └── evaluation_prompts.py
│ ├── llm_service.py
│ └── embedding_service.py
│
├── repos/
│ ├── document/
│ │ ├── document_repo.py
│ │ └── chunk_repo.py
│ ├── chat/
│ │ ├── session_repo.py
│ │ ├── message_repo.py
│ │ └── citation_repo.py
│ ├── quiz/
│ │ ├── quiz_session_repo.py
│ │ ├── quiz_question_repo.py
│ │ └── quiz_answer_repo.py
│ └── vector_store_repo.py
│
├── tasks/
│ ├── pdf_processing_task.py
│ └── worker.py
│
├── utils/
│ ├── pdf_utils.py
│ └── bbox_utils.py
│
└── pyproject.toml # uv uses this not requirements.txt
