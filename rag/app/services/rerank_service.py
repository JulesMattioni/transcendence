from sentence_transformers import CrossEncoder
from shared.base_service import BaseService
from app.config import RERANK_MODEL_NAME


class RerankService(BaseService):
    """
    Re-scores retrieved chunks by relevance with a cross-encoder.

    Bi-encoder retrieval is fast but coarse; a cross-encoder reads the
    query and each document together to give a sharper relevance score,
    used to keep only the best candidates. The model is loaded once at
    startup and shared process-wide (see rerank_service below).
    """

    def __init__(self) -> None:
        """
        Initialize the service without loading the model yet.
        """

        super().__init__()
        self._model: CrossEncoder | None = None

    def load(self) -> None:
        """
        Load the cross-encoder model, once.

        Called at application startup; subsequent calls are no-ops so the
        model is never reloaded.
        """

        if self._model is None:
            self._model = CrossEncoder(RERANK_MODEL_NAME)

    def _get_model(self) -> CrossEncoder:
        """
        Return the loaded model or fail fast if load() was skipped.

        Returns:
            The loaded CrossEncoder.

        Raises:
            RuntimeError: If the model has not been loaded yet.
        """

        if self._model is None:
            raise RuntimeError("Reranker model not loaded.")
        return self._model

    def rerank(
        self, query: str, documents: list[str]
    ) -> list[tuple[int, float]]:
        """
        Score documents against a query and rank them, best first.

        Args:
            query: Query the documents are scored against.
            documents: Candidate document texts to score.

        Returns:
            (original_index, score) pairs sorted by descending score;
            empty when documents is empty.
        """

        if not documents:
            return []
        pairs = [(query, doc) for doc in documents]
        scores = self._get_model().predict(pairs)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [(idx, float(score)) for idx, score in ranked]


rerank_service = RerankService()
