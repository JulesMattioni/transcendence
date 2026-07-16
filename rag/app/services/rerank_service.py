from sentence_transformers import CrossEncoder
from shared.base_service import BaseService
from app.config import RERANK_MODEL_NAME


class RerankService(BaseService):
    def __init__(self) -> None:
        super().__init__()
        self._model: CrossEncoder | None = None

    def load(self) -> None:
        if self._model is None:
            self._model = CrossEncoder(RERANK_MODEL_NAME)

    def _get_model(self) -> CrossEncoder:
        if self._model is None:
            raise RuntimeError("Reranker model not loaded.")
        return self._model

    def rerank(
        self, query: str, documents: list[str]
    ) -> list[tuple[int, float]]:
        if not documents:
            return []
        pairs = [(query, doc) for doc in documents]
        scores = self._get_model().predict(pairs)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [(idx, float(score)) for idx, score in ranked]


rerank_service = RerankService()
