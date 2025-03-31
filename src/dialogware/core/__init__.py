# src/dialogware/core/__init__.py
"""
DialogWare: Text-to-Software - rdzeń systemu
============================================

Ten moduł zawiera podstawowe klasy abstrakcyjne definiujące architekturę systemu.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic

T = TypeVar('T')
U = TypeVar('U')


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


class PipelineElement(Generic[T, U]):
    """
    Element pipeline'u, który przetwarza dane wejściowe i zwraca wynik.
    """

    def __init__(self, function: Callable[[T], U], name: Optional[str] = None):
        self.function = function
        self.name = name or function.__name__

    def __call__(self, input_data: T) -> U:
        return self.function(input_data)


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


class CommandResult:
    """
    Klasa reprezentująca wynik wykonania komendy.
    """

    def __init__(self,
                 success: bool,
                 data: Any = None,
                 error: Optional[str] = None,
                 generated_code: Optional[str] = None,
                 execution_log: Optional[List[Dict[str, Any]]] = None,
                 sql: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error
        self.generated_code = generated_code
        self.execution_log = execution_log or []
        self.sql = sql

    def __repr__(self) -> str:
        if self.success:
            return f"CommandResult(success=True, data={self.data})"
        return f"CommandResult(success=False, error={self.error})"


class DialogWareProcessor:
    """
    Główny procesor systemu DialogWare integrujący wszystkie komponenty.
    """

    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager
        self.context = {}
        self.history = []

    def process(self, input_text: str, domain: Optional[str] = None) -> CommandResult:
        """
        Przetwarza polecenie w języku naturalnym.

        Args:
            input_text: Tekst wejściowy w języku naturalnym
            domain: Opcjonalna domena (jeśli znana)

        Returns:
            Wynik wykonania komendy
        """
        # Dodaj polecenie do historii
        self.history.append(input_text)

        if domain is None:
            # TODO: Implementacja automatycznego wykrywania domeny
            domain = "default"

        try:
            # Pobierz odpowiednie komponenty
            parser = self.plugin_manager.get_parser(domain)
            translator = self.plugin_manager.get_translator(domain)
            executor = self.plugin_manager.get_executor(domain)

            # Przetwarzanie polecenia
            parsed_data = parser.parse(input_text)
            dsl_command = translator.translate(parsed_data)
            result = executor.execute(dsl_command)

            return CommandResult(
                success=True,
                data=result,
                execution_log=[{
                    "stage": "parsing",
                    "input": input_text,
                    "output": parsed_data
                }, {
                    "stage": "translation",
                    "input": parsed_data,
                    "output": dsl_command
                }, {
                    "stage": "execution",
                    "input": dsl_command,
                    "output": result
                }]
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=str(e)
            )

    def create_pipeline(self, pipeline_text: str) -> Pipeline:
        """
        Tworzy pipeline na podstawie opisu w języku naturalnym.

        Args:
            pipeline_text: Opis pipeline'u w języku naturalnym

        Returns:
            Skonfigurowany pipeline
        """
        # TODO: Implementacja tworzenia pipeline'u z tekstu
        pipeline = Pipeline()

        # Tutaj wstępna implementacja mockująca działanie
        lines = pipeline_text.strip().split("\n")
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Usunięcie numeracji jeśli istnieje
            if line[0].isdigit() and ". " in line:
                line = line.split(". ", 1)[1]

            # Tworzymy element pipeline'u, który na razie tylko loguje
            element = PipelineElement(
                lambda data, step=line: self._mock_pipeline_step(data, step),
                name=f"step_{i + 1}"
            )
            pipeline.add(element)

        return pipeline

    def _mock_pipeline_step(self, data: Any, step_description: str) -> Any:
        """
        Tymczasowa implementacja kroku pipeline'u.

        Args:
            data: Dane wejściowe
            step_description: Opis kroku

        Returns:
            Dane wyjściowe (w mockowanej implementacji takie same jak wejściowe)
        """
        print(f"Executing: {step_description}")
        # W przyszłości tu będzie prawdziwa implementacja
        return data

    def debug_process(self, input_text: str) -> 'DebugResult':
        """
        Debuguje przetwarzanie polecenia.

        Args:
            input_text: Tekst wejściowy

        Returns:
            Wynik debugowania
        """
        from dialogware.debuggers.debug_result import DebugResult

        # TODO: Implementacja właściwego debugowania
        return DebugResult(
            input_text=input_text,
            nlp_tree={},
            dsl_representation="",
            execution_trace=[]
        )