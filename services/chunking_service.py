from dataclasses import dataclass

from config import settings
from services.transcript_service import TranscriptItem


@dataclass(frozen=True)
class TranscriptChunk:
    text: str
    start_time: float
    end_time: float


def chunk_transcript(
    transcript: list[TranscriptItem],
    chunk_size: int = settings.chunk_size,
    chunk_overlap: int = settings.chunk_overlap,
) -> list[TranscriptChunk]:
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: list[TranscriptChunk] = []
    current_items: list[TranscriptItem] = []
    current_text = ""

    for item in transcript:
        next_text = f"{current_text} {item.text}".strip()
        if current_items and len(next_text) > chunk_size:
            chunks.append(_build_chunk(current_items))
            current_items, current_text = _overlap_items(current_items, chunk_overlap)
            next_text = f"{current_text} {item.text}".strip()

        current_items.append(item)
        current_text = next_text

    if current_items:
        chunks.append(_build_chunk(current_items))

    return chunks


def _build_chunk(items: list[TranscriptItem]) -> TranscriptChunk:
    start_time = items[0].start
    end_time = items[-1].start + items[-1].duration

    return TranscriptChunk(
        text=" ".join(item.text for item in items),
        start_time=start_time,
        end_time=end_time,
    )


def _overlap_items(items: list[TranscriptItem], chunk_overlap: int) -> tuple[list[TranscriptItem], str]:
    overlap: list[TranscriptItem] = []
    overlap_text = ""

    for item in reversed(items):
        next_text = f"{item.text} {overlap_text}".strip()
        if overlap and len(next_text) > chunk_overlap:
            break
        overlap.insert(0, item)
        overlap_text = next_text

    return overlap, overlap_text
