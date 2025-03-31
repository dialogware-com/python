# mdirtree

1. Podstawowe wymagania (`requirements.txt`):
   - flask - dla REST API
   - requests - dla klienta HTTP
   - click - dla CLI
   - colorama - dla kolorowego output
   - typing-extensions - dla lepszego typowania
   - pyyaml - dla obsługi YAML

2. Wymagania deweloperskie (`requirements-dev.txt`):
   - pytest - testy jednostkowe
   - coverage - pokrycie kodu
   - black - formatowanie kodu
   - flake8 - linting
   - mypy - sprawdzanie typów
   - isort - sortowanie importów
   - pre-commit - hooki gita
   - tox - testowanie na różnych wersjach Pythona
   - twine i build - do publikacji na PyPI

3. Konfiguracja tox (`tox.ini`):
   - Testowanie na Python 3.7-3.10
   - Automatyczne linting i formatowanie
   - Generowanie raportów pokrycia

4. Pre-commit hooki (`.pre-commit-config.yaml`):
   - Sprawdzanie białych znaków
   - Formatowanie black
   - Sortowanie importów
   - Linting flake8

5. Konfiguracja setuptools (`setup.cfg`):
   - Metadane projektu
   - Zależności
   - Konfiguracja mypy
   - Konfiguracja pytest
   - Konfiguracja coverage
   - Konfiguracja isort

Aby użyć:

1. Instalacja podstawowa:
```bash
pip install -r requirements.txt
```

2. Instalacja dla deweloperów:
```bash
pip install -r requirements-dev.txt
```

3. Uruchomienie testów:
```bash
tox
```

4. Instalacja pre-commit hooków:
```bash
pre-commit install
```

5. Sprawdzenie formatowania:
```bash
black .
flake8 .
mypy src/mdirtree
isort .
```

Aktualizacja
```bash
pip install -e .
```

Ta konfiguracja zapewnia:
- Spójne formatowanie kodu
- Sprawdzanie typów
- Automatyczne testy
- Pokrycie kodu
- Czystość commitów
- Kompatybilność z różnymi wersjami Pythona

