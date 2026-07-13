from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi


@dataclass(frozen=True)
class TranscriptItem:
    text: str
    start: float
    duration: float


def extract_video_id(url: str) -> str:
    parsed = urlparse(url.strip())

    if parsed.hostname in {"youtu.be", "www.youtu.be"}:
        return parsed.path.strip("/")

    if parsed.hostname in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
            if video_id:
                return video_id

        for prefix in ("/embed/", "/shorts/"):
            if parsed.path.startswith(prefix):
                return parsed.path.removeprefix(prefix).split("/")[0]

    raise ValueError("Invalid YouTube URL")


def fetch_transcript(url: str, languages: list[str] | None = None) -> list[TranscriptItem]:
    video_id = extract_video_id(url)
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages or ["en"])

    return [
        TranscriptItem(
            text=item["text"].strip(),
            start=float(item["start"]),
            duration=float(item["duration"]),
        )
        for item in transcript
        if item.get("text", "").strip()
    ]
