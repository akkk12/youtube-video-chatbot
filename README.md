# YouTube Video Chatbot

A free-stack chatbot that answers questions from a YouTube video's transcript. It fetches transcript text, chunks it with timestamps, stores embeddings in ChromaDB, retrieves the most relevant transcript passages, and answers using either a local Ollama model or Gemini.

## Features

- Paste a YouTube URL and process its transcript
- Preserve transcript timestamps
- Chunk transcript text with overlap
- Generate embeddings with `sentence-transformers`
- Store and query vectors with ChromaDB
- Ask transcript-grounded questions
- Show timestamp citations, source chunks, and confidence
- Chat history and clear chat button
- Study helpers: summary, notes, flashcards, and MCQs
- Local free LLM support through Ollama
- Optional Gemini support

## Architecture

```text
YouTube URL
    |
    v
Transcript Service
    |
    v
Chunking Service
    |
    v
Embedding Service
    |
    v
ChromaDB Vector Store
    |
    v
Retriever
    |
    v
LLM Service: Ollama or Gemini
    |
    v
Answer + timestamps + source chunks
```

## Project Structure

```text
youtube-chatbot/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── prompts/
│   ├── qa_system.txt
│   └── study_prompts.py
├── services/
│   ├── transcript_service.py
│   ├── chunking_service.py
│   ├── embedding_service.py
│   ├── vector_store_service.py
│   ├── retrieval_service.py
│   └── gemini_service.py
└── ui/
    └── streamlit_app.py
```

## Requirements

- Python 3.11
- Ollama for local free LLM usage
- A YouTube video with an available transcript

## Setup

```bash
cd youtube-chatbot
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Option 1: Run With Free Local Ollama

Install Ollama:

```bash
brew install ollama
```

Use the small model already configured by default:

```bash
ollama pull qwen2.5:0.5b
```

For better answers, use a larger free model:

```bash
ollama pull llama3.2:3b
```

Then update `.env`:

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

Start Ollama:

```bash
ollama serve
```

## Option 2: Run With Gemini

If you have free Gemini quota available, update `.env`:

```bash
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-2.0-flash-lite
```

## Run The Streamlit App

In a terminal with the virtual environment active:

```bash
streamlit run ui/streamlit_app.py
```

Open the local URL Streamlit prints, usually:

```text
http://localhost:8501
```

## Optional FastAPI Health Check

The FastAPI app currently exposes a simple health endpoint:

```bash
uvicorn app:app --reload
```

Then open:

```text
http://127.0.0.1:8000/health
```

## Environment Variables

```bash
LLM_PROVIDER=ollama
GOOGLE_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-2.0-flash-lite
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:0.5b
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHROMA_PERSIST_DIR=chroma_db
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RETRIEVAL_TOP_K=5
```

## Usage

1. Start Ollama if using local LLM mode.
2. Start Streamlit.
3. Paste a YouTube URL in the sidebar.
4. Click `Process`.
5. Ask questions in the chat box.
6. Review timestamp citations and source chunks.

## Notes

- `.env`, `.venv`, `chroma_db`, caches, and local OS files are ignored by Git.
- The app answers from retrieved transcript chunks only.
- If transcript data is missing for a video, try a different video with captions enabled.
