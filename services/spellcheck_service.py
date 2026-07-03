# ============================================================================
# Spell Check Service
# thin wrapper around pyspellchecker, plus a per-session custom dictionary
# ============================================================================

from spellchecker import SpellChecker


class SpellCheckService:
    """
    Wraps pyspellchecker's dictionary lookups and adds a lightweight
    in-memory "add to dictionary" list so users can permanently allow
    custom words (names, jargon, etc.) for the current session.

    One instance is shared across all open tabs (created once in
    MainWindow) since loading the dictionary has a small upfront cost
    and the word list itself is read-only per lookup.
    """

    def __init__(self, language: str = "en"):
        self._checker = SpellChecker(language=language)
        self._custom_words: set[str] = set()

    def is_correct(self, word: str) -> bool:
        """Return True if word is spelled correctly (or user-added)."""
        lower = word.lower()
        if lower in self._custom_words:
            return True
        return len(self._checker.unknown([lower])) == 0

    def suggestions(self, word: str, limit: int = 5) -> list[str]:
        """Return up to `limit` candidate corrections, best guess first."""
        candidates = self._checker.candidates(word.lower())
        if not candidates:
            return []
        # pyspellchecker returns an unordered set; rank by edit distance
        # proxy (its own correction() call gives the single best guess,
        # so surface that first if it's in the candidate set).
        best = self._checker.correction(word.lower())
        ordered = sorted(candidates, key=lambda w: (w != best, w))
        return ordered[:limit]

    def add_word(self, word: str):
        """Permanently allow `word` for the rest of this session."""
        self._custom_words.add(word.lower())
