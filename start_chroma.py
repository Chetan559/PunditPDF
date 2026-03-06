import os
import uvicorn

# Force Chroma to use the local folder and stay persistent
os.environ["PERSIST_DIRECTORY"] = "./chroma_db"
os.environ["IS_PERSISTENT"] = "TRUE"
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"

if __name__ == "__main__":
    print("🚀 Starting ChromaDB Server directly via Uvicorn...")
    uvicorn.run("chromadb.app:app", host="127.0.0.1", port=8555, log_level="info")