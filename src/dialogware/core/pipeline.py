"""
pipeline.py
"""


class Pipeline:
    """
    Pipeline do łańcuchowania operacji.
    """

    def __init__(self, name: str = "default"):
        self.name = name
        self.elements: List[PipelineElement] = []
        self.debug_mode = False
        self.execution_trace = []

    def add(self, element: PipelineElement) -> 'Pipeline':
        """
        Dodaje element do pipeline'u.

        Args:
            element: Element pipeline'u do dodania

        Returns:
            self dla umożliwienia łańcuchowania
        """
        self.elements.append(element)
        return self

    def execute(self, input_data: Any) -> Any:
        """
        Wykonuje pipeline na danych wejściowych.

        Args:
            input_data: Dane wejściowe do przetworzenia

        Returns:
            Rezultat przetwarzania
        """
        result = input_data
        self.execution_trace.clear()

        for element in self.elements:
            if self.debug_mode:
                try:
                    result = element(result)
                    self.execution_trace.append({
                        "element": element.name,
                        "input": input_data,
                        "output": result,
                        "status": "success"
                    })
                except Exception as e:
                    self.execution_trace.append({
                        "element": element.name,
                        "input": input_data,
                        "error": str(e),
                        "status": "error"
                    })
                    raise
            else:
                result = element(result)

        return result

    def enable_debug(self, enabled: bool = True) -> 'Pipeline':
        """
        Włącza lub wyłącza tryb debugowania.

        Args:
            enabled: Czy włączyć debugowanie

        Returns:
            self dla umożliwienia łańcuchowania
        """
        self.debug_mode = enabled
        return self

    def __call__(self, input_data: Any) -> Any:
        """
        Wykonuje pipeline na danych wejściowych.

        Args:
            input_data: Dane wejściowe do przetworzenia

        Returns:
            Rezultat przetwarzania
        """
        return self.execute(input_data)
