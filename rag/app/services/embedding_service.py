from sentence_transformers import SentenceTransformer
from shared.base_service import BaseService

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


class EmbeddingService(BaseService):
    def __init__(self) -> None:
        super().__init__()
        self._model: SentenceTransformer | None = None

    def load(self) -> None:
        if self._model is None:
            self._model = SentenceTransformer(MODEL_NAME)

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            raise RuntimeError("Embeddings model not loaded.")
        return self._model

    def embed_text(self, text: str) -> list[float]:
        vector = self._get_model().encode(text, normalize_embeddings=True)
        return vector.tolist()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors = self._get_model().encode(texts, normalize_embeddings=True)
        return vectors.tolist()


embedding_service = EmbeddingService()
