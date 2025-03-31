# src/dialogware/__init__.py
"""
DialogWare: Text-to-Software
============================

System umożliwiający konwersję poleceń w języku naturalnym na operacje
poprzez kilka warstw abstrakcji, z możliwością generowania kodu w czasie rzeczywistym.
"""

__version__ = "0.1.0"
__author__ = "DialogWare Team"

import os
import importlib
import logging
from typing import Any, Dict, List, Optional, Union, Tuple

from dialogware.core import (
    AbstractParser, AbstractTranslator, AbstractExecutor,
    PluginManager, DialogWareProcessor, CommandResult, Pipeline
)

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class DialogWare:
    """
    Główna klasa systemu DialogWare.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicjalizacja systemu DialogWare.

        Args:
            config: Konfiguracja systemu
        """
        self.config = config or {}
        self.plugin_manager = PluginManager()
        self.processor = DialogWareProcessor(self.plugin_manager)
        self.debuggers = None

        # Inicjalizacja domyślnych komponentów
        self._setup_default_plugins()

        # Inicjalizacja debugerów
        self._setup_debuggers()

    def _setup_default_plugins(self) -> None:
        """
        Konfiguruje domyślne wtyczki systemu.
        """
        # Sprawdzenie czy mamy zainstalowane potrzebne moduły
        try:
            from dialogware.plugins.file_operations import FileOperationParser, FileOperationTranslator, \
                FileOperationExecutor
            self.plugin_manager.register_parser("file", FileOperationParser())
            self.plugin_manager.register_translator("file", FileOperationTranslator())
            self.plugin_manager.register_executor("file", FileOperationExecutor())
            logger.info("Zarejestrowano moduł operacji na plikach")
        except ImportError as e:
            logger.warning(f"Nie można zarejestrować modułu operacji na plikach: {str(e)}")

        try:
            from dialogware.plugins.sql_operations import SQLParser, SQLTranslator, SQLExecutor
            self.plugin_manager.register_parser("sql", SQLParser())
            self.plugin_manager.register_translator("sql", SQLTranslator())
            self.plugin_manager.register_executor("sql", SQLExecutor())
            logger.info("Zarejestrowano moduł operacji SQL")
        except ImportError as e:
            logger.warning(f"Nie można zarejestrować modułu operacji SQL: {str(e)}")

    def _setup_debuggers(self) -> None:
        """
        Konfiguruje debugery systemu.
        """
        try:
            from dialogware.debuggers import setup_debuggers
            self.debuggers = setup_debuggers(self.plugin_manager)
            logger.info("Zarejestrowano debugery")
        except ImportError as e:
            logger.warning(f"Nie można zarejestrować debugerów: {str(e)}")

    def process(self, input_text: str, domain: Optional[str] = None) -> CommandResult:
        """
        Przetwarza polecenie w języku naturalnym.

        Args:
            input_text: Tekst wejściowy w języku naturalnym
            domain: Opcjonalna domena (jeśli znana)

        Returns:
            Wynik wykonania komendy
        """
        return self.processor.process(input_text, domain)

    def debug_process(self, input_text: str, domain: Optional[str] = None) -> Any:
        """
        Debuguje przetwarzanie polecenia.

        Args:
            input_text: Tekst wejściowy
            domain: Opcjonalna domena

        Returns:
            Wynik debugowania
        """
        return self.processor.debug_process(input_text)

    def create_pipeline(self, pipeline_text: str) -> Pipeline:
        """
        Tworzy pipeline na podstawie opisu w języku naturalnym.

        Args:
            pipeline_text: Opis pipeline'u w języku naturalnym

        Returns:
            Skonfigurowany pipeline
        """
        return self.processor.create_pipeline(pipeline_text)

    def register_parser(self, domain: str, parser: AbstractParser) -> None:
        """
        Rejestruje parser dla danej domeny.

        Args:
            domain: Nazwa domeny
            parser: Obiekt parsera
        """
        self.plugin_manager.register_parser(domain, parser)

    def register_translator(self, domain: str, translator: AbstractTranslator) -> None:
        """
        Rejestruje translator dla danej domeny.

        Args:
            domain: Nazwa domeny
            translator: Obiekt translatora
        """
        self.plugin_manager.register_translator(domain, translator)

    def register_executor(self, domain: str, executor: AbstractExecutor) -> None:
        """
        Rejestruje wykonawcę dla danej domeny.

        Args:
            domain: Nazwa domeny
            executor: Obiekt wykonawcy
        """
        self.plugin_manager.register_executor(domain, executor)

    def register_generator(self, language: str, generator: Any) -> None:
        """
        Rejestruje generator kodu dla danego języka.

        Args:
            language: Język programowania
            generator: Obiekt generatora
        """
        self.plugin_manager.register_generator(language, generator)

    async def setup_code_generator(self, api_key: Optional[str] = None,
                                   provider: str = "anthropic",
                                   cache_dir: Optional[str] = None) -> None:
        """
        Konfiguruje generator kodu.

        Args:
            api_key: Klucz API (dla Anthropic)
            provider: Dostawca generatora (anthropic lub ollama)
            cache_dir: Katalog cache
        """
        try:
            from dialogware.plugins.code_generation import setup_code_generator
            generator = setup_code_generator(api_key, provider, cache_dir)
            self.plugin_manager.register_generator(provider, generator)
            logger.info(f"Zarejestrowano generator kodu {provider}")
        except ImportError as e:
            logger.warning(f"Nie można zarejestrować generatora kodu: {str(e)}")

    async def generate_function(self,
                                name: str,
                                params: List[str] = None,
                                description: str = "",
                                examples: List[Tuple] = None,
                                language: str = "python") -> str:
        """
        Generuje kod funkcji.

        Args:
            name: Nazwa funkcji
            params: Lista parametrów
            description: Opis funkcji
            examples: Lista przykładów użycia
            language: Język programowania

        Returns:
            Wygenerowany kod funkcji
        """
        try:
            from dialogware.plugins.code_generation import FunctionSpec

            # Pobierz generator
            generator = self.plugin_manager.get_generator("anthropic")  # Domyślnie Anthropic

            # Utwórz specyfikację funkcji
            spec = FunctionSpec(
                name=name,
                params=params or [],
                description=description,
                examples=examples or [],
                language=language
            )

            # Wygeneruj funkcję
            return await generator.generate_function(spec)
        except ImportError as e:
            logger.error(f"Nie można wygenerować funkcji: {str(e)}")
            return ""
        except Exception as e:
            logger.error(f"Błąd podczas generowania funkcji: {str(e)}")
            return ""


# Funkcja pomocnicza do tworzenia instancji
def create_instance(config: Optional[Dict[str, Any]] = None) -> DialogWare:
    """
    Tworzy i konfiguruje instancję DialogWare.

    Args:
        config: Opcjonalna konfiguracja

    Returns:
        Skonfigurowana instancja DialogWare
    """
    return DialogWare(config)


# Domyślna instancja
default_instance = create_instance()

# Ekspozycja funkcji z domyślnej instancji
process = default_instance.process
debug_process = default_instance.debug_process
create_pipeline = default_instance.create_pipeline