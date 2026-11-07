"""Multilingual Detection & Response Engine for Tamil, Tanglish, and English."""

import re
from typing import Dict, List, Optional


class LanguageService:
    """
    Detects language (Tamil, Tanglish, English) and prepares language-aligned
    system instructions and fallback messages for low-resource environments.
    """

    TAMIL_UNICODE_PATTERN = re.compile(r"[\u0B80-\u0BD7]")

    # Common Tanglish phonetic vocabulary and suffixes (Tamil written using Latin characters)
    TANGLISH_KEYWORDS = {
        "enna", "epdi", "eppadi", "sollu", "sollunga", "theriyuma", "theriyum",
        "pannu", "panna", "pannunga", "pannalam", "irukku", "irukken", "irukeenga",
        "nalla", "romba", "ethu", "edhu", "yaaru", "podu", "podunga", "venum",
        "aachu", "aaguthu", "aagum", "pathi", "patthi", "kudunga", "kudu",
        "illa", "illai", "aama", "aamam", "konjam", "thaan", "thambi", "anna",
        "da", "di", "pola", "maathiri", "vanthu", "parunga", "paaru", "kooda",
        "enakku", "unakku", "ungalukku", "avangalukku", "ithu", "adhu", "evvalavu"
    }

    def detect_language(self, text: Optional[str]) -> str:
        """
        Detect language:
        - 'ta': Pure Tamil script
        - 'tanglish': Tamil written in English alphabet
        - 'en': English (default)
        """
        if not text or not text.strip():
            return "en"

        cleaned = text.strip()

        # Check 1: Tamil Unicode script
        if self.TAMIL_UNICODE_PATTERN.search(cleaned):
            return "ta"

        # Check 2: Tanglish heuristic analysis
        # Tokenize Latin words
        words = re.findall(r"\b[a-zA-Z]+\b", cleaned.lower())
        if not words:
            return "en"

        tanglish_matches = sum(1 for w in words if w in self.TANGLISH_KEYWORDS)

        # Check for characteristic Tanglish word endings like -na, -la, -ku, -oda
        tanglish_suffixes = sum(
            1 for w in words
            if len(w) > 4 and (w.endswith("na") or w.endswith("la") or w.endswith("oda") or w.endswith("unga"))
        )

        total_score = tanglish_matches * 2 + tanglish_suffixes
        if total_score >= 2 or (len(words) <= 4 and tanglish_matches >= 1):
            return "tanglish"

        return "en"

    def get_system_instruction(self, lang: str) -> str:
        """Generate language-specific system instruction to steer LLM output."""
        if lang == "ta":
            return (
                "\n\nLANGUAGE INSTRUCTION: The user asked in Tamil. "
                "You MUST answer completely and naturally in Tamil. "
                "Explain concepts clearly in understandable Tamil. "
                "Retain technical terms, code keywords, and proper names (e.g. 'Python', 'FastAPI', 'RAG', 'Machine Learning') in English."
            )
        elif lang == "tanglish":
            return (
                "\n\nLANGUAGE INSTRUCTION: The user asked in Tanglish (Tamil written in English letters). "
                "Understand the meaning accurately and respond in natural Tamil or conversational Tanglish as appropriate. "
                "Explain technical concepts clearly and keep technical terms and programming keywords in English."
            )
        return "\n\nLANGUAGE INSTRUCTION: Answer clearly, accurately, and professionally in English."

    def get_fallback_header(self, lang: str, reason: str = "quota_exceeded") -> str:
        """Generate culturally natural grounded fallback notices in the user's language."""
        if lang == "ta":
            if reason == "quota_exceeded":
                return (
                    "*(குறிப்பு: கிளவுட் AI சேவை வரம்பு முடிந்தது / கிரெடிட் இல்லை. "
                    "உங்கள் ஆவணங்களிலிருந்து நேரடியாகப் பெறப்பட்ட உண்மைத் தகவல்கள் கீழே தரப்பட்டுள்ளன:)*"
                )
            elif reason == "unconfigured":
                return (
                    "*(குறிப்பு: கிளவுட் AI கீ இன்னும் அமைக்கப்படவில்லை. "
                    "உங்கள் ஆவணங்களிலிருந்து நேரடியாகப் பெறப்பட்ட தகவல்கள் கீழே தரப்பட்டுள்ளன:)*"
                )
            else:
                return (
                    "*(குறிப்பு: கிளவுட் AI இணைப்பு கிடைக்கவில்லை. "
                    "உங்கள் ஆவணங்களிலிருந்து நேரடியாகப் பெறப்பட்ட தகவல்கள் கீழே தரப்பட்டுள்ளன:)*"
                )

        elif lang == "tanglish":
            if reason == "quota_exceeded":
                return (
                    "*(Note: Cloud AI quota mudinjuruchu or credits illa. "
                    "Unga uploaded documents-la irunthu verify panna direct information keezhe kuduthurukom:)*"
                )
            elif reason == "unconfigured":
                return (
                    "*(Note: Cloud AI key set pannala. "
                    "Unga uploaded documents-la irunthu direct information keezhe kuduthurukom:)*"
                )
            else:
                return (
                    "*(Note: Cloud AI connection illa. "
                    "Unga uploaded documents-la irunthu direct excerpts keezhe kuduthurukom:)*"
                )

        else:  # English
            if reason == "quota_exceeded":
                return (
                    "*(Note: Cloud AI quota or rate limit reached. "
                    "Displaying verified grounded excerpts retrieved directly from your indexed documents:)*"
                )
            elif reason == "unconfigured":
                return (
                    "*(Note: Cloud AI is in unconfigured mode because no API key is set. "
                    "Displaying verified grounded excerpts retrieved directly from your indexed documents:)*"
                )
            else:
                return (
                    "*(Note: Cloud AI service is currently unavailable. "
                    "Displaying verified grounded excerpts retrieved directly from your indexed documents:)*"
                )

    def get_insufficient_evidence_message(self, lang: str) -> str:
        """Localized insufficient evidence response."""
        if lang == "ta":
            return "பதிவேற்றப்பட்ட ஆவணங்களில் இந்த கேள்விக்கான தகவல் கிடைக்கவில்லை."
        elif lang == "tanglish":
            return "Upload panna documents-la indha question-ku answer kedaikala."
        return "I cannot find the answer to this question in the uploaded documents."


language_service = LanguageService()
