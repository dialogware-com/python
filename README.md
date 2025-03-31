# python
python library - DialogWare: Text-to-Software - Moduł generowania kodu zawiera komponenty potrzebne do generowania kodu na żądanie przy użyciu API Anthropic Claude lub Ollama.

```bash
mdirtree structure.md -o ./dir
```

# DialogWare: Text-to-Software

System umożliwiający konwersję poleceń w języku naturalnym na konkretne operacje poprzez kilka warstw abstrakcji, z możliwością generowania kodu w czasie rzeczywistym.

## Opis projektu

DialogWare: Text-to-Software (wcześniej znany jako Natural Command Processor) to kompleksowy, modularny system, który umożliwia przetwarzanie poleceń w języku naturalnym na operacje komputerowe. System dzięki warstwowej architekturze zapewnia elastyczność i rozszerzalność, a integracja z LLM API pozwala na generowanie kodu na żądanie.

## Architektura systemu

System składa się z 4 głównych warstw abstrakcji:

1. **Parser języka naturalnego** - przetwarza zdania w języku naturalnym na strukturę danych
2. **Translator DSL** - przekształca struktury na język domenowy (DSL)
3. **Pipeline** - umożliwia łańcuchowanie operacji w formie pipe.funkcja1().funkcja2()
4. **Wykonawca komend** - realizuje operacje w różnych domenach

## Główne moduły funkcjonalne

System zawiera następujące moduły:

1. **Moduł operacji na plikach** - znajdowanie, tworzenie, modyfikowanie plików i katalogów
2. **Moduł Text-to-SQL** - konwersja poleceń na zapytania SQL z obsługą fuzzy matching dla tabel/kolumn
3. **Moduł sterowania przeglądarką** - operacje na stronach internetowych (w rozwoju)
4. **Wizualny designer pipeline'ów** - interfejs webowy do projektowania procesów (w rozwoju)
5. **Moduł generowania kodu** - generowanie funkcji na żądanie poprzez Anthropic/Ollama API

## Instalacja

```bash
pip install dialogware
```

Lub zainstaluj z dodatkowymi funkcjonalnościami:

```bash
# Z obsługą przeglądarki
pip install dialogware[browser]

# Z rozszerzonym wsparciem dla SQL
pip install dialogware[sql]

# Z narzędziami programistycznymi
pip install dialogware[dev]

# Pełna instalacja
pip install dialogware[full]
```

## Szybki start

```python
from dialogware import DialogWare

# Inicjalizacja systemu
system = DialogWare()

# Przetwarzanie polecenia w języku naturalnym
result = system.process("znajdź wszystkie pliki tekstowe w katalogu projekty")
print(result.data)

# Tworzenie i wykonanie pipeline'u
pipeline = system.create_pipeline("""
1. Pobierz dane z pliku dane.csv
2. Odfiltruj rekordy z brakującymi polami
3. Zapisz wyniki do bazy danych
""")
pipeline.execute("dane.csv")

# Debugowanie procesu
debug_result = system.debug_process("pokaż 10 najlepszych klientów z największą sumą zamówień")
debug_result.visualize()
```

## Przykłady użycia

### Operacje na plikach

```python
from dialogware import DialogWare

system = DialogWare()

# Znajdowanie plików
result = system.process("znajdź wszystkie pliki PDF większe niż 5MB w katalogu dokumenty")
for file in result.data:
    print(file)

# Wykonywanie złożonych operacji
result = system.process("znajdź duplikaty plików w katalogu projekty i przenieś je do katalog_duplikaty")
print(result.data)
```

### Operacje SQL

```python
import sqlite3
from dialogware import DialogWare
from dialogware.plugins.sql_operations import initialize_module

# Połączenie z bazą danych
conn = sqlite3.connect("baza_danych.db")

# Inicjalizacja systemu
system = DialogWare()

# Inicjalizacja modułu SQL z połączeniem do bazy
parser, translator, executor = initialize_module(conn)
system.register_parser("sql", parser)
system.register_translator("sql", translator)
system.register_executor("sql", executor)

# Wykonanie zapytania
result = system.process("pokaż 10 najlepszych klientów z największą sumą zamówień", domain="sql")
print(result.sql)  # Wygenerowane zapytanie SQL
print(result.data)  # Wyniki zapytania
```

### Generowanie kodu

```python
import asyncio
from dialogware import DialogWare

async def main():
    # Inicjalizacja systemu
    system = DialogWare()
    
    # Konfiguracja generatora kodu
    await system.setup_code_generator(
        api_key="your_anthropic_api_key",  # lub ustaw zmienną środowiskową ANTHROPIC_API_KEY
        provider="anthropic",
        cache_dir="./cache"
    )
    
    # Generowanie funkcji
    code = await system.generate_function(
        name="convert_csv_to_excel",
        params=["file_path", "output_path=None"],
        description="Converts CSV file to Excel format with proper formatting",
        examples=[("data.csv", "data.xlsx")],
        language="python"
    )
    
    print(code)

# Uruchomienie
asyncio.run(main())
```

## Debugowanie

System oferuje narzędzia do debugowania na różnych poziomach:

```python
from dialogware import DialogWare
from dialogware.debuggers import NLPDebugger, DSLDebugger, PipelineDebugger, ExecutionDebugger

system = DialogWare()

# Debugowanie parsowania NLP
nlp_debugger = NLPDebugger()
parse_tree = nlp_debugger.parse("znajdź wszystkie pliki w katalogu projekty", domain="file")
nlp_debugger.visualize(parse_tree)

# Debugowanie kodu DSL
dsl_debugger = DSLDebugger()
dsl_query = dsl_debugger.analyze("find('*.txt').where(size > 1MB)")
dsl_query.print_syntax_tree()
dsl_query.validate()
print