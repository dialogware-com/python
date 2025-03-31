

# src/dialogware/debuggers/dsl_debugger.py
"""
Debuger dla warstwy DSL.
"""

from DSLAnalysisResult import DSLAnalysisResult

class DSLDebugger:
    """
    Narzędzie do debugowania reprezentacji DSL.
    """

    def __init__(self):
        self.translators = {}

    def register_translator(self, domain: str, translator: Any) -> None:
        """
        Rejestruje translator dla danej domeny.

        Args:
            domain: Domena
            translator: Translator
        """
        self.translators[domain] = translator

    def analyze(self, dsl_code: str) -> 'DSLAnalysisResult':
        """
        Analizuje kod DSL.

        Args:
            dsl_code: Kod DSL do analizy

        Returns:
            Wynik analizy
        """
        return DSLAnalysisResult(dsl_code)

