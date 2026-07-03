# ============================================================================
# Spell Check Highlighter
# underlines misspelled words with a red squiggly, live as you type
# ============================================================================
#
# Qt only re-runs highlightBlock() on the block(s) that actually changed
# (not the whole document), so this stays cheap even in large documents.

import re
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor

from services.spellcheck_service import SpellCheckService

_WORD_RE = re.compile(r"[A-Za-z']+")


class SpellCheckHighlighter(QSyntaxHighlighter):
    """Attach to a QTextDocument to underline misspelled words live."""

    def __init__(self, document, spell_service: SpellCheckService):
        super().__init__(document)
        self._spell = spell_service

        self._format = QTextCharFormat()
        self._format.setUnderlineStyle(
            QTextCharFormat.UnderlineStyle.SpellCheckUnderline
        )
        self._format.setUnderlineColor(QColor("#e74c3c"))

        self.enabled = True

    def highlightBlock(self, text: str):
        if not self.enabled:
            return
        for match in _WORD_RE.finditer(text):
            word = match.group()
            if len(word) < 2:
                continue
            if not self._spell.is_correct(word):
                self.setFormat(match.start(), len(word), self._format)

    def set_enabled(self, enabled: bool):
        """Toggle spell checking on/off and force a re-highlight."""
        self.enabled = enabled
        self.rehighlight()
