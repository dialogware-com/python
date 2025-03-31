# src/dialogware/plugins/code_generation/__init__.py
"""
DialogWare: Text-to-Software - Moduł generowania kodu
=====================================================

Ten moduł zawiera komponenty potrzebne do generowania kodu na żądanie
przy użyciu API Anthropic Claude lub Ollama.
"""

import os
import re
import json
import inspect
import asyncio
import aiohttp
import tempfile
import logging
from typing import Any, Dict, List, Optional, Callable, Union, TypeVar, Tuple

from dialogware.core import CommandResult

logger = logging.getLogger(__name__)


class FunctionSpec:
    """
    Specyfikacja funkcji do wygenerowania.
    """

    def __init__(
            self,
            name: str,
            params: List[str] = None,
            description: str = "",
            examples: List[Tuple] = None,
            return_type: str = None,
            imports: List[str] = None,
            language: str = "python"
    ):
        """
        Inicjalizacja specyfikacji funkcji.

        Args:
            name: Nazwa funkcji
            params: Lista parametrów
            description: Opis funkcji
            examples: Lista przykładów użycia (argumenty, oczekiwany wynik)
            return_type: Typ zwracany przez funkcję
            imports: Lista modułów do zaimportowania
            language: Język programowania
        """
        self.name = name
        self.params = params or []
        self.description = description
        self.examples = examples or []
        self.return_type = return_type
        self.imports = imports or []
        self.language = language.lower()

    def to_dict(self) -> Dict[str, Any]:
        """
        Konwertuje specyfikację do słownika.

        Returns:
            Słownik reprezentujący specyfikację
        """
        return {
            "name": self.name,
            "params": self.params,
            "description": self.description,
            "examples": self.examples,
            "return_type": self.return_type,
            "imports": self.imports,
            "language": self.language
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FunctionSpec':
        """
        Tworzy specyfikację z słownika.

        Args:
            data: Słownik z danymi specyfikacji

        Returns:
            Obiekt specyfikacji
        """
        return cls(
            name=data.get("name", ""),
            params=data.get("params", []),
            description=data.get("description", ""),
            examples=data.get("examples", []),
            return_type=data.get("return_type"),
            imports=data.get("imports", []),
            language=data.get("language", "python")
        )

    def get_signature(self) -> str:
        """
        Zwraca sygnaturę funkcji.

        Returns:
            Sygnatura funkcji
        """
        if self.language == "python":
            params_str = ", ".join(self.params)
            return_type_str = f" -> {self.return_type}" if self.return_type else ""
            return f"def {self.name}({params_str}){return_type_str}:"
        elif self.language == "javascript":
            params_str = ", ".join(self.params)
            return f"function {self.name}({params_str}) {{"
        else:
            raise ValueError(f"Nieobsługiwany język: {self.language}")


class AnthropicClient:
    """
    Klient API Anthropic Claude.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com",
                 model: str = "claude-3-haiku-20240307"):
        """
        Inicjalizacja klienta API Anthropic.

        Args:
            api_key: Klucz API Anthropic
            base_url: Bazowy URL API
            model: Model Claude do użycia
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.headers = {
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "x-api-key": api_key
        }

    async def generate_code(self, prompt: str, max_tokens: int = 4000) -> str:
        """
        Generuje kod przy użyciu API Anthropic Claude.

        Args:
            prompt: Prompt dla Claude
            max_tokens: Maksymalna liczba tokenów w odpowiedzi

        Returns:
            Wygenerowany kod
        """
        url = f"{self.base_url}/v1/messages"

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=self.headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Error from Anthropic API: {response.status} - {error_text}")

                response_data = await response.json()
                content = response_data.get("content", [])

                # Wyodrębnienie tekstu z odpowiedzi
                text = "".join([block.get("text", "") for block in content if block.get("type") == "text"])

                # Wyodrębnienie kodu z odpowiedzi
                code_blocks = re.findall(r'```(?:\w+)?\s*([\s\S]+?)\s*```', text)

                if code_blocks:
                    return code_blocks[0].strip()
                return text.strip()

    async def generate_function(self, spec: FunctionSpec) -> str:
        """
        Generuje funkcję na podstawie specyfikacji.

        Args:
            spec: Specyfikacja funkcji

        Returns:
            Wygenerowany kod funkcji
        """
        language = spec.language
        prompt = self._create_function_prompt(spec)

        return await self.generate_code(prompt)

    def _create_function_prompt(self, spec: FunctionSpec) -> str:
        """
        Tworzy prompt do generowania funkcji.

        Args:
            spec: Specyfikacja funkcji

        Returns:
            Prompt dla Claude
        """
        language_desc = "Python" if spec.language == "python" else "JavaScript" if spec.language == "javascript" else spec.language

        prompt = f"""Write a {language_desc} function that matches this specification:

Function name: {spec.name}
Parameters: {', '.join(spec.params)}
Description: {spec.description}
"""

        if spec.return_type:
            prompt += f"Return type: {spec.return_type}\n"

        if spec.imports:
            prompt += f"Required imports: {', '.join(spec.imports)}\n"

        if spec.examples:
            prompt += "\nExamples:\n"
            for args, result in spec.examples:
                args_str = ', '.join([f"{arg}" for arg in args])
                prompt += f"- Input: {args_str}, Expected output: {result}\n"

        prompt += f"\nWrite only the {language_desc} code with no explanation. Start with imports and then the function definition."

        return prompt


class CodeGenerator:
    """
    Generator kodu dla różnych języków programowania.
    """

    def __init__(self, api_key: Optional[str] = None, provider: str = "anthropic"):
        """
        Inicjalizacja generatora kodu.

        Args:
            api_key: Klucz API (dla Anthropic)
            provider: Dostawca generatora (anthropic lub ollama)
        """
        self.provider = provider.lower()
        self.api_key = api_key

        if self.provider == "anthropic":
            if not api_key:
                raise ValueError("Dla Anthropic wymagany jest klucz API")
            self.client = AnthropicClient(api_key)
        elif self.provider == "ollama":
            self.client = OllamaClient()
        else:
            raise ValueError(f"Nieobsługiwany dostawca: {provider}")

    async def generate_function(self, spec: Union[FunctionSpec, Dict[str, Any]],
                                cache_dir: Optional[str] = None) -> str:
        """
        Generuje kod funkcji na podstawie specyfikacji.

        Args:
            spec: Specyfikacja funkcji
            cache_dir: Katalog cache dla wygenerowanych funkcji

        Returns:
            Kod wygenerowanej funkcji
        """
        if isinstance(spec, dict):
            spec = FunctionSpec.from_dict(spec)

        # Sprawdzenie cache
        if cache_dir:
            cache_file = self._get_cache_path(spec, cache_dir)
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return f.read()

        # Generowanie kodu
        code = await self.client.generate_function(spec)

        # Zapis do cache
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
            cache_file = self._get_cache_path(spec, cache_dir)
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(code)

        return code

    async def complete_implementation(self, partial_code: str, requirements: str,
                                      language: str = "python",
                                      cache_dir: Optional[str] = None) -> str:
        """
        Uzupełnia implementację istniejącego kodu.

        Args:
            partial_code: Częściowy kod do uzupełnienia
            requirements: Opis wymagań
            language: Język programowania
            cache_dir: Katalog cache

        Returns:
            Uzupełniony kod
        """
        # Utworzenie hasha dla cache
        cache_key = f"{language}_{partial_code[:100]}_{requirements[:100]}"
        import hashlib
        cache_file_name = hashlib.md5(cache_key.encode()).hexdigest() + ".code"

        # Sprawdzenie cache
        if cache_dir:
            cache_file = os.path.join(cache_dir, cache_file_name)
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return f.read()

        # Utworzenie prompta
        prompt = f"""Complete the following {language} code according to these requirements:

Requirements:
{requirements}

Partial code:
```{language}
{partial_code}
```

Complete the implementation. Write the full code without explanation."""

        # Generowanie kodu
        code = await self.client.generate_code(prompt)

        # Zapis do cache
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
            cache_file = os.path.join(cache_dir, cache_file_name)
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(code)

        return code

    def _get_cache_path(self, spec: FunctionSpec, cache_dir: str) -> str:
        """
        Zwraca ścieżkę pliku cache dla specyfikacji.

        Args:
            spec: Specyfikacja funkcji
            cache_dir: Katalog cache

        Returns:
            Ścieżka pliku cache
        """
        # Utworzenie nazwy pliku w oparciu o specyfikację
        cache_key = f"{spec.language}_{spec.name}_{','.join(spec.params)}"
        import hashlib
        cache_file_name = hashlib.md5(cache_key.encode()).hexdigest() + f".{spec.language}"

        return os.path.join(cache_dir, cache_file_name)


class CodeAnalyzer:
    """
    Analizator kodu służący do wykrywania brakujących funkcji.
    """

    def analyze_code(self, code: str) -> List[FunctionSpec]:
        """
        Analizuje kod w poszukiwaniu wywołań nieistniejących funkcji.

        Args:
            code: Kod do analizy

        Returns:
            Lista specyfikacji brakujących funkcji
        """
        missing_functions = []

        # Wzorzec dla wywołań funkcji w Pythonie
        # Uproszczona implementacja - w rzeczywistości potrzebny byłby parser AST
        pattern = r'(\w+)\s*\(([^\)]*)\)'

        # Wykrywanie funkcji wbudowanych
        import builtins
        builtin_functions = dir(builtins)

        # Wykrywanie zdefiniowanych funkcji
        defined_pattern = r'def\s+(\w+)\s*\('
        defined_functions = re.findall(defined_pattern, code)

        # Wykrywanie zaimportowanych funkcji
        import_pattern = r'from\s+(\w+)\s+import\s+([^#\n]+)'
        imports = re.findall(import_pattern, code)
        imported_functions = []
        for module, funcs in imports:
            imported_functions.extend([f.strip() for f in funcs.split(',')])

        # Znajdowanie wywołań funkcji
        for match in re.finditer(pattern, code):
            func_name = match.group(1)
            args_str = match.group(2)

            # Ignorowanie funkcji wbudowanych i już zdefiniowanych
            if func_name in builtin_functions or func_name in defined_functions or func_name in imported_functions:
                continue

            # Analiza argumentów
            args = [arg.strip() for arg in args_str.split(',') if arg.strip()]

            # Utworzenie specyfikacji
            spec = FunctionSpec(
                name=func_name,
                params=["arg" + str(i + 1) for i in range(len(args))],
                description=f"Function {func_name} that should handle these arguments: {args_str}"
            )

            missing_functions.append(spec)

        return missing_functions


async def dynamic_code_generation(code: str, generator: CodeGenerator,
                                  analyzer: Optional[CodeAnalyzer] = None,
                                  cache_dir: Optional[str] = None) -> Tuple[str, List[str]]:
    """
    Dynamicznie generuje brakujące funkcje w kodzie.

    Args:
        code: Kod do analizy
        generator: Generator kodu
        analyzer: Analizator kodu
        cache_dir: Katalog cache

    Returns:
        Krotka (uzupełniony kod, lista wygenerowanych funkcji)
    """
    analyzer = analyzer or CodeAnalyzer()
    missing_functions = analyzer.analyze_code(code)

    generated_functions = []

    for func_spec in missing_functions:
        try:
            generated_code = await generator.generate_function(func_spec, cache_dir)
            generated_functions.append(generated_code)
        except Exception as e:
            logger.error(f"Błąd podczas generowania funkcji {func_spec.name}: {str(e)}")

    # Łączenie oryginalnego kodu z wygenerowanymi funkcjami
    if generated_functions:
        result_code = "\n\n".join(generated_functions) + "\n\n" + code
    else:
        result_code = code

    return result_code, generated_functions


def setup_code_generator(api_key: Optional[str] = None, provider: str = "anthropic",
                         cache_dir: Optional[str] = None) -> CodeGenerator:
    """
    Konfiguruje generator kodu.

    Args:
        api_key: Klucz API (dla Anthropic)
        provider: Dostawca generatora (anthropic lub ollama)
        cache_dir: Katalog cache

    Returns:
        Skonfigurowany generator kodu
    """
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)

    if provider == "anthropic" and not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Brak klucza API Anthropic. Ustaw ANTHROPIC_API_KEY lub podaj api_key")

    return CodeGenerator(api_key=api_key, provider=provider)


# Przykład użycia
if __name__ == "__main__":
    async def example():
        # Przykładowa specyfikacja funkcji
        spec = FunctionSpec(
            name="convert_csv_to_excel",
            params=["file_path", "output_path=None"],
            description="Converts CSV file to Excel format",
            examples=[("data.csv", "data.xlsx")],
            imports=["pandas"]
        )

        # Inicjalizacja generatora kodu
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Brak klucza API. Ustaw ANTHROPIC_API_KEY")
            return

        generator = setup_code_generator(api_key)

        # Generowanie funkcji
        code = await generator.generate_function(spec)
        print(f"Wygenerowany kod:\n{code}\n")

        # Przykład uzupełniania implementacji
        partial_code = """
def extract_keywords(text, max_keywords=5):
    # Extract most relevant keywords from text
    # Implementation needed
    pass
"""

        requirements = """
The function should extract the most important keywords from the given text.
It should tokenize the text, remove stopwords, and use TF-IDF to identify important terms.
Return a list of the top 'max_keywords' keywords.
"""

        completed_code = await generator.complete_implementation(partial_code, requirements)
        print(f"Uzupełniony kod:\n{completed_code}\n")

        # Przykład dynamicznego generowania kodu
        code_with_missing_functions = """
def process_data(filepath):
    data = load_data(filepath)
    cleaned_data = clean_data(data)
    return analyze_results(cleaned_data)
"""

        analyzer = CodeAnalyzer()
        full_code, generated = await dynamic_code_generation(code_with_missing_functions, generator, analyzer)
        print(f"Pełny kod z wygenerowanymi funkcjami:\n{full_code}\n")


    import asyncio

    asyncio.run(example())


    def __init__(self, base_globals: Optional[Dict[str, Any]] = None):
        """
        Inicjalizacja środowiska wykonawczego.

        Args:
            base_globals: Bazowa słownik globalnych zmiennych
        """
        self.base_globals = base_globals or {}
        self.temp_globals = {}


    def execute_code(self, code: str, locals_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Wykonuje kod w bezpiecznym środowisku.

        Args:
            code: Kod do wykonania
            locals_dict: Słownik lokalnych zmiennych

        Returns:
            Słownik zmiennych po wykonaniu
        """
        # Kopiowanie bazowych zmiennych globalnych
        globals_dict = self.base_globals.copy()

        # Dodanie standardowych modułów
        import math, re, datetime, json, os, sys
        globals_dict.update({
            'math': math,
            're': re,
            'datetime': datetime,
            'json': json,
            'os': os,
            'sys': sys,
        })

        # Utworzenie lokalnego środowiska
        locals_dict = locals_dict or {}

        # Wykonanie kodu
        exec(code, globals_dict, locals_dict)

        # Zachowanie zmiennych globalnych
        self.temp_globals = globals_dict

        return locals_dict


    def call_function(self, function_name: str, *args, **kwargs) -> Any:
        """
        Wywołuje funkcję zdefiniowaną w środowisku.

        Args:
            function_name: Nazwa funkcji do wywołania
            *args: Argumenty pozycyjne
            **kwargs: Argumenty nazwane

        Returns:
            Wynik wywołania funkcji
        """
        if function_name not in self.temp_globals:
            raise ValueError(f"Funkcja {function_name} nie istnieje w środowisku")

        func = self.temp_globals[function_name]
        if not callable(func):
            raise ValueError(f"{function_name} nie jest funkcją")

        return func(*args, **kwargs)


    def __init__(self, base_url: str = "http://localhost:11434", model: str = "codellama"):
        """
        Inicjalizacja klienta API Ollama.

        Args:
            base_url: Bazowy URL API Ollama
            model: Model Ollama do użycia
        """
        self.base_url = base_url
        self.model = model


    async def generate_code(self, prompt: str, max_tokens: int = 4000) -> str:
        """
        Generuje kod przy użyciu API Ollama.

        Args:
            prompt: Prompt dla modelu
            max_tokens: Maksymalna liczba tokenów w odpowiedzi

        Returns:
            Wygenerowany kod
        """
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Error from Ollama API: {response.status} - {error_text}")

                response_data = await response.json()
                text = response_data.get("response", "")

                # Wyodrębnienie kodu z odpowiedzi
                code_blocks = re.findall(r'```(?:\w+)?\s*([\s\S]+?)\s*```', text)

                if code_blocks:
                    return code_blocks[0].strip()
                return text.strip()


    async def generate_function(self, spec: FunctionSpec) -> str:
        """
        Generuje funkcję na podstawie specyfikacji.

        Args:
            spec: Specyfikacja funkcji

        Returns:
            Wygenerowany kod funkcji
        """
        language = spec.language
        prompt = self._create_function_prompt(spec)

        return await self.generate_code(prompt)


    def _create_function_prompt(self, spec: FunctionSpec) -> str:
        """
        Tworzy prompt do generowania funkcji.

        Args:
            spec: Specyfikacja funkcji

        Returns:
            Prompt dla modelu
        """
        language_desc = "Python" if spec.language == "python" else "JavaScript" if spec.language == "javascript" else spec.language

        prompt = f"""Write a {language_desc} function that matches this specification:

Function name: {spec.name}
Parameters: {', '.join(spec.params)}
Description: {spec.description}
"""

        if spec.return_type:
            prompt += f"Return type: {spec.return_type}\n"

        if spec.imports:
            prompt += f"Required imports: {', '.join(spec.imports)}\n"

        if spec.examples:
            prompt += "\nExamples:\n"
            for args, result in spec.examples:
                args_str = ', '.join([f"{arg}" for arg in args])
                prompt += f"- Input: {args_str}, Expected output: {result}\n"

        prompt += f"\nWrite only the {language_desc} code with no explanation. Start with imports and then the function definition."

        return prompt