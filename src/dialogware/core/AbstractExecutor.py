

class AbstractExecutor(ABC):
    """
    Abstrakcyjna klasa bazowa dla wykonawców komend.
    """

    @abstractmethod
    def execute(self, command: str) -> Any:
        """
        Wykonuje przetłumaczoną komendę.

        Args:
            command: Komenda do wykonania w formacie DSL

        Returns:
            Rezultat wykonania komendy
        """
        pass

