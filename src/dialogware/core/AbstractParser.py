
class AbstractParser(ABC):
    """
    Abstrakcyjna klasa bazowa dla parserów języka naturalnego.
    """

    @abstractmethod
    def parse(self, input_text: str) -> Dict[str, Any]:
        """
        Parsuje tekst w języku naturalnym na strukturę danych.

        Args:
            input_text: Tekst wejściowy w języku naturalnym

        Returns:
            Strukturę danych reprezentującą parsed command
        """
        pass

