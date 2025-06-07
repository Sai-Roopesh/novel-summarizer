# Usage Guide

This guide describes how to start the PDF assistant and interact with it.

## Prerequisites

- Docker and docker-compose installed
- An OpenAI API key set in the environment as `OPENAI_API_KEY`
- Docker daemon running (start Docker Desktop or use `colima start` on macOS)

## Starting the services

1. Clone this repository

```bash
git clone <repo-url>
cd novel-summarizer
```

2. Build and start all containers:

```bash
docker-compose up --build
```

The FastAPI backend will be running on [http://localhost:8000](http://localhost:8000) and the React frontend on [http://localhost:3000](http://localhost:3000).

## Using the application

1. Open the frontend in your browser at `http://localhost:3000`.
2. Upload one or more PDF files using the upload form.
3. Once uploaded, enter a question about the PDFs in the chat box and send it.
4. The assistant will stream back an answer with footnotes linking to the relevant snippets.
5. Click a citation footnote to view the original text chunk from the PDF.

All uploaded files are processed in the background and embeddings are stored in a local Chroma database. Chat history is kept when you include the `chat_id` parameter in subsequent `/ask` requests.

## Evaluation

An evaluation script is provided in `evaluation/evaluate.py`. After the services are running, execute:

```bash
python evaluation/evaluate.py
```

to run the sample question set and view basic F1 and recall metrics.

