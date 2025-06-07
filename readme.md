### Project Design Plan — PDF-QA RAG Agent

---

#### 1. Project Title

**“Ask-Me-Anything PDF Assistant: A Retrieval-Augmented Generation (RAG) System”**

---

#### 2. 1-Sentence Pitch

> *Build an AI agent that ingests any number of PDF documents, stores their knowledge in a vector database, and answers natural-language questions with cited snippets—as fast as ChatGPT, but with your PDFs as the brain.*

---

#### 3. Learning / Portfolio Objectives

| Theme        | What you’ll practice                                                  |
| ------------ | --------------------------------------------------------------------- |
| **AI & NLP** | Text extraction, embedding, similarity search, prompt engineering     |
| **Backend**  | FastAPI endpoints, async file uploads, chunked batch jobs             |
| **Data Ops** | Vector DB basics (Chroma / Qdrant / Pinecone), metadata design        |
| **DevOps**   | Docker, docker-compose, CI (GitHub Actions) + optional k8s helm chart |
| **Product**  | Citation UX, streaming answers, guardrails & eval harness             |

*(Use or drop the table as the vibe-coding platform prefers; it highlights concrete skills earned.)*

---

#### 4. High-Level Architecture

```
┌──────────┐  PDFs  ┌───────────────┐  chunks+meta ┌───────────┐  top-k  ┌───────────┐
│  Client  │ ─────► │  Ingestion &  │ ───────────► │ Vector DB │ ───────► │ Retriever │
│  (UI/API)│        │  Pre-Process  │              └───────────┘          └────┬──────┘
└────┬─────┘        └──────┬────────┘                               Retrieved │ context
     │      Query            │                                        ┌───────▼──────┐
     │                       │                                        │   RAG LLM    │
     └───────────────────────────────────────────────────────────────► │ (Generator) │
                                                                      └──────┬──────┘
                                                                             │ Answer + sources
                                                                      ┌──────▼──────┐
                                                                      │  Streaming  │
                                                                      │   Backend   │
                                                                      └─────────────┘
```

*Explanation*:

1. **Ingestion** – PDF → text (pdfminer or Tesseract-OCR fallback) → chunk (≈ 400-token windows, 50-token overlap) → embed.
2. **Storage** – Chunk embeddings + metadata (`doc_id`, `page`, `chunk_id`) into vector store.
3. **Retrieval** – Embed user query → `k` nearest neighbor search.
4. **Generation** – Compose prompt *system + retrieved context + user query* and hit LLM (open-source Llama 3-70B or OpenAI GPT-4o).
5. **Post-processing** – Return answer + highlighted citations; stream tokens to UI for perceived speed.

---

#### 5. Core Components & Tech Stack

| Layer             | Choice (default)                                                        | Alternatives                            |
| ----------------- | ----------------------------------------------------------------------- | --------------------------------------- |
| **PDF → Text**    | `pdfminer.six` + `pytesseract` (images)                                 | Adobe PDF-Services API                  |
| **Embeddings**    | `sentence-transformers/all-MiniLM-L6-v2`                                | OpenAI `text-embedding-3-small`, Cohere |
| **Vector DB**     | **Chroma** (local quick-start)                                          | Pinecone / Qdrant / Weaviate / FAISS    |
| **Orchestration** | **LangChain** (DocumentLoader, Retriever, ConversationalRetrievalChain) | llama-index or vanilla SDK              |
| **LLM**           | `gpt-4o` via API                                                        | Llama-3 with Ollama / vLLM              |
| **API**           | **FastAPI**                                                             | Flask, Django                           |
| **UI**            | React + SWR streaming                                                   | Next.js / Vue / Svelte                  |
| **Deployment**    | Docker compose                                                          | Helm/Kubernetes, Render, Fly.io         |

---

#### 6. Step-by-Step Roadmap

| Phase                                | Milestones                                                                                                             | Hints                                                      |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| **Week 1: Setup & Ingestion**        | • FastAPI endpoints for `/upload` and `/ask`  <br>• Parse & store text in SQLite for debugging                         | Use background `celery` or `asyncio` task for heavy OCR    |
| **Week 2: Vector Store & Retrieval** | • Compute embeddings batch job  <br>• Top-k similarity search                                                          | Store chunk text (< 1 KB) inside DB doc for cheap recall   |
| **Week 3: RAG Loop**                 | • Prototype LangChain ConversationalRetrievalChain  <br>• Return JSON: `{answer, sources}`                             | Keep prompt under \~8 K tokens with `ContextWindowManager` |
| **Week 4: UX & Citations**           | • Simple chat UI, markdown rendering  <br>• Clickable footnotes show original PDF page                                 | Stream SSE / WebSockets for token-level updates            |
| **Week 5: Hardening**                | • Add evaluation harness (`ragas` or custom: answer-ground-truth vs recall)  <br>• Rate limiting, file-type guardrails | Log token counts to foresee billing                        |
| **Stretch**                          | • Multi-tenant auth  <br>• Incremental ingestion watcher for new PDFs  <br>• Fine-tune small LLM on domain Q\&A        | Look-ahead reranking (re-embed top-k with MultiQuery)      |

---

#### 7. Key Design Decisions to Discuss in “Vibe” Prompt

1. **Chunk strategy** – fixed tokens vs semantic splitting (llama-index `SentenceSplitter`); impact on recall vs cost.
2. **Embedding dimensionality** – 384-d MiniLM → fast & cheap; larger models better for nuance.
3. **Citation granularity** – chunk-level vs page-level; influences UX and legal defensibility.
4. **Source-aware prompting** – Use “You MUST cite sources” system rule to reduce hallucinations.
5. **Cold-start latency** – Pre-warm LLM container or use API with streaming.
6. **Cost controls** – Cache embeddings; implement hybrid search (BM25 first pass).

---

#### 8. Deliverables

* ✅ **GitHub repo** with MIT licence
* ✅ `README.md` (1-click `docker-compose up`)
* ✅ Short demo video (< 2 min) answering a sample PDF question
* ✅ Architecture diagram (png/svg) in `/docs`
* ✅ Post-mortem & next steps (10-line reflection)

---

#### 9. Evaluation Rubric (Self/Peer)

| Area             | Excellent (A)                     | Good (B)           | Needs Work |
| ---------------- | --------------------------------- | ------------------ | ---------- |
| **Accuracy**     | ≥ 80 % answer F1 on held-out Qs   | 60-79 %            | < 60 %     |
| **Latency**      | P95 < 3 s                         | 3-5 s              | > 5 s      |
| **Citations**    | 100 % clickable & correct         | Minor mismaps      | Missing    |
| **Code Quality** | Typed, tests, 0 lints             | Some TODOs         | Spaghetti  |
| **UX**           | Live streaming, mobile responsive | Static full answer | Bare JSON  |

---

#### 10. “Vibe Coding-Platform” Prompt (copy-paste ready)

> **Build an “Ask-Me-Anything PDF Assistant”**. Users upload one or many PDFs. Your system extracts text, splits it into \~400-token chunks, embeds with `all-MiniLM-L6-v2`, and stores in a Chroma vector DB.
>
> On each question, embed the query, retrieve the top-k chunks, and feed them plus the question to an LLM (GPT-4o **or** local Llama-3). Stream the answer to the frontend **with footnote citations linking back to the original PDF page**.
>
> Provide Dockerised FastAPI backend, React chat UI, and a one-command `dev` setup. Document design choices and add an evaluation script that reports recall\@k and answer F1 on a small test set. Bonus: authentication, incremental ingestion, live cost tracker.

---

Use (or adapt) this design plan as the blueprint for your project brief—ready for the Vibe coding platform or any hackathon spec. Happy building!
