from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
from typing import List


# Module-level singleton to cache the model
_embeddings_instance = None


def get_embeddings():
    """Get the singleton embeddings instance."""
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = LocalHuggingFaceEmbeddings()
    return _embeddings_instance


class LocalHuggingFaceEmbeddings(Embeddings):
    """LangChain-compatible embeddings wrapper for sentence-transformers."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize the sentence-transformers model.

        Args:
            model_name: The HuggingFace model name to load.
        """
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embeddings, one per text.
        """
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query.

        Args:
            text: The query text to embed.

        Returns:
            The embedding as a list of floats.
        """
        embedding = self.model.encode([text])
        return embedding[0].tolist()
