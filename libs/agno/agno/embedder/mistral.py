from os import getenv
from typing import Any, Dict, List, Optional, Tuple

from agno.embedder.base import Embedder
from agno.utils.log import logger

try:
    from mistralai import Mistral
    from mistralai.models.embeddingresponse import EmbeddingResponse
except ImportError:
    raise ImportError("`mistralai` not installed")


class MistralEmbedder(Embedder):
    model: str = "mistral-embed"
    dimensions: int = 1024
    # -*- Request parameters
    request_params: Optional[Dict[str, Any]] = None
    # -*- Client parameters
    api_key: Optional[str] = getenv("MISTRAL_API_KEY")
    endpoint: Optional[str] = None
    max_retries: Optional[int] = None
    timeout: Optional[int] = None
    client_params: Optional[Dict[str, Any]] = None
    # -*- Provide the Mistral Client manually
    mistral_client: Optional[Mistral] = None

    @property
    def client(self) -> Mistral:
        if self.mistral_client:
            return self.mistral_client

        _client_params: Dict[str, Any] = {}
        if self.api_key:
            _client_params["api_key"] = self.api_key
        if self.endpoint:
            _client_params["endpoint"] = self.endpoint
        if self.max_retries:
            _client_params["max_retries"] = self.max_retries
        if self.timeout:
            _client_params["timeout"] = self.timeout
        if self.client_params:
            _client_params.update(self.client_params)
        return Mistral(**_client_params)

    def _response(self, text: str) -> EmbeddingResponse:
        _request_params: Dict[str, Any] = {
            "inputs": text,
            "model": self.model,
        }
        if self.request_params:
            _request_params.update(self.request_params)
        response = self.client.embeddings.create(**_request_params)
        if response is None:
            raise ValueError("Failed to get embedding response")
        return response

    def get_embedding(self, text: str) -> List[float]:
        try:
            response: EmbeddingResponse = self._response(text=text)
            if response.data and response.data[0].embedding:
                return response.data[0].embedding
            return []
        except Exception as e:
            logger.warning(f"Error getting embedding: {e}")
            return []

    def get_embedding_and_usage(self, text: str) -> Tuple[List[float], Dict[str, Any]]:
        try:
            response: EmbeddingResponse = self._response(text=text)
            embedding: List[float] = (
                response.data[0].embedding if (response.data and response.data[0].embedding) else []
            )
            usage: Dict[str, Any] = response.usage.model_dump() if response.usage else {}
            return embedding, usage
        except Exception as e:
            logger.warning(f"Error getting embedding and usage: {e}")
            return [], {}
