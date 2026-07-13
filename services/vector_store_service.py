from chromadb import PersistentClient
from chromadb.api.models.Collection import Collection

from config import settings
from services.chunking_service import TranscriptChunk


class VectorStoreService:
    def __init__(self, persist_dir: str = settings.chroma_persist_dir) -> None:
        self.client = PersistentClient(path=persist_dir)

    def get_collection(self, video_id: str) -> Collection:
        return self.client.get_or_create_collection(name=f"video_{video_id}")

    def add_chunks(
        self,
        video_id: str,
        chunks: list[TranscriptChunk],
        embeddings: list[list[float]],
    ) -> None:
        collection = self.get_collection(video_id)

        collection.upsert(
            ids=[f"{video_id}_{index}" for index in range(len(chunks))],
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=[
                {
                    "text": chunk.text,
                    "start_time": chunk.start_time,
                    "end_time": chunk.end_time,
                }
                for chunk in chunks
            ],
        )

    def query(
        self,
        video_id: str,
        query_embedding: list[float],
        top_k: int = settings.retrieval_top_k,
    ) -> dict:
        collection = self.get_collection(video_id)
        return collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
