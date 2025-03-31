
class DebugResult:
    """
    Klasa przechowująca wyniki debugowania.
    """

    def __init__(self,
                 input_text: str,
                 nlp_tree: Dict[str, Any] = None,
                 dsl_representation: str = "",
                 execution_trace: List[Dict[str, Any]] = None):
        """
        Inicjalizacja wyniku debugowania.

        Args:
            input_text: Oryginalny tekst wejściowy
            nlp_tree: Drzewo parsowania NLP
            dsl_representation: Reprezentacja w DSL
            execution_trace: Ślad wykonania
        """
        self.input_text = input_text
        self.nlp_tree = nlp_tree or {}
        self.dsl_representation = dsl_representation
        self.execution_trace = execution_trace or []

    def visualize(self) -> None:
        """
        Wizualizuje proces debugowania.
        """
        print("=== Debug Visualization ===")
        print(f"Input: {self.input_text}")

        print("\n=== NLP Tree ===")
        self._print_dict(self.nlp_tree)

        print("\n=== DSL Representation ===")
        print(self.dsl_representation)

        print("\n=== Execution Trace ===")
        for i, step in enumerate(self.execution_trace):
            print(f"Step {i + 1}:")
            self._print_dict(step)

    def _print_dict(self, d: Dict[str, Any], indent: int = 2) -> None:
        """
        Pomocnicza metoda do wyświetlania słownika.

        Args:
            d: Słownik do wyświetlenia
            indent: Wcięcie
        """
        for key, value in d.items():
            if isinstance(value, dict):
                print(" " * indent + f"{key}:")
                self._print_dict(value, indent + 2)
            elif isinstance(value, list):
                print(" " * indent + f"{key}:")
                for item in value:
                    if isinstance(item, dict):
                        self._print_dict(item, indent + 2)
                    else:
                        print(" " * (indent + 2) + f"{item}")
            else:
                print(" " * indent + f"{key}: {value}")

