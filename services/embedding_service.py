from sentence_transformers import SentenceTransformer

from config import settings


class EmbeddingService:
    def __init__(self, model_name: str = settings.embedding_model) -> None:
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]
