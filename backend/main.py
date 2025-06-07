from fastapi import FastAPI, UploadFile, File, HTTPException
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

UPLOAD_DIR = "uploads"
DB_DIR = "chromadb"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

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

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, file_id + ".pdf")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    text = extract_text(file_path)
    chunks = text_splitter.split_text(text)
    metadata = [{"source": file.filename, "chunk": i} for i in range(len(chunks))]
    vector_store.add_texts(chunks, metadatas=metadata)
    vector_store.persist()
    return {"id": file_id, "chunks": len(chunks)}

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

