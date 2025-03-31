
class AbstractTranslator(ABC):
    """
    Abstrakcyjna klasa bazowa dla translatorów DSL.
    """

    @abstractmethod
    def translate(self, parsed_data: Dict[str, Any]) -> str:
        """
        Tłumaczy sparsowane dane na format DSL.

        Args:
            parsed_data: Dane po parsowaniu

        Returns:
            Reprezentacja w DSL
        """
        pass
