from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import OpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.callbacks.manager import get_openai_callback
import logging
import time
import os
import shutil
from pdfminer.high_level import extract_text
import uuid
import database

UPLOAD_DIR = "uploads"
DB_DIR = "chromadb"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)
database.init_db()

app = FastAPI(title="PDF-QA RAG Agent")
logging.basicConfig(level=logging.INFO)
REQUEST_LIMIT = 20
WINDOW = 60
request_times: list[float] = []
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    now = time.time()
    global request_times
    request_times = [t for t in request_times if now - t < WINDOW]
    if len(request_times) >= REQUEST_LIMIT:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
    request_times.append(now)
    return await call_next(request)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = Chroma(embedding_function=embeddings, persist_directory=DB_DIR)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
llm = OpenAI(temperature=0.2)
retriever = vector_store.as_retriever(search_kwargs={"k": 4})
qa_chain = ConversationalRetrievalChain.from_llm(llm, retriever)
chat_histories: dict[str, list[tuple[str, str]]] = {}


class AskRequest(BaseModel):
    query: str
    chat_id: str | None = None


def process_pdf(doc_id: str, file_path: str, filename: str):
    text = extract_text(file_path)
    chunks = text_splitter.split_text(text)
    database.store_chunks(doc_id, filename, chunks)
    metadata = [
        {"source": filename, "doc_id": doc_id, "chunk": i}
        for i in range(len(chunks))
    ]
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
async def ask_question(payload: AskRequest):
    query = payload.query
    chat_id = payload.chat_id
    if chat_id is None or chat_id not in chat_histories:
        chat_id = chat_id or str(uuid.uuid4())
        chat_histories.setdefault(chat_id, [])
    history = chat_histories[chat_id]
    with get_openai_callback() as cb:
        result = qa_chain({"question": query, "chat_history": history})
    logging.info(
        "tokens prompt=%s completion=%s total=%s",
        cb.prompt_tokens,
        cb.completion_tokens,
        cb.total_tokens,
    )
    history.append((query, result["answer"]))
    sources = [d.metadata for d in result.get("source_documents", [])]
    return {
        "chat_id": chat_id,
        "answer": result["answer"].strip(),
        "sources": sources,
    }


@app.get("/chunk")
async def get_chunk(doc_id: str, chunk: int):
    text = database.get_chunk(doc_id, chunk)
    if text is None:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return {"text": text}


