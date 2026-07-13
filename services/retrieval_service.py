from dataclasses import dataclass

from config import settings
from services.embedding_service import EmbeddingService
from services.vector_store_service import VectorStoreService


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    start_time: float
    end_time: float
    similarity_score: float


class RetrievalService:
    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        vector_store: VectorStoreService | None = None,
    ) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or VectorStoreService()

    def retrieve(
        self,
        video_id: str,
        query: str,
        top_k: int = settings.retrieval_top_k,
    ) -> list[RetrievedChunk]:
        query_embedding = self.embedding_service.embed_query(query)
        results = self.vector_store.query(video_id, query_embedding, top_k)

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        return [
            RetrievedChunk(
                text=document,
                start_time=float(metadata["start_time"]),
                end_time=float(metadata["end_time"]),
                similarity_score=max(0.0, 1.0 - float(distance)),
            )
            for document, metadata, distance in zip(documents, metadatas, distances)
        ]
