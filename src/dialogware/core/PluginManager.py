
class PluginManager:
    """
    Zarządca wtyczek dla różnych domen.
    """

    def __init__(self):
        self.parsers: Dict[str, AbstractParser] = {}
        self.translators: Dict[str, AbstractTranslator] = {}
        self.executors: Dict[str, AbstractExecutor] = {}
        self.generators: Dict[str, Any] = {}

    def register_parser(self, domain: str, parser: AbstractParser) -> None:
        """
        Rejestruje parser dla danej domeny.

        Args:
            domain: Nazwa domeny
            parser: Obiekt parsera
        """
        self.parsers[domain] = parser

    def register_translator(self, domain: str, translator: AbstractTranslator) -> None:
        """
        Rejestruje translator dla danej domeny.

        Args:
            domain: Nazwa domeny
            translator: Obiekt translatora
        """
        self.translators[domain] = translator

    def register_executor(self, domain: str, executor: AbstractExecutor) -> None:
        """
        Rejestruje wykonawcę dla danej domeny.

        Args:
            domain: Nazwa domeny
            executor: Obiekt wykonawcy
        """
        self.executors[domain] = executor

    def register_generator(self, language: str, generator: Any) -> None:
        """
        Rejestruje generator kodu dla danego języka.

        Args:
            language: Język programowania
            generator: Obiekt generatora
        """
        self.generators[language] = generator

    def get_parser(self, domain: str) -> AbstractParser:
        """Pobiera parser dla domeny."""
        if domain not in self.parsers:
            raise KeyError(f"Parser for domain '{domain}' not registered")
        return self.parsers[domain]

    def get_translator(self, domain: str) -> AbstractTranslator:
        """Pobiera translator dla domeny."""
        if domain not in self.translators:
            raise KeyError(f"Translator for domain '{domain}' not registered")
        return self.translators[domain]

    def get_executor(self, domain: str) -> AbstractExecutor:
        """Pobiera wykonawcę dla domeny."""
        if domain not in self.executors:
            raise KeyError(f"Executor for domain '{domain}' not registered")
        return self.executors[domain]

    def get_generator(self, language: str) -> Any:
        """Pobiera generator dla języka."""
        if language not in self.generators:
            raise KeyError(f"Generator for language '{language}' not registered")
        return self.generators[language]

