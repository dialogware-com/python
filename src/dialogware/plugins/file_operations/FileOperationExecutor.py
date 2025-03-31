# src/dialogware/plugins/file_operations/__init__.py
"""
DialogWare: Text-to-Software - Moduł operacji na plikach
========================================================

Ten moduł zawiera klasy i funkcje do wykonywania operacji na plikach i katalogach
poprzez polecenia w języku naturalnym.
"""

import os
import shutil
import glob
import re
import time
import datetime
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, Iterator
from pathlib import Path
import fnmatch
import json

from dialogware.core import AbstractParser, AbstractTranslator, AbstractExecutor, CommandResult


class FileOperationExecutor(AbstractExecutor):
    """
    Wykonawca operacji na plikach.
    """

    def __init__(self):
        self.operations = {
            "find": self._find_files,
            "list": self._list_files,
            "create": self._create_files,
            "delete": self._delete_files,
            "copy": self._copy_files,
            "move": self._move_files,
            "modify": self._modify_files,
        }

        # Cache dla wyników wyszukiwania, aby umożliwić łańcuchowanie
        self.last_result = []

    def execute(self, command: str) -> Any:
        """
        Wykonuje komendę DSL dla operacji na plikach.

        Args:
            command: Komenda DSL do wykonania

        Returns:
            Wynik wykonania komendy (lista plików lub informacje o statusie)
        """
        # Parsowanie polecenia DSL
        parts = self._parse_dsl(command)
        main_operation = parts["operation"]

        if main_operation not in self.operations:
            raise ValueError(f"Nieznana operacja: {main_operation}")

        # Wywołanie odpowiedniej operacji
        result = self.operations[main_operation](parts)

        # Obsługa akcji łańcuchowych (np. copy_to, move_to)
        for action in parts.get("chain_actions", []):
            action_name = action["action"]

            if action_name == "copy_to":
                result = self._chain_copy_to(result, action["params"][0])
            elif action_name == "move_to":
                result = self._chain_move_to(result, action["params"][0])
            elif action_name == "convert_to":
                result = self._chain_convert_to(result, action["params"][0])
            elif action_name == "where":
                result = self._chain_where(result, action["params"])

        # Zapamiętaj wynik dla późniejszego łańcuchowania
        self.last_result = result

        return result

    def _parse_dsl(self, command: str) -> Dict[str, Any]:
        """
        Parsuje komendę DSL na strukturę danych.

        Args:
            command: Komenda DSL

        Returns:
            Parsowana struktura komendy
        """
        result = {}

        # Wykrywanie głównej operacji
        operation_match = re.match(r'(\w+)\(', command)
        if not operation_match:
            raise ValueError(f"Nieprawidłowa składnia DSL: {command}")

        result["operation"] = operation_match.group(1)

        # Wykrywanie parametrów głównej operacji
        params_str = re.search(r'\((.*?)\)', command)
        if params_str:
            params = params_str.group(1)
            result["params"] = self._parse_params(params)

        # Wykrywanie akcji łańcuchowych
        chain_actions = []
        for action_match in re.finditer(r'\.(\w+)\((.*?)\)', command):
            action_name = action_match.group(1)
            action_params = action_match.group(2)
            chain_actions.append({
                "action": action_name,
                "params": self._parse_params(action_params)
            })

        result["chain_actions"] = chain_actions

        return result

    def _parse_params(self, params_str: str) -> List[Any]:
        """
        Parsuje parametry z części DSL.

        Args:
            params_str: String z parametrami

        Returns:
            Lista parametrów
        """
        if not params_str.strip():
            return []

        # Obsługa prostych parametrów
        if params_str.startswith('"') and params_str.endswith('"'):
            return [params_str[1:-1]]

        # Obsługa list parametrów
        if "paths=" in params_str or "patterns=" in params_str:
            paths = []
            patterns = []

            # Ekstrakcja ścieżek
            paths_match = re.search(r'paths=\[(.*?)\]', params_str)
            if paths_match:
                paths_str = paths_match.group(1)
                paths = [p.strip(' "\'') for p in paths_str.split(",")]

            # Ekstrakcja wzorców
            patterns_match = re.search(r'patterns=\[(.*?)\]', params_str)
            if patterns_match:
                patterns_str = patterns_match.group(1)
                patterns = [p.strip(' "\'') for p in patterns_str.split(",")]

            return [paths, patterns]

        # Obsługa warunków
        if " " in params_str:
            parts = params_str.split()
            if len(parts) >= 3 and parts[1] in [">", "<", "==", "!=", ">=", "<="]:
                return parts

        # Obsługa funkcji wewnętrznych
        func_match = re.match(r'(\w+)\(\'(.*?)\'\)', params_str)
        if func_match:
            func_name = func_match.group(1)
            func_param = func_match.group(2)
            return [func_name, func_param]

        # Domyślnie zwróć jako pojedynczy parametr
        return [params_str]

    def _find_files(self, parsed_command: Dict[str, Any]) -> List[str]:
        """
        Znajduje pliki na podstawie parametrów.

        Args:
            parsed_command: Parsowana komenda

        Returns:
            Lista znalezionych plików
        """
        params = parsed_command.get("params", [])

        paths = []
        patterns = []

        # Ekstrakcja parametrów
        if len(params) == 1 and isinstance(params[0], str):
            # Jeden wzorzec
            patterns = [params[0]]
        elif len(params) == 2 and isinstance(params[0], list) and isinstance(params[1], list):
            # Lista ścieżek i wzorców
            paths = params[0]
            patterns = params[1]

        # Domyślne wartości
        if not paths:
            paths = ["."]
        if not patterns:
            patterns = ["*"]

        # Znajdowanie plików
        found_files = []
        for path in paths:
            for pattern in patterns:
                search_path = os.path.join(path, pattern)
                found_files.extend(glob.glob(search_path, recursive=True))

        return [os.path.abspath(f) for f in found_files]

    def _list_files(self, parsed_command: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Listuje pliki i zwraca szczegółowe informacje.

        Args:
            parsed_command: Parsowana komenda

        Returns:
            Lista informacji o plikach
        """
        files = self._find_files(parsed_command)

        result = []
        for file_path in files:
            try:
                stat = os.stat(file_path)
                file_info = {
                    "path": file_path,
                    "name": os.path.basename(file_path),
                    "directory": os.path.dirname(file_path),
                    "size": stat.st_size,
                    "created": datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "accessed": datetime.datetime.fromtimestamp(stat.st_atime).isoformat(),
                    "is_directory": os.path.isdir(file_path),
                    "extension": os.path.splitext(file_path)[1].lstrip(".").lower() if not os.path.isdir(
                        file_path) else ""
                }
                result.append(file_info)
            except Exception as e:
                print(f"Błąd podczas przetwarzania pliku {file_path}: {str(e)}")

        return result

    def _create_files(self, parsed_command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tworzy pliki lub katalogi.

        Args:
            parsed_command: Parsowana komenda

        Returns:
            Informacja o statusie operacji
        """
        params = parsed_command.get("params", [])

        if not params:
            raise ValueError("Brak ścieżki do utworzenia pliku lub katalogu")

        file_path = params[0] if isinstance(params[0], str) else params[0][0]

        # Określanie czy to katalog czy plik
        is_directory = file_path.endswith("/") or file_path.endswith("\\")

        try:
            if is_directory:
                os.makedirs(file_path, exist_ok=True)
                return {"status": "success", "message": f"Utworzono katalog {file_path}"}
            else:
                # Upewnij się, że katalog nadrzędny istnieje
                parent_dir = os.path.dirname(file_path)
                if parent_dir and not os.path.exists(parent_dir):
                    os.makedirs(parent_dir, exist_ok=True)

                # Utwórz pusty plik jeśli nie istnieje
                if not os.path.exists(file_path):
                    with open(file_path, 'w') as f:
                        pass
                return {"status": "success", "message": f"Utworzono plik {file_path}"}
        except Exception as e:
            return {"status": "error", "message": f"Błąd podczas tworzenia {file_path}: {str(e)}"}

    def _delete_files(self, parsed_command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Usuwa pliki lub katalogi.

        Args:
            parsed_command: Parsowana komenda

        Returns:
            Informacja o statusie operacji
        """
        files = self._find_files(parsed_command)

        if not files:
            return {"status": "warning", "message": "Nie znaleziono plików do usunięcia"}

        deleted = []
        errors = []

        for file_path in files:
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                deleted.append(file_path)
            except Exception as e:
                errors.append({"path": file_path, "error": str(e)})

        return {
            "status": "success" if not errors else "partial",
            "deleted": deleted,
            "errors": errors,
            "count": len(deleted)
        }

    def _copy_files(self, parsed_command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kopiuje pliki lub katalogi.

        Args:
            parsed_command: Parsowana komenda

        Returns:
            Informacja o statusie operacji
        """
        params = parsed_command.get("params", [])

        if len(params) < 2:
            raise ValueError("Nie podano źródła i celu kopiowania")

        source_files = self._find_files({"params": [params[0]]})
        destination = params[1] if isinstance(params[1], str) else params[1][0]

        if not source_files:
            return {"status": "warning", "message": "Nie znaleziono plików do skopiowania"}

        copied = []
        errors = []

        for source in source_files:
            try:
                if os.path.isdir(source):
                    dest_path = os.path.join(destination, os.path.basename(source))
                    shutil.copytree(source, dest_path)
                else:
                    if os.path.isdir(destination):
                        dest_path = os.path.join(destination, os.path.basename(source))
                    else:
                        dest_path = destination
                        # Upewnij się, że katalog nadrzędny istnieje
                        parent_dir = os.path.dirname(dest_path)
                        if parent_dir and not os.path.exists(parent_dir):
                            os.makedirs(parent_dir, exist_ok=True)

                    shutil.copy2(source, dest_path)

                copied.append({"source": source, "destination": dest_path})
            except Exception as e:
                errors.append({"source": source, "error": str(e)})

        return {
            "status": "success" if not errors else "partial",
            "copied": copied,
            "errors": errors,
            "count": len(copied)
        }

    def _move_files(self, parsed_command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Przenosi pliki lub katalogi.

        Args:
            parsed_command: Parsowana komenda

        Returns:
            Informacja o statusie operacji
        """
        params = parsed_command.get("params", [])

        if len(params) < 2:
            raise ValueError("Nie podano źródła i celu przenoszenia")

        source_files = self._find_files({"params": [params[0]]})
        destination = params[1] if isinstance(params[1], str) else params[1][0]

        if not source_files:
            return {"status": "warning", "message": "Nie znaleziono plików do przeniesienia"}

        moved = []
        errors = []

        for source in source_files:
            try:
                if os.path.isdir(destination):
                    dest_path = os.path.join(destination, os.path.basename(source))
                else:
                    dest_path = destination
                    # Upewnij się, że katalog nadrzędny istnieje
                    parent_dir = os.path.dirname(dest_path)
                    if parent_dir and not os.path.exists(parent_dir):
                        os.makedirs(parent_dir, exist_ok=True)

                shutil.move(source, dest_path)
                moved.append({"source": source, "destination": dest_path})
            except Exception as e:
                errors.append({"source": source, "error": str(e)})

        return {
            "status": "success" if not errors else "partial",
            "moved": moved,
            "errors": errors,
            "count": len(moved)
        }

    def _modify_files(self, parsed_command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Modyfikuje zawartość plików.

        Args:
            parsed_command: Parsowana komenda

        Returns:
            Informacja o statusie operacji
        """
        # TODO: Implementacja modyfikacji zawartości plików
        # Ta funkcja będzie rozbudowana w przyszłości

        return {"status": "error", "message": "Funkcja modyfikacji plików nie została jeszcze zaimplementowana"}

    def _chain_where(self, files: List[str], condition: List[str]) -> List[str]:
        """
        Filtruje listę plików na podstawie warunku.

        Args:
            files: Lista plików do filtrowania
            condition: Warunek filtrowania

        Returns:
            Przefiltrowana lista plików
        """
        if len(condition) < 3:
            return files

        property_name = condition[0]
        operator = condition[1]
        value = condition[2]

        filtered_files = []

        for file_path in files:
            if property_name == "size":
                file_size = os.path.getsize(file_path)
                try:
                    size_value = float(value)

                    if operator == ">" and file_size > size_value:
                        filtered_files.append(file_path)
                    elif operator == "<" and file_size < size_value:
                        filtered_files.append(file_path)
                    elif operator == "==" and file_size == size_value:
                        filtered_files.append(file_path)
                    elif operator == ">=" and file_size >= size_value:
                        filtered_files.append(file_path)
                    elif operator == "<=" and file_size <= size_value:
                        filtered_files.append(file_path)
                except ValueError:
                    pass
            elif property_name == "modified":
                if len(condition) >= 4:  # Musi być: modified > 7 days
                    file_mtime = os.path.getmtime(file_path)
                    current_time = time.time()

                    try:
                        time_value = float(condition[2])
                        unit = condition[3]

                        # Konwersja jednostek na sekundy
                        if unit in ["day", "days"]:
                            time_value = time_value * 86400  # 24 * 60 * 60
                        elif unit in ["week", "weeks"]:
                            time_value = time_value * 604800  # 7 * 24 * 60 * 60
                        elif unit in ["month", "months"]:
                            time_value = time_value * 2592000  # 30 * 24 * 60 * 60
                        elif unit in ["year", "years"]:
                            time_value = time_value * 31536000  # 365 * 24 * 60 * 60

                        time_diff = current_time - file_mtime

                        if operator == ">" and time_diff > time_value:
                            filtered_files.append(file_path)
                        elif operator == "<" and time_diff < time_value:
                            filtered_files.append(file_path)
                    except ValueError:
                        pass
            elif condition[0] == "content_contains":
                if len(condition) > 1 and os.path.isfile(file_path):
                    search_text = condition[1]
                    try:
                        with open(file_path, 'r', errors='ignore') as f:
                            content = f.read()
                            if search_text in content:
                                filtered_files.append(file_path)
                    except Exception:
                        pass
            elif condition[0] == "modified_in":
                if len(condition) > 1:
                    period = condition[1]
                    file_mtime = os.path.getmtime(file_path)
                    file_date = datetime.datetime.fromtimestamp(file_mtime)
                    current_date = datetime.datetime.now()

                    if period == "today":
                        if file_date.date() == current_date.date():
                            filtered_files.append(file_path)
                    elif period == "yesterday":
                        yesterday = current_date - datetime.timedelta(days=1)
                        if file_date.date() == yesterday.date():
                            filtered_files.append(file_path)
                    elif period == "this_week":
                        start_of_week = current_date - datetime.timedelta(days=current_date.weekday())
                        if file_date.date() >= start_of_week.date():
                            filtered_files.append(file_path)
                    elif period == "this_month":
                        if file_date.year == current_date.year and file_date.month == current_date.month:
                            filtered_files.append(file_path)
                    elif period == "this_year":
                        if file_date.year == current_date.year:
                            filtered_files.append(file_path)
                    elif period == "last_week":
                        start_of_last_week = current_date - datetime.timedelta(days=current_date.weekday() + 7)
                        end_of_last_week = start_of_last_week + datetime.timedelta(days=6)
                        if start_of_last_week.date() <= file_date.date() <= end_of_last_week.date():
                            filtered_files.append(file_path)
                    elif period == "last_month":
                        last_month = current_date.month - 1
                        year = current_date.year
                        if last_month == 0:
                            last_month = 12
                            year -= 1
                        if file_date.year == year and file_date.month == last_month:
                            filtered_files.append(file_path)
                    elif period == "last_year":
                        if file_date.year == current_date.year - 1:
                            filtered_files.append(file_path)

        return filtered_files

    def _chain_copy_to(self, files: List[str], destination: str) -> Dict[str, Any]:
        """
        Kopiuje wynik poprzedniej operacji do celu.

        Args:
            files: Lista plików do skopiowania
            destination: Katalog docelowy

        Returns:
            Informacja o statusie operacji
        """
        if not os.path.exists(destination):
            os.makedirs(destination, exist_ok=True)

        copied = []
        errors = []

        for source in files:
            try:
                dest_path = os.path.join(destination, os.path.basename(source))
                if os.path.isdir(source):
                    shutil.copytree(source, dest_path)
                else:
                    shutil.copy2(source, dest_path)
                copied.append({"source": source, "destination": dest_path})
            except Exception as e:
                errors.append({"source": source, "error": str(e)})

        return {
            "status": "success" if not errors else "partial",
            "copied": copied,
            "errors": errors,
            "count": len(copied)
        }

    def _chain_move_to(self, files: List[str], destination: str) -> Dict[str, Any]:
        """
        Przenosi wynik poprzedniej operacji do celu.

        Args:
            files: Lista plików do przeniesienia
            destination: Katalog docelowy

        Returns:
            Informacja o statusie operacji
        """
        if not os.path.exists(destination):
            os.makedirs(destination, exist_ok=True)

        moved = []
        errors = []

        for source in files:
            try:
                dest_path = os.path.join(destination, os.path.basename(source))
                shutil.move(source, dest_path)
                moved.append({"source": source, "destination": dest_path})
            except Exception as e:
                errors.append({"source": source, "error": str(e)})

        return {
            "status": "success" if not errors else "partial",
            "moved": moved,
            "errors": errors,
            "count": len(moved)
        }

    def _chain_convert_to(self, files: List[str], format_to: str) -> Dict[str, Any]:
        """
        Konwertuje pliki do innego formatu.

        Args:
            files: Lista plików do konwersji
            format_to: Format docelowy

        Returns:
            Informacja o statusie operacji
        """
        # Ta funkcja wymaga implementacji wielu konwerterów formatów
        # Na razie zwracamy informację o braku implementacji

        return {
            "status": "error",
            "message": f"Konwersja do formatu {format_to} nie została jeszcze zaimplementowana",
            "files": files
        }
