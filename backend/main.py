from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import OpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
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
retriever = vector_store.as_retriever(search_kwargs={"k": 4})
qa_chain = ConversationalRetrievalChain.from_llm(llm, retriever)
chat_histories: dict[str, list[tuple[str, str]]] = {}


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
async def ask_question(query: str, chat_id: str | None = None):
    if chat_id is None or chat_id not in chat_histories:
        chat_id = chat_id or str(uuid.uuid4())
        chat_histories.setdefault(chat_id, [])
    history = chat_histories[chat_id]
    result = qa_chain({"question": query, "chat_history": history})
    history.append((query, result["answer"]))
    sources = [d.metadata for d in result.get("source_documents", [])]
    return {
        "chat_id": chat_id,
        "answer": result["answer"].strip(),
        "sources": sources,
    }


