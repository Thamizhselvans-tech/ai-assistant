"""Multilingual Detection & Response Engine for Tamil, Tanglish, and English."""

from backend.app.services.language_detector import LanguageDetector, language_detector


class LanguageService(LanguageDetector):
    """
    Subclasses LanguageDetector to provide full backward compatibility with any
    services or tests referencing LanguageService or language_service.
    """
    pass


language_service = LanguageService()

__all__ = ["LanguageService", "language_service", "LanguageDetector", "language_detector"]
