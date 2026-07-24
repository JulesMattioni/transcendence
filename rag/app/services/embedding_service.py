from sentence_transformers import SentenceTransformer
from shared.base_service import BaseService

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


class EmbeddingService(BaseService):
    """
    Turns text into normalized embedding vectors for similarity search.

    The sentence-transformer model is heavy to load, so it is loaded once
    at startup and reused. A single instance is shared process-wide (see
    embedding_service below).
    """

    def __init__(self) -> None:
        """
        Initialize the service without loading the model yet.
        """

        super().__init__()
        self._model: SentenceTransformer | None = None

    def load(self) -> None:
        """
        Load the sentence-transformer model, once.

        Called at application startup; subsequent calls are no-ops so the
        model is never reloaded.
        """

        if self._model is None:
            self._model = SentenceTransformer(MODEL_NAME)

    def _get_model(self) -> SentenceTransformer:
        """
        Return the loaded model or fail fast if load() was skipped.

        Returns:
            The loaded SentenceTransformer.

        Raises:
            RuntimeError: If the model has not been loaded yet.
        """

        if self._model is None:
            raise RuntimeError("Embeddings model not loaded.")
        return self._model

    def embed_text(self, text: str) -> list[float]:
        """
        Embed a single text into one normalized vector.

        Args:
            text: Text to embed.

        Returns:
            The text's embedding as a list of floats.
        """

        vector = self._get_model().encode(text, normalize_embeddings=True)
        return vector.tolist()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of texts into normalized vectors.

        Args:
            texts: Texts to embed.

        Returns:
            One embedding per input text, in the same order.
        """

        vectors = self._get_model().encode(texts, normalize_embeddings=True)
        return vectors.tolist()


embedding_service = EmbeddingService()
