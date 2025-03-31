

import os
import shutil
import glob
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
import fnmatch

from dialogware.core import AbstractParser, AbstractTranslator, AbstractExecutor, CommandResult


class FileOperationParser(AbstractParser):
    """
    Parser poleceń dotyczących operacji na plikach.
    """

    def __init__(self):
        self.commands = {
            "find": ["znajdź", "szukaj", "wyszukaj", "find", "search", "locate"],
            "list": ["listuj", "wyświetl", "pokaż", "list", "show", "display"],
            "create": ["utwórz", "stwórz", "nowy", "create", "new", "make"],
            "delete": ["usuń", "skasuj", "wymaż", "delete", "remove", "erase"],
            "copy": ["kopiuj", "skopiuj", "copy", "duplicate"],
            "move": ["przenieś", "move", "rename"],
            "modify": ["zmodyfikuj", "edytuj", "modify", "edit", "change"],
        }

        self.file_types = {
            "txt": ["txt", "tekst", "text", "tekstowy", "tekstowe"],
            "csv": ["csv", "dane", "data", "values"],
            "json": ["json", "jason"],
            "xml": ["xml"],
            "html": ["html", "htm", "strona", "page"],
            "pdf": ["pdf", "dokument", "document"],
            "image": ["obraz", "zdjęcie", "photo", "image", "img", "jpg", "jpeg", "png", "gif"],
            "video": ["wideo", "video", "film", "movie", "mp4", "avi"],
            "audio": ["audio", "dźwięk", "sound", "mp3", "wav"],
            "doc": ["doc", "docx", "word"],
            "xls": ["xls", "xlsx", "excel", "arkusz", "spreadsheet"],
            "ppt": ["ppt", "pptx", "powerpoint", "prezentacja", "presentation"],
        }

        self.size_units = {
            "b": 1,
            "kb": 1024,
            "mb": 1024 * 1024,
            "gb": 1024 * 1024 * 1024,
            "tb": 1024 * 1024 * 1024 * 1024,
        }

    def parse(self, input_text: str) -> Dict[str, Any]:
        """
        Parsuje tekst w języku naturalnym na strukturę operacji na plikach.

        Args:
            input_text: Tekst wejściowy w języku naturalnym

        Returns:
            Strukturę danych reprezentującą operację na plikach
        """
        input_text = input_text.lower()

        # Wykrywanie operacji
        operation = self._detect_operation(input_text)

        # Wykrywanie parametrów
        params = {}

        # Wykrywanie ścieżek i wzorców plików
        paths, patterns = self._detect_paths_and_patterns(input_text)
        if paths:
            params["paths"] = paths
        if patterns:
            params["patterns"] = patterns

        # Wykrywanie filtrów
        size_filters = self._detect_size_filters(input_text)
        if size_filters:
            params["size_filters"] = size_filters

        date_filters = self._detect_date_filters(input_text)
        if date_filters:
            params["date_filters"] = date_filters

        content_filters = self._detect_content_filters(input_text)
        if content_filters:
            params["content_filters"] = content_filters

        # Wykrywanie akcji po wykonaniu głównej operacji
        additional_actions = self._detect_additional_actions(input_text)
        if additional_actions:
            params["additional_actions"] = additional_actions

        return {
            "operation": operation,
            "params": params,
            "original_text": input_text
        }

    def _detect_operation(self, text: str) -> str:
        """
        Wykrywa rodzaj operacji na podstawie tekstu.

        Args:
            text: Tekst wejściowy

        Returns:
            Nazwa wykrytej operacji
        """
        for operation, keywords in self.commands.items():
            for keyword in keywords:
                if keyword in text.split():
                    return operation

        # Domyślna operacja jeśli nie wykryto innej
        return "find"

    def _detect_paths_and_patterns(self, text: str) -> Tuple[List[str], List[str]]:
        """
        Wykrywa ścieżki i wzorce plików w tekście.

        Args:
            text: Tekst wejściowy

        Returns:
            Krotka (ścieżki, wzorce)
        """
        paths = []
        patterns = []

        # Wykrywanie ścieżek w cudzysłowach
        path_pattern = r'"([^"]+)"|\'([^\']+)\''
        matches = re.finditer(path_pattern, text)
        for match in matches:
            path = match.group(1) or match.group(2)
            if "*" in path or "?" in path:
                patterns.append(path)
            else:
                paths.append(path)

        # Wykrywanie wzorców plików
        for ext, keywords in self.file_types.items():
            for keyword in keywords:
                if keyword in text:
                    if ext == "image":
                        patterns.append("*.jpg")
                        patterns.append("*.jpeg")
                        patterns.append("*.png")
                        patterns.append("*.gif")
                    elif ext == "video":
                        patterns.append("*.mp4")
                        patterns.append("*.avi")
                        patterns.append("*.mkv")
                    elif ext == "audio":
                        patterns.append("*.mp3")
                        patterns.append("*.wav")
                        patterns.append("*.ogg")
                    else:
                        patterns.append(f"*.{ext}")

        # Wykrywanie prostych wzorców typu *.txt
        simple_patterns = re.findall(r'\*\.\w+', text)
        patterns.extend(simple_patterns)

        return paths, list(set(patterns))  # Usuwanie duplikatów

    def _detect_size_filters(self, text: str) -> List[Dict[str, Any]]:
        """
        Wykrywa filtry rozmiaru plików.

        Args:
            text: Tekst wejściowy

        Returns:
            Lista filtrów rozmiaru
        """
        filters = []

        # Wzorzec dla filtrów rozmiaru
        size_pattern = r'(większe|większy|większa|większych|większe niż|larger|bigger|larger than|bigger than|>|mniejsze|mniejszy|mniejsza|mniejszych|mniejsze niż|smaller|smaller than|less than|<) (?:niż |than )?(\d+(?:\.\d+)?)\s*(b|kb|mb|gb|tb)'
        matches = re.finditer(size_pattern, text, re.IGNORECASE)

        for match in matches:
            comparison, size_val, unit = match.groups()
            size = float(size_val) * self.size_units.get(unit.lower(), 1)

            if any(word in comparison.lower() for word in
                   ["większe", "większy", "większa", "większych", "większe niż", "larger", "bigger", "larger than",
                    "bigger than", ">"]):
                operator = ">"
            else:
                operator = "<"

            filters.append({
                "type": "size",
                "operator": operator,
                "value": size
            })

        return filters

    def _detect_date_filters(self, text: str) -> List[Dict[str, Any]]:
        """
        Wykrywa filtry daty plików.

        Args:
            text: Tekst wejściowy

        Returns:
            Lista filtrów daty
        """
        filters = []

        # Wzorce dla różnych okresów czasu
        time_patterns = [
            (r'(nowsze|nowszy|nowsza|nowszych|nowsze niż|newer|newer than) (?:niż |than )?(\d+) (dni|day|days)', "days",
             ">"),
            (r'(starsze|starszy|starsza|starszych|starsze niż|older|older than) (?:niż |than )?(\d+) (dni|day|days)',
             "days", "<"),
            (
            r'(nowsze|nowszy|nowsza|nowszych|nowsze niż|newer|newer than) (?:niż |than )?(\d+) (tygodni|tydzień|tygodnie|week|weeks)',
            "weeks", ">"),
            (
            r'(starsze|starszy|starsza|starszych|starsze niż|older|older than) (?:niż |than )?(\d+) (tygodni|tydzień|tygodnie|week|weeks)',
            "weeks", "<"),
            (
            r'(nowsze|nowszy|nowsza|nowszych|nowsze niż|newer|newer than) (?:niż |than )?(\d+) (miesięcy|miesiąc|miesiące|month|months)',
            "months", ">"),
            (
            r'(starsze|starszy|starsza|starszych|starsze niż|older|older than) (?:niż |than )?(\d+) (miesięcy|miesiąc|miesiące|month|months)',
            "months", "<"),
            (
            r'(nowsze|nowszy|nowsza|nowszych|nowsze niż|newer|newer than) (?:niż |than )?(\d+) (lat|rok|lata|year|years)',
            "years", ">"),
            (
            r'(starsze|starszy|starsza|starszych|starsze niż|older|older than) (?:niż |than )?(\d+) (lat|rok|lata|year|years)',
            "years", "<"),
        ]

        for pattern, unit, operator in time_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                _, value, _ = match.groups()
                filters.append({
                    "type": "date",
                    "operator": operator,
                    "value": int(value),
                    "unit": unit
                })

        # Specjalne wzorce dla określonych okresów
        special_patterns = [
            (r'(dzisiaj|today)', "today"),
            (r'(wczoraj|yesterday)', "yesterday"),
            (r'(w tym tygodniu|this week)', "this_week"),
            (r'(w tym miesiącu|this month)', "this_month"),
            (r'(w tym roku|this year)', "this_year"),
            (r'(ostatni tydzień|last week)', "last_week"),
            (r'(ostatni miesiąc|last month)', "last_month"),
            (r'(ostatni rok|last year)', "last_year"),
        ]

        for pattern, period in special_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                filters.append({
                    "type": "date",
                    "period": period
                })

        return filters

    def _detect_content_filters(self, text: str) -> List[Dict[str, Any]]:
        """
        Wykrywa filtry zawartości plików.

        Args:
            text: Tekst wejściowy

        Returns:
            Lista filtrów zawartości
        """
        filters = []

        # Wzorzec dla zawierającego tekst
        content_patterns = [
            (r'zawierające "(.*?)"|zawierają "(.*?)"|contains "(.*?)"|containing "(.*?)"', "contains"),
            (r'zawierające \'(.*?)\'|zawierają \'(.*?)\'|contains \'(.*?)\'|containing \'(.*?)\'', "contains"),
            (r'niezawierające "(.*?)"|nie zawierają "(.*?)"|not containing "(.*?)"|not contains "(.*?)"',
             "not_contains"),
            (r'niezawierające \'(.*?)\'|nie zawierają \'(.*?)\'|not containing \'(.*?)\'|not contains \'(.*?)\'',
             "not_contains"),
        ]

        for pattern, filter_type in content_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Wybieramy pierwszą niepustą grupę
                content = next((g for g in match.groups() if g), None)
                if content:
                    filters.append({
                        "type": "content",
                        "filter_type": filter_type,
                        "value": content
                    })

        return filters

    def _detect_additional_actions(self, text: str) -> List[Dict[str, Any]]:
        """
        Wykrywa dodatkowe akcje po wykonaniu głównej operacji.

        Args:
            text: Tekst wejściowy

        Returns:
            Lista dodatkowych akcji
        """
        actions = []

        # Wykrywanie akcji kopiowania
        copy_pattern = r'(kopiuj|skopiuj|copy) (?:do|to) [\'"]?([\w\/\.\-]+)[\'"]?'
        copy_matches = re.search(copy_pattern, text, re.IGNORECASE)
        if copy_matches:
            actions.append({
                "action": "copy",
                "destination": copy_matches.group(2)
            })

        # Wykrywanie akcji przenoszenia
        move_pattern = r'(przenieś|move) (?:do|to) [\'"]?([\w\/\.\-]+)[\'"]?'
        move_matches = re.search(move_pattern, text, re.IGNORECASE)
        if move_matches:
            actions.append({
                "action": "move",
                "destination": move_matches.group(2)
            })

        # Wykrywanie konwersji formatu
        convert_pattern = r'(konwertuj|convert) (?:do|to) [\'"]?([\w]+)[\'"]?'
        convert_matches = re.search(convert_pattern, text, re.IGNORECASE)
        if convert_matches:
            actions.append({
                "action": "convert",
                "format": convert_matches.group(2)
            })

        return actions
