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
    build_multilingual_system_prompt,
    build_multilingual_rag_prompt,
)
import backend.app.rag.vector_store as vs_module
from backend.app.schemas.chat import SourceCitation
from backend.app.services.llm_provider import llm_provider_service
from backend.app.services.language_detector import language_detector, LanguageDetector
from backend.app.services.language_service import language_service

SearchResult = vs_module.SearchResult
logger = logging.getLogger(__name__)


class RAGPipeline:
    """Executes semantic search, context building, and grounded LLM generation with multilingual support."""

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
        client, _, _ = llm_provider_service.get_client()
        return client

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
        similarity_threshold: Optional[float] = None,
        previous_language: Optional[str] = None
    ) -> Tuple[str, List[SourceCitation], bool]:
        """
        Execute full RAG flow:
        1. Multilingual language detection (Tamil, Tanglish, English) with context continuity
        2. Semantic retrieval of top matching document chunks
        3. Format source citations
        4. Build injection-defended grounded prompt with language instruction
        5. Generate answer via active LLM Provider or graceful grounded fallback
        Returns (answer_text, citations, is_grounded).
        """
        # Step 1: Detect user query language
        lang = language_detector.detect_language(question, context_language=previous_language)
        self.last_detected_language = lang

        # Step 2: Semantic search
        results = self.search_context(
            question=question,
            user_id=user_id,
            document_ids=document_ids,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )

        import re
        q_clean = (question or "").strip().lower()

        # Meta-queries (asking about document title, author, topics, or document identity)
        is_title_query = bool(re.search(
            r"\b(title|titles|topic|topics|document name|heading|what is this document|who is the author|author)\b",
            q_clean
        ))

        if is_title_query:
            try:
                has_chunk_0 = any(r.chunk_index == 0 for r in results)
                if not has_chunk_0:
                    raw_c0 = self.retriever.vector_store.collection.get(
                        where={"user_id": int(user_id)},
                        include=["documents", "metadatas"]
                    )
                    for d_text, meta in zip(raw_c0.get("documents", []), raw_c0.get("metadatas", [])):
                        if meta.get("chunk_index") == 0:
                            doc_id = str(meta.get("document_id", ""))
                            if not document_ids or doc_id in document_ids:
                                results.insert(0, SearchResult(
                                    chunk_id=str(meta.get("document_id", "")) + "_c0",
                                    document_id=doc_id,
                                    user_id=int(user_id),
                                    filename=str(meta.get("filename", "")),
                                    file_type=str(meta.get("file_type", "pdf")),
                                    page_number=meta.get("page_number"),
                                    chunk_index=0,
                                    text=d_text,
                                    score=0.99,
                                    metadata=meta
                                ))
                                break
            except Exception as e:
                logger.debug(f"Title query chunk 0 lookup skipped: {e}")

        # Overview / Synthesis query fallback:
        is_synthesis_query = bool(re.search(
            r"\b(conclusion|conclusions|summarize|summary|overview|findings|objectives|takeaway|takeaways|main points|core idea)\b",
            q_clean
        )) or ("சுருக்க" in q_clean or "முக்கிய குறிப்புகள்" in q_clean or "முக்கிய நோக்கம்" in q_clean)

        if not results and is_synthesis_query:
            results = self.search_context(
                question=question,
                user_id=user_id,
                document_ids=document_ids,
                top_k=top_k,
                similarity_threshold=0.15
            )

        # Scoped document direct fallback ONLY if user explicitly requested a summary of a single scoped document
        if not results and document_ids and len(document_ids) == 1 and is_synthesis_query:
            try:
                doc_filter = {
                    "$and": [
                        {"user_id": {"$eq": int(user_id)}},
                        {"document_id": {"$eq": str(document_ids[0])}}
                    ]
                }
                scoped_res = self.retriever.vector_store.collection.get(
                    where=doc_filter,
                    limit=top_k or 4,
                    include=["documents", "metadatas"]
                )
                docs = scoped_res.get("documents", [])
                is_url_doc = docs and all(re.match(r"^https?://\S+$", d.strip()) for d in docs)
                if not is_url_doc:
                    for d_text, meta in zip(docs, scoped_res.get("metadatas", [])):
                        results.append(SearchResult(
                            chunk_id=str(meta.get("document_id", "")) + f"_c{meta.get('chunk_index', 0)}",
                            document_id=str(meta.get("document_id", "")),
                            user_id=int(user_id),
                            filename=str(meta.get("filename", "")),
                            file_type=str(meta.get("file_type", "pdf")),
                            page_number=meta.get("page_number"),
                            chunk_index=meta.get("chunk_index", 0),
                            text=d_text,
                            score=0.85,
                            metadata=meta
                        ))
            except Exception as e:
                logger.debug(f"Scoped document fallback skipped: {e}")

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

        # Step 3: Check for insufficient evidence
        if not results:
            hint = ""
            try:
                where_filter: dict = {"user_id": int(user_id)}
                if document_ids and len(document_ids) == 1:
                    where_filter = {
                        "$and": [
                            {"user_id": {"$eq": int(user_id)}},
                            {"document_id": {"$eq": str(document_ids[0])}}
                        ]
                    }
                user_chunks = self.retriever.vector_store.collection.get(
                    where=where_filter,
                    limit=50,
                    include=["documents"]
                )
                docs = user_chunks.get("documents", [])
                if docs and any(re.match(r"^https?://\S+$", d.strip()) for d in docs):
                    hint = " Note: One or more of your uploaded files appears to contain only a web link. The AI Knowledge Assistant indexes document text directly and does not browse external websites. Please paste the actual story or document text into a file before uploading."
            except Exception:
                pass

            insufficient_msg = language_service.get_insufficient_evidence_message(lang)
            fallback_msg = f"{insufficient_msg} No relevant document sections were found matching your query.{hint}"
            return fallback_msg, [], False

        # Step 4: Build grounded prompt with language instruction
        prompt = build_rag_prompt(question=question, context_chunks=results)
        full_system_prompt = build_multilingual_system_prompt(lang)

        messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": prompt}
        ]

        # Formatted excerpts for direct fallback
        formatted_sources = "\n\n".join(
            f"- **{c.filename}** (Page {c.page_number or 'N/A'}):\n  \"{c.excerpt}\""
            for c in citations[:3]
        )

        # Step 5: Test Client override (unit testing mocks)
        if self._custom_client:
            try:
                response = self._custom_client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=messages,
                    temperature=settings.OPENAI_TEMPERATURE,
                    max_tokens=settings.OPENAI_MAX_TOKENS,
                    timeout=30.0
                )
                answer = response.choices[0].message.content or ""
                return answer.strip(), citations, True
            except RateLimitError as e:
                logger.warning(f"Mock RateLimitError: {e}")
                header = language_service.get_fallback_header(lang, "quota_exceeded")
                return f"{header}\n\n{formatted_sources}", citations, True
            except Exception as e:
                logger.error(f"Mock completion error: {e}")
                header = language_service.get_fallback_header(lang, "api_error")
                return f"{header}\n\n{formatted_sources}", citations, True

        # Step 6: Execute generation via LLMProviderService
        answer, error_code, error_detail = llm_provider_service.generate_completion(
            messages=messages,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS
        )

        if answer:
            return answer.strip(), citations, True

        # Step 7: Graceful grounded fallback in user's detected language
        header = language_service.get_fallback_header(lang, error_code or "quota_exceeded")
        fallback_answer = f"{header}\n\n{formatted_sources}"
        return fallback_answer, citations, True

    def answer_question_multilingual(
        self,
        question: str,
        user_id: int,
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        previous_language: Optional[str] = None
    ) -> Tuple[str, List[SourceCitation], bool, str]:
        """Convenience method returning explicit 4-tuple (answer, citations, is_grounded, detected_language)."""
        answer, citations, is_grounded = self.answer_question(
            question=question,
            user_id=user_id,
            document_ids=document_ids,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            previous_language=previous_language
        )
        detected_lang = getattr(self, "last_detected_language", "en")
        return answer, citations, is_grounded, detected_lang

    def answer_general_question(
        self,
        question: str,
        previous_language: Optional[str] = None
    ) -> Tuple[str, str]:
        """Direct general AI conversation without document grounding."""
        lang = language_detector.detect_language(question, context_language=previous_language)
        self.last_detected_language = lang
        full_system_prompt = (
            "You are a friendly, intelligent AI Knowledge Assistant.\n"
            "Explain concepts accurately, clearly, and thoughtfully.\n"
            + language_detector.get_system_instruction(lang)
        )
        messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": question}
        ]
        answer, error_code, _ = llm_provider_service.generate_completion(messages=messages)
        if answer:
            return answer.strip(), lang
        fallback = language_detector.get_fallback_header(lang, error_code or "api_error")
        return fallback, lang


rag_pipeline = RAGPipeline()

__all__ = [
    "RAGPipeline",
    "rag_pipeline",
    "SearchResult",
    "SYSTEM_PROMPT",
    "USER_PROMPT_TEMPLATE",
]
