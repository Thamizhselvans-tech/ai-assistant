"""Comprehensive Multilingual Language Detection and Localization Engine.

Supports:
- Tamil Script ('ta'): Pure Tamil unicode characters and mixed Tamil-English technical sentences.
- Tanglish ('tanglish'): Tamil written phonetically using the Latin/English alphabet with phonetic vocabulary,
  suffixes, n-grams, and grammatical markers.
- English ('en'): Standard English technical and conversational queries.

Includes explicit language change detection, context-aware follow-up resolution,
and culturally grounded fallback notices for 4GB low-RAM environments.
"""

import re
from typing import Dict, List, Optional, Tuple, Set


class LanguageDetector:
    """
    Lightweight, deterministic language detector and prompt localization engine.
    Does NOT call external LLMs for detection, keeping memory low and latency sub-millisecond.
    """

    LANG_TAMIL = "ta"
    LANG_TANGLISH = "tanglish"
    LANG_ENGLISH = "en"

    SUPPORTED_LANGUAGES = [LANG_TAMIL, LANG_TANGLISH, LANG_ENGLISH]

    # Tamil Unicode block: U+0B80 to U+0BD7
    TAMIL_UNICODE_PATTERN = re.compile(r"[\u0B80-\u0BD7]")

    # Explicit language switch expressions
    EXPLICIT_ENGLISH_PATTERNS = [
        r"\b(?:now\s+)?(?:explain\s+)?in\s+english\b",
        r"\b(?:tell\s+|speak\s+|respond\s+|reply\s+)?in\s+english\b",
        r"\bswitch\s+to\s+english\b",
        r"\benglish(?:-la|\s+la|\s+il|\s+please)?\b",
        r"\bcan\s+you\s+(?:explain|answer)\s+in\s+english\b",
    ]

    EXPLICIT_TAMIL_PATTERNS = [
        r"\b(?:now\s+)?(?:explain\s+)?in\s+tamil\b",
        r"\btamil(?:-la|\s+la|\s+il|\s+il\s+sollunga|\s+la\s+sollu|\s+la\s+explain\s+pannu)\b",
        r"\bswitch\s+to\s+tamil\b",
        r"\btamil\s+please\b",
        r"\bதமிழ்\s*(?:மொழியில்|ல்|இல்)?\b",
    ]

    EXPLICIT_TANGLISH_PATTERNS = [
        r"\b(?:now\s+)?(?:explain\s+)?in\s+tanglish\b",
        r"\btanglish(?:-la|\s+la|\s+il|\s+la\s+sollu|\s+la\s+explain\s+pannu)\b",
        r"\bswitch\s+to\s+tanglish\b",
        r"\btanglish\s+please\b",
    ]

    # Comprehensive Tanglish Lexicon (Tamil written using Latin script)
    # 1. Interrogatives / Question Markers
    TANGLISH_INTERROGATIVES = {
        "enna", "yanna", "ennaa", "ennathu", "ennadhu", "ennachu", "ennapa",
        "edhu", "ethu", "edhukku", "ethukku", "edhuku", "ethuku", "edhula",
        "eppadi", "epdi", "eppidi", "eppudi",
        "enga", "engae", "engirukku", "engey",
        "yaaru", "yaar", "yaarukku", "yar",
        "yen", "yean", "ethukaga", "edhukkaaga",
        "eppo", "eppovum", "eppothum", "eppodhu",
        "evvalavu", "evalo", "evlo", "ethanai", "yethana",
    }

    # 2. Common Verbs & Imperatives
    TANGLISH_VERBS = {
        "sollu", "sollunga", "solla", "sollanum", "solren", "solranga", "sonna",
        "kudu", "kudunga", "kodu", "kodunga", "kuduthu", "kudukkum",
        "pannu", "panna", "pannunga", "pannalam", "panniten", "panniyacha", "pannirukku", "pannunga",
        "paru", "paaru", "parunga", "pakanum", "paarkalam", "paatha", "paarthu",
        "vaanga", "vanga", "vaa", "vandhu", "vanthu", "vandha", "vanthathu",
        "ponga", "po", "poitu", "pona", "poiduchu",
        "podu", "podunga", "vachiko", "vei", "veinga",
        "kaatu", "kaatunga", "kaamikkanum",
        "theriyum", "theriyuma", "theriyala", "therila", "theriyathu",
        "puriya", "puriyala", "purinjitha", "purinjithu", "puriyum", "puriyudha",
        "irukku", "irukka", "irukken", "irukkeenga", "irundhathu", "irundhadhu", "irukura",
        "vaasi", "padi", "padikka", "eluthu", "ezhudhu", "eludhanga",
        "kedaikkum", "kedaikala", "kidaikala", "kidaikuma", "kedaikuma",
        "mudiyum", "mudiyathu", "mudiyala", "koodathu", "aagathu",
    }

    # 3. Pronouns & Demonstratives
    TANGLISH_PRONOUNS = {
        "naan", "nan", "naanga", "namma", "namakku",
        "nee", "neenga", "neengala", "unnoda", "ungada",
        "avan", "aval", "avanga", "avargal", "avangalukku",
        "ithu", "idhu", "adhu", "edhu", "indha", "andha", "endha",
        "enakku", "unakku", "ungalukku", "adhukku", "idhukku",
        "ivan", "ival", "idhellam", "adhellam", "adhoda", "idhoda",
    }

    # 4. Particles, Conjunctions & Adverbs
    TANGLISH_PARTICLES = {
        "na", "nu", "thaan", "dhan", "kooda", "kuda",
        "mari", "maathiri", "mathiri", "pola",
        "pathi", "patthi", "patri",
        "aana", "aanal", "apram", "appuram", "adhuvara",
        "aachu", "aaguthu", "aagum", "varum",
        "illa", "illai", "aama", "aamam", "seri", "sari",
        "venum", "vendaam", "vendam", "konjam", "romba", "nalla",
        "matrum", "mattum", "ulla", "ulle", "ku", "ukku", "kaga", "kaaga",
        "la", "le", "oda", "koodave",
        "da", "di", "machi", "bro", "thambi", "anna", "nanba",
    }

    ALL_TANGLISH_KEYWORDS = (
        TANGLISH_INTERROGATIVES
        | TANGLISH_VERBS
        | TANGLISH_PRONOUNS
        | TANGLISH_PARTICLES
    )

    # Tanglish multi-word structural collocations
    TANGLISH_PHRASE_PATTERNS = [
        re.compile(r"\bna\s+enna\b", re.IGNORECASE),             # e.g. "machine learning na enna"
        re.compile(r"\bepdi\s+work\s+aaguthu\b", re.IGNORECASE),  # e.g. "epdi work aaguthu"
        re.compile(r"\bnu\s+sollu\b", re.IGNORECASE),            # e.g. "details nu sollu"
        re.compile(r"\b(?:kudu|kudunga)\b", re.IGNORECASE),      # e.g. "example kudu"
        re.compile(r"\b(?:sollu|sollunga)\b", re.IGNORECASE),    # e.g. "summary sollu"
        re.compile(r"\bromba\s+nalla\b", re.IGNORECASE),         # e.g. "romba nalla"
        re.compile(r"\b(?:pathi|patthi)\s+sollu\b", re.IGNORECASE),
        re.compile(r"\bindha\s+doc\b", re.IGNORECASE),
        re.compile(r"\bulla\s+difference\b", re.IGNORECASE),
    ]

    # Characteristic Tanglish grammatical suffixes
    TANGLISH_SUFFIXES = ("-la", "-na", "-ku", "-ukku", "-oda", "-unga", "-alam", "-aaguthu", "-aachu", "-ah", "-aa")

    def check_explicit_language_switch(self, text: str) -> Optional[str]:
        """Detect explicit user requests to switch the response language."""
        if not text:
            return None

        for pattern in self.EXPLICIT_ENGLISH_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return self.LANG_ENGLISH

        for pattern in self.EXPLICIT_TAMIL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return self.LANG_TAMIL

        for pattern in self.EXPLICIT_TANGLISH_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return self.LANG_TANGLISH

        return None

    def is_tamil_script(self, text: str) -> bool:
        """Return True if text contains any Tamil script character."""
        if not text:
            return False
        return bool(self.TAMIL_UNICODE_PATTERN.search(text))

    def get_confidence_scores(self, text: str) -> Dict[str, float]:
        """Compute relative confidence score across Tamil, Tanglish, and English."""
        if not text or not text.strip():
            return {self.LANG_ENGLISH: 1.0, self.LANG_TAMIL: 0.0, self.LANG_TANGLISH: 0.0}

        cleaned = text.strip()

        # 1. Tamil Script check
        tamil_chars = len(self.TAMIL_UNICODE_PATTERN.findall(cleaned))
        if tamil_chars > 0:
            # Contains Tamil unicode letters -> strong Tamil score
            total_chars = max(len(re.findall(r"\S", cleaned)), 1)
            ratio = tamil_chars / total_chars
            return {
                self.LANG_TAMIL: min(1.0, 0.5 + ratio * 0.5),
                self.LANG_TANGLISH: 0.1,
                self.LANG_ENGLISH: max(0.0, 1.0 - (0.5 + ratio * 0.5))
            }

        # 2. Latin characters tokenization
        tokens = re.findall(r"\b[a-zA-Z0-9_\-']+\b", cleaned.lower())
        if not tokens:
            return {self.LANG_ENGLISH: 1.0, self.LANG_TAMIL: 0.0, self.LANG_TANGLISH: 0.0}

        tanglish_count = 0
        for tok in tokens:
            # Direct keyword match
            bare_tok = tok.replace("-", "").strip()
            if tok in self.ALL_TANGLISH_KEYWORDS or bare_tok in self.ALL_TANGLISH_KEYWORDS:
                tanglish_count += 1
                continue

            # Suffix match (e.g. "doc-la", "learning-na", "work-aaguthu")
            if any(tok.endswith(sfx) for sfx in self.TANGLISH_SUFFIXES if len(tok) > len(sfx) + 2):
                tanglish_count += 1
                continue

        # Phrase pattern matches
        phrase_matches = sum(1 for p in self.TANGLISH_PHRASE_PATTERNS if p.search(cleaned))

        weighted_tanglish_hits = tanglish_count + (phrase_matches * 2)
        total_tokens = len(tokens)

        tanglish_score = min(1.0, weighted_tanglish_hits / max(total_tokens, 1))

        # Boost short distinctive queries or queries with 2+ Tanglish indicators
        if weighted_tanglish_hits >= 2:
            tanglish_score = max(tanglish_score, 0.55)
        elif weighted_tanglish_hits >= 1 and total_tokens <= 5:
            tanglish_score = max(tanglish_score, 0.75)

        english_score = max(0.0, 1.0 - tanglish_score)

        return {
            self.LANG_ENGLISH: english_score,
            self.LANG_TAMIL: 0.0,
            self.LANG_TANGLISH: tanglish_score
        }

    def detect_language(self, text: Optional[str], context_language: Optional[str] = None) -> str:
        """
        Detect language of user message:
        - 'ta': Tamil script (includes mixed Tamil with English technical terms).
        - 'tanglish': Tamil written in English alphabet.
        - 'en': English.

        Handles explicit language changes and short follow-up continuity.
        """
        if not text or not text.strip():
            return context_language if context_language in self.SUPPORTED_LANGUAGES else self.LANG_ENGLISH

        cleaned = text.strip()

        # Step 1: Explicit language switch directive takes highest priority
        explicit_switch = self.check_explicit_language_switch(cleaned)
        if explicit_switch:
            return explicit_switch

        # Step 2: Tamil Unicode script detection
        if self.is_tamil_script(cleaned):
            return self.LANG_TAMIL

        # Step 3: Tanglish analysis
        scores = self.get_confidence_scores(cleaned)
        tanglish_score = scores.get(self.LANG_TANGLISH, 0.0)

        # High confidence Tanglish
        if tanglish_score >= 0.25:
            return self.LANG_TANGLISH

        # Step 4: Short follow-up question continuity handling
        # If user previously spoke Tamil or Tanglish and enters a short follow-up (<= 3 words)
        # without explicit English grammar or switch (e.g. "Example?", "Continue", "More details"),
        # preserve previous language.
        words = re.findall(r"\b[a-zA-Z]+\b", cleaned)
        if len(words) <= 3 and context_language in [self.LANG_TAMIL, self.LANG_TANGLISH]:
            # Check if this short follow-up is an explicit switch (already handled in step 1)
            # If not switching, inherit context language
            return context_language

        # Step 5: Default to English
        return self.LANG_ENGLISH

    def get_system_instruction(self, lang: str) -> str:
        """Generate structured system instruction for the LLM based on detected language."""
        if lang == self.LANG_TAMIL:
            return (
                "\n\n=======================================================\n"
                "LANGUAGE AND LOCALIZATION INSTRUCTION (Tamil - தமிழ்):\n"
                "- The user asked in Tamil. You MUST formulate your entire response in clear, natural, grammatically correct Tamil.\n"
                "- Explain technical concepts simply and clearly in understandable Tamil.\n"
                "- Retain industry-standard technical terms, programming keywords, formulas, and acronyms in English where useful "
                "(e.g., 'Machine Learning', 'Supervised Learning', 'FastAPI', 'Python', 'RAG', 'ChromaDB', 'Vector Store').\n"
                "- When answering from document context, ground all facts strictly in the provided excerpts and cite source filenames "
                "and page numbers accurately without translating filenames (e.g., keep 'Report.pdf', 'Page 1' as-is).\n"
                "=======================================================\n"
            )
        elif lang == self.LANG_TANGLISH:
            return (
                "\n\n=======================================================\n"
                "LANGUAGE AND LOCALIZATION INSTRUCTION (Tanglish / Tamil):\n"
                "- The user asked in Tanglish (Tamil expressed phonetically in English/Latin letters).\n"
                "- Understand the user's intended Tamil meaning accurately.\n"
                "- Formulate your response in natural, fluent Tamil (or friendly conversational Tanglish) that matches the user's style.\n"
                "- Explain technical concepts clearly, retaining English technical terms and programming keywords.\n"
                "- When answering from document context, ground all facts strictly in the provided excerpts and cite source filenames "
                "and page numbers accurately without translating filenames.\n"
                "=======================================================\n"
            )
        return (
            "\n\n=======================================================\n"
            "LANGUAGE AND LOCALIZATION INSTRUCTION (English):\n"
            "- Answer clearly, accurately, and professionally in English.\n"
            "- Ground all facts strictly in the provided document excerpts and cite source filenames and pages accurately.\n"
            "=======================================================\n"
        )

    def get_fallback_header(self, lang: str, reason: str = "quota_exceeded") -> str:
        """Generate culturally natural grounded fallback notices in the user's language."""
        if lang == self.LANG_TAMIL:
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
            elif reason == "auth_error":
                return (
                    "*(குறிப்பு: கிளவுட் AI அங்கீகார பிழை (Invalid API Key). "
                    "உங்கள் ஆவணங்களிலிருந்து பெறப்பட்ட தகவல்கள் கீழே தரப்பட்டுள்ளன:)*"
                )
            else:
                return (
                    "*(குறிப்பு: கிளவுட் AI இணைப்பு கிடைக்கவில்லை. "
                    "உங்கள் ஆவணங்களிலிருந்து நேரடியாகப் பெறப்பட்ட தகவல்கள் கீழே தரப்பட்டுள்ளன:)*"
                )

        elif lang == self.LANG_TANGLISH:
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
            elif reason == "auth_error":
                return (
                    "*(Note: Cloud AI authentication error (Invalid Key). "
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
            elif reason == "auth_error":
                return (
                    "*(Note: Cloud AI authentication failed due to an invalid API key. "
                    "Displaying verified grounded excerpts retrieved directly from your indexed documents:)*"
                )
            else:
                return (
                    "*(Note: Cloud AI service is currently unavailable. "
                    "Displaying verified grounded excerpts retrieved directly from your indexed documents:)*"
                )

    def get_insufficient_evidence_message(self, lang: str) -> str:
        """Localized insufficient evidence response when no document content matches."""
        if lang == self.LANG_TAMIL:
            return "பதிவேற்றப்பட்ட ஆவணங்களில் இந்த கேள்விக்கான தகவல் கிடைக்கவில்லை."
        elif lang == self.LANG_TANGLISH:
            return "Upload panna documents-la indha question-ku answer kedaikala."
        return "I cannot find the answer to this question in the uploaded documents."


language_detector = LanguageDetector()

__all__ = ["LanguageDetector", "language_detector"]
