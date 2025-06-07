from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import OpenAI
import os
import shutil
from pdfminer.high_level import extract_text
import uuid
from . import database

UPLOAD_DIR = "uploads"
DB_DIR = "chromadb"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)
database.init_db()

app = FastAPI(title="PDF-QA RAG Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = Chroma(embedding_function=embeddings, persist_directory=DB_DIR)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
llm = OpenAI(temperature=0.2)


def process_pdf(doc_id: str, file_path: str, filename: str):
    text = extract_text(file_path)
    chunks = text_splitter.split_text(text)
    database.store_chunks(doc_id, filename, chunks)
    metadata = [{"source": filename, "chunk": i} for i in range(len(chunks))]
    vector_store.add_texts(chunks, metadatas=metadata)
    vector_store.persist()

@app.post("/upload")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, file_id + ".pdf")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    background_tasks.add_task(process_pdf, file_id, file_path, file.filename)
    return {"id": file_id, "status": "processing"}

@app.post("/ask")
async def ask_question(query: str):
    docs = vector_store.similarity_search(query, k=4)
    if not docs:
        return JSONResponse({"answer": "No relevant documents found", "sources": []})
    context = "\n\n".join([d.page_content for d in docs])
    prompt = (
        "You are a helpful assistant. Use the following context to answer the question.\n" +
        context +
        f"\nQuestion: {query}\nAnswer:"
    )
    answer = llm(prompt)
    sources = [d.metadata for d in docs]
    return {"answer": answer.strip(), "sources": sources}


