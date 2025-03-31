# src/dialogware/debuggers/nlp_debugger.py
"""
Debuger dla warstwy NLP.
"""


class NLPDebugger:
    """
    Narzędzie do debugowania parsowania języka naturalnego.
    """

    def __init__(self):
        self.parsers = {}

    def register_parser(self, domain: str, parser: Any) -> None:
        """
        Rejestruje parser dla danej domeny.

        Args:
            domain: Domena
            parser: Parser
        """
        self.parsers[domain] = parser

    def parse(self, text: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Parsuje tekst w celu debugowania.

        Args:
            text: Tekst do parsowania
            domain: Opcjonalna domena

        Returns:
            Drzewo parsowania
        """
        if domain is None:
            # TODO: Implementacja automatycznego wykrywania domeny
            domain = "default"

        if domain not in self.parsers:
            raise ValueError(f"Parser for domain '{domain}' not registered")

        parser = self.parsers[domain]
        result = parser.parse(text)

        return result

    def analyze_confidence(self, text: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Analizuje pewność rozpoznania elementów.

        Args:
            text: Tekst do analizy
            domain: Opcjonalna domena

        Returns:
            Mapa pewności rozpoznania
        """
        # TODO: Implementacja analizy pewności
        return {
            "overall_confidence": 0.8,
            "entities": [
                # Tu będą rzeczywiste dane z analizy
            ]
        }

    def visualize(self, parse_tree: Dict[str, Any]) -> None:
        """
        Wizualizuje drzewo parsowania.

        Args:
            parse_tree: Drzewo parsowania
        """
        # Implementacja wizualizacji
        print("=== NLP Parse Tree Visualization ===")
        self._print_tree(parse_tree)

    def _print_tree(self, node: Dict[str, Any], level: int = 0) -> None:
        """
        Rekurencyjnie wyświetla drzewo.

        Args:
            node: Węzeł drzewa
            level: Poziom zagnieżdżenia
        """
        indent = "  " * level

        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    print(f"{indent}{key}:")
                    self._print_tree(value, level + 1)
                else:
                    print(f"{indent}{key}: {value}")
        elif isinstance(node, list):
            for item in node:
                self._print_tree(item, level)
        else:
            print(f"{indent}{node}")
