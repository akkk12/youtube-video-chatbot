from dataclasses import dataclass
import json
from pathlib import Path
from urllib import request

import google.generativeai as genai

from config import settings
from services.retrieval_service import RetrievedChunk


PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"
FALLBACK_ANSWER = "I couldn't find this information in the video."


@dataclass(frozen=True)
class GeminiAnswer:
    answer: str
    sources: list[RetrievedChunk]
    confidence: float


class GeminiService:
    def __init__(self, api_key: str = settings.google_api_key, model_name: str = settings.gemini_model) -> None:
        self.provider = settings.llm_provider.lower()
        self.system_prompt = (PROMPT_DIR / "qa_system.txt").read_text(encoding="utf-8")

        if self.provider == "ollama":
            self.model = None
            return

        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def answer_question(self, question: str, chunks: list[RetrievedChunk]) -> GeminiAnswer:
        if not chunks:
            return GeminiAnswer(answer=FALLBACK_ANSWER, sources=[], confidence=0.0)

        try:
            if self.provider == "ollama":
                answer = self._answer_with_ollama(question, chunks)
            else:
                response = self.model.generate_content(
                    [
                        self.system_prompt,
                        f"Transcript context:\n{self._format_context(chunks)}",
                        f"Question: {question}",
                    ]
                )
                answer = response.text.strip() if response.text else FALLBACK_ANSWER
        except Exception as exc:
            answer = self._fallback_answer(question, chunks, exc)

        return GeminiAnswer(
            answer=answer,
            sources=chunks,
            confidence=self._confidence(chunks),
        )

    def run_study_prompt(self, prompt: str, chunks: list[RetrievedChunk]) -> GeminiAnswer:
        return self.answer_question(prompt, chunks)

    def _format_context(self, chunks: list[RetrievedChunk]) -> str:
        return "\n\n".join(
            f"[{_format_time(chunk.start_time)} - {_format_time(chunk.end_time)}]\n{chunk.text}"
            for chunk in chunks
        )

    def _confidence(self, chunks: list[RetrievedChunk]) -> float:
        if not chunks:
            return 0.0
        return round(sum(chunk.similarity_score for chunk in chunks) / len(chunks), 2)

    def _fallback_answer(self, question: str, chunks: list[RetrievedChunk], exc: Exception) -> str:
        if "429" in str(exc) or "quota" in str(exc).lower():
            best = chunks[0]
            return (
                "Gemini quota is currently unavailable, so here is the most relevant transcript passage instead.\n\n"
                f"Mentioned at {_format_time(best.start_time)} - {_format_time(best.end_time)}:\n\n"
                f"{best.text}"
            )
        raise exc

    def _answer_with_ollama(self, question: str, chunks: list[RetrievedChunk]) -> str:
        prompt = (
            f"{self.system_prompt}\n\n"
            f"Transcript context:\n{self._format_context(chunks)}\n\n"
            f"Question: {question}"
        )
        payload = json.dumps(
            {
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
            }
        ).encode("utf-8")
        req = request.Request(
            f"{settings.ollama_base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data.get("response", "").strip() or FALLBACK_ANSWER


def _format_time(seconds: float) -> str:
    total_seconds = int(seconds)
    minutes, second = divmod(total_seconds, 60)
    hour, minute = divmod(minutes, 60)

    if hour:
        return f"{hour}:{minute:02d}:{second:02d}"
    return f"{minute}:{second:02d}"
