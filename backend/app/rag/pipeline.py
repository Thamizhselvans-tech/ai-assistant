"""End-to-End RAG Pipeline: Vector Search -> Grounded Prompt -> LLM Generation -> Citations."""

import logging
from typing import List, Optional, Tuple
from openai import OpenAI, APIError, APIConnectionError, RateLimitError

from backend.app.core.config import settings
from backend.app.rag.retriever import semantic_retriever, SemanticRetriever
from backend.app.rag.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    INSUFFICIENT_EVIDENCE_ANSWER,
    format_context,
    build_rag_prompt,
)
import backend.app.rag.vector_store as vs_module
from backend.app.schemas.chat import SourceCitation

SearchResult = vs_module.SearchResult
logger = logging.getLogger(__name__)


class RAGPipeline:
    """Executes semantic search, context building, and grounded LLM generation."""

    def __init__(
        self,
        openai_client: Optional[OpenAI] = None,
        retriever_instance: Optional[SemanticRetriever] = None
    ):
        self._custom_client = openai_client
        self._custom_retriever = retriever_instance

    @property
    def retriever(self) -> SemanticRetriever:
        return self._custom_retriever or semantic_retriever

    def _get_openai_client(self) -> Optional[OpenAI]:
        if self._custom_client:
            return self._custom_client
        api_key = settings.OPENAI_API_KEY.strip()
        if not api_key or api_key == "your-openai-api-key-here":
            return None
        return OpenAI(
            api_key=api_key,
            base_url=settings.OPENAI_BASE_URL
        )

    def search_context(
        self,
        question: str,
        user_id: int,
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[SearchResult]:
        """Generate query vector and retrieve top relevant chunks from ChromaDB via SemanticRetriever."""
        k = top_k or settings.TOP_K_RETRIEVAL
        threshold = similarity_threshold if similarity_threshold is not None else settings.SIMILARITY_THRESHOLD
        return self.retriever.retrieve(
            question=question,
            user_id=user_id,
            document_ids=document_ids,
            top_k=k,
            similarity_threshold=threshold
        )

    def build_context_text(self, results: List[SearchResult]) -> str:
        """Format retrieved search results safely into structured context."""
        return format_context(results)

    def answer_question(
        self,
        question: str,
        user_id: int,
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> Tuple[str, List[SourceCitation], bool]:
        """
        Execute full RAG flow:
        1. Semantic retrieval of top matching document chunks
        2. Format source citations
        3. Build injection-defended grounded prompt
        4. Generate answer via OpenAI or graceful fallback
        Returns (answer_text, citations, is_grounded).
        """
        # Step 1: Semantic search
        results = self.search_context(
            question=question,
            user_id=user_id,
            document_ids=document_ids,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )

        # Convert results to citations
        citations: List[SourceCitation] = [
            SourceCitation(
                document_id=r.document_id,
                filename=r.filename,
                page_number=r.page_number,
                chunk_index=r.chunk_index,
                excerpt=r.text[:300] + ("..." if len(r.text) > 300 else ""),
                score=r.score
            )
            for r in results
        ]

        # Step 2: Check for insufficient evidence
        if not results:
            hint = ""
            try:
                import re
                user_chunks = self.retriever.vector_store.collection.get(
                    where={"user_id": int(user_id)},
                    limit=5,
                    include=["documents"]
                )
                docs = user_chunks.get("documents", [])
                if docs and any(re.match(r"^https?://[^\s]+$", d.strip()) for d in docs):
                    hint = " Note: One or more of your uploaded files appears to contain only a web link. The AI Knowledge Assistant indexes document text directly and does not browse external websites. Please paste the actual story or document text into a file before uploading."
            except Exception:
                pass

            fallback_msg = (
                f"{INSUFFICIENT_EVIDENCE_ANSWER} "
                f"No relevant document sections were found matching your query.{hint}"
            )
            return fallback_msg, [], False

        client = self._get_openai_client()

        # Step 3: Handle case when OpenAI key is missing or unconfigured
        if client is None:
            formatted_sources = "\n\n".join(
                f"- **{c.filename}** (Page {c.page_number or 'N/A'}):\n  \"{c.excerpt}\""
                for c in citations[:3]
            )
            info_msg = (
                "*(Note: LLM generation is running in unconfigured mode because `OPENAI_API_KEY` is not set. "
                "Configure your OpenAI API key in `.env` or Settings to enable full generative responses.)*\n\n"
                f"**Most relevant excerpts found in your documents:**\n\n{formatted_sources}"
            )
            return info_msg, citations, True

        # Step 4: Build prompt and execute OpenAI generation
        prompt = build_rag_prompt(question=question, context_chunks=results)

        try:
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                timeout=30.0
            )
            answer = response.choices[0].message.content or ""
            return answer.strip(), citations, True

        except RateLimitError:
            logger.error("OpenAI Rate limit exceeded")
            return "The AI service rate limit was exceeded. Please wait a moment and try again.", citations, False
        except APIConnectionError:
            logger.error("Failed to connect to OpenAI API")
            return "Unable to connect to the AI service. Please check your internet connection or API base URL.", citations, False
        except APIError as e:
            logger.error(f"OpenAI API Error: {str(e)}")
            return f"An error occurred while communicating with the AI service: {str(e)}", citations, False
        except Exception as e:
            logger.error(f"Unexpected generation error: {str(e)}")
            return f"An unexpected error occurred during answer generation: {str(e)}", citations, False


rag_pipeline = RAGPipeline()

__all__ = [
    "RAGPipeline",
    "rag_pipeline",
    "SearchResult",
    "SYSTEM_PROMPT",
    "USER_PROMPT_TEMPLATE",
]
