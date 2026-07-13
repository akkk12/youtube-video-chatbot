import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from prompts.study_prompts import FLASHCARDS_PROMPT, MCQS_PROMPT, NOTES_PROMPT, SUMMARY_PROMPT
from services.chunking_service import chunk_transcript
from services.embedding_service import EmbeddingService
from services.gemini_service import GeminiAnswer, GeminiService
from services.retrieval_service import RetrievalService
from services.transcript_service import extract_video_id, fetch_transcript
from services.vector_store_service import VectorStoreService


SUGGESTED_QUESTIONS = [
    "What is the main idea of this video?",
    "What are the key takeaways?",
    "Can you explain the most important example?",
]


def main() -> None:
    st.set_page_config(page_title="YouTube Video Chatbot", page_icon="▶️", layout="wide")
    _init_state()

    with st.sidebar:
        st.title("YouTube Video Chatbot")
        url = st.text_input("YouTube URL")

        if st.button("Process", type="primary", use_container_width=True):
            _process_video(url)

        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []

        st.divider()
        st.subheader("Processed videos")
        if st.session_state.processed_videos:
            for video_id in st.session_state.processed_videos:
                if st.button(video_id, key=f"video_{video_id}", use_container_width=True):
                    st.session_state.current_video_id = video_id
                    st.session_state.messages = []
        else:
            st.caption("No videos processed yet.")

    st.title("Ask questions about the video")

    if not st.session_state.current_video_id:
        st.info("Paste a YouTube URL and process it to begin.")
        return

    _render_study_buttons()
    _render_messages()

    prompt = st.chat_input("Ask a question")
    if prompt:
        _ask(prompt)

    st.divider()
    st.subheader("Suggested questions")
    for question in SUGGESTED_QUESTIONS:
        if st.button(question, key=f"suggested_{question}"):
            _ask(question)


def _init_state() -> None:
    defaults = {
        "messages": [],
        "processed_videos": [],
        "current_video_id": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _process_video(url: str) -> None:
    if not url.strip():
        st.warning("Enter a YouTube URL.")
        return

    with st.spinner("Processing transcript..."):
        try:
            video_id = extract_video_id(url)
            transcript = fetch_transcript(url)
            chunks = chunk_transcript(transcript)
            embeddings = EmbeddingService().embed_texts([chunk.text for chunk in chunks])
            VectorStoreService().add_chunks(video_id, chunks, embeddings)
        except Exception as exc:
            st.error(str(exc))
            return

    st.session_state.current_video_id = video_id
    if video_id not in st.session_state.processed_videos:
        st.session_state.processed_videos.append(video_id)
    st.success(f"Processed {len(chunks)} transcript chunks.")


def _ask(question: str) -> None:
    st.session_state.messages.append({"role": "user", "content": question})

    with st.spinner("Answering from transcript..."):
        try:
            retriever = RetrievalService()
            chunks = retriever.retrieve(st.session_state.current_video_id, question)
            answer = GeminiService().answer_question(question, chunks)
        except Exception as exc:
            st.error(str(exc))
            return

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()


def _render_study_buttons() -> None:
    cols = st.columns(4)
    actions = [
        ("Summarize", SUMMARY_PROMPT),
        ("Notes", NOTES_PROMPT),
        ("Flashcards", FLASHCARDS_PROMPT),
        ("MCQs", MCQS_PROMPT),
    ]

    for col, (label, prompt) in zip(cols, actions):
        if col.button(label, use_container_width=True):
            _ask(prompt)


def _render_messages() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            content = message["content"]
            if isinstance(content, GeminiAnswer):
                _render_answer(content)
            else:
                st.write(content)


def _render_answer(answer: GeminiAnswer) -> None:
    st.write(answer.answer)
    st.write(f"Confidence: {round(answer.confidence * 100)}%")

    if answer.sources:
        first_source = answer.sources[0]
        st.caption(f"📍 Mentioned at: {_format_time(first_source.start_time)} - {_format_time(first_source.end_time)}")

        with st.expander("📄 Sources Used"):
            for index, source in enumerate(answer.sources, start=1):
                st.markdown(f"**Source {index}: {_format_time(source.start_time)} - {_format_time(source.end_time)}**")
                st.write(source.text)
                st.caption(f"Similarity: {round(source.similarity_score * 100)}%")


def _format_time(seconds: float) -> str:
    total_seconds = int(seconds)
    minutes, second = divmod(total_seconds, 60)
    hour, minute = divmod(minutes, 60)

    if hour:
        return f"{hour}:{minute:02d}:{second:02d}"
    return f"{minute}:{second:02d}"


if __name__ == "__main__":
    main()
