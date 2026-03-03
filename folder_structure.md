app/
│
├── main.py
│
├── middlewares/
│ ├── cors.py
│ ├── logging.py
│ └── rate_limit.py
│
├── routers/
│ ├── document/
│ │ └── routes.py
│ ├── rag/
│ │ └── routes.py
│ ├── quiz/
│ │ └── routes.py
│ ├── evaluation/
│ │ └── routes.py
│ └── health.py
│
├── schemas/
│ ├── document/
│ │ ├── request.py
│ │ └── response.py
│ ├── rag/
│ │ ├── request.py
│ │ └── response.py
│ ├── quiz/
│ │ ├── request.py
│ │ └── response.py
│ ├── evaluation/
│ │ └── response.py
│ └── common.py
│
├── services/
│ ├── document/
│ │ ├── document_service.py
│ │ ├── ingestion_service.py
│ │ └── indexing_service.py
│ │
│ ├── rag/
│ │ ├── rag_service.py
│ │ ├── retriever.py
│ │ ├── intent_service.py
│ │ └── citation_service.py
│ │
│ ├── quiz/
│ │ ├── generator_service.py
│ │ ├── session_service.py
│ │ └── grading_service.py
│ │
│ ├── evaluation/
│ │ ├── evaluation_service.py
│ │ └── recommendation_service.py
│ │
│ ├── llm_service.py
│ └── embedding_service.py
│
├── repos/
│ ├── document/
│ │ └── document_repo.py
│ ├── quiz/
│ │ └── quiz_session_repo.py
│ └── vector_store_repo.py
│
├── utils/
│ ├── pdf_utils.py
│ ├── bbox_utils.py
│ ├── prompt_builder.py
│ ├── config.py
│ └── constants.py
│
└── requirements.txt
