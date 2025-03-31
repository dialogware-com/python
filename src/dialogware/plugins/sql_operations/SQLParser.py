
import re
import sqlite3
import json
import datetime
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union, Set
from difflib import SequenceMatcher
import logging

from dialogware.core import AbstractParser, AbstractTranslator, AbstractExecutor, CommandResult

logger = logging.getLogger(__name__)


class SQLParser(AbstractParser):
    """
    Parser poleceń SQL w języku naturalnym.
    """

    def __init__(self, schema: Optional['SQLSchema'] = None):
        self.schema = schema or SQLSchema()

        # Słowniki akcji i operacji SQL
        self.actions = {
            "select": ["pokaż", "wyświetl", "znajdź", "wyszukaj", "pobierz", "lista", "get", "show", "display", "find",
                       "search", "retrieve", "list", "select"],
            "insert": ["dodaj", "wstaw", "utwórz", "wprowadź", "nowy", "add", "insert", "create", "new"],
            "update": ["zaktualizuj", "zmień", "modyfikuj", "popraw", "update", "modify", "change", "alter"],
            "delete": ["usuń", "kasuj", "wymaż", "skasuj", "remove", "delete", "erase"],
            "count": ["policz", "zlicz", "count", "calculate", "compute"],
            "group": ["grupuj", "group", "categorize"],
            "sort": ["sortuj", "uporządkuj", "sort", "order"],
            "join": ["połącz", "złącz", "join", "combine", "merge"],
            "limit": ["ogranicz", "limit", "top"],
        }

        # Operatory porównania
        self.operators = {
            "równe": "=",
            "równy": "=",
            "równa": "=",
            "równych": "=",
            "jest": "=",
            "to": "=",
            "wynosi": "=",
            "większe": ">",
            "większy": ">",
            "większa": ">",
            "powyżej": ">",
            "mniejsze": "<",
            "mniejszy": "<",
            "mniejsza": "<",
            "poniżej": "<",
            "co najmniej": ">=",
            "minimum": ">=",
            "przynajmniej": ">=",
            "nie więcej niż": "<=",
            "maksimum": "<=",
            "co najwyżej": "<=",
            "różne od": "<>",
            "nie jest": "<>",
            "inne niż": "<>",
            "not": "<>",
            "=": "=",
            ">": ">",
            "<": "<",
            ">=": ">=",
            "<=": "<=",
            "!=": "<>",
            "<>": "<>",
        }

        # Operatory logiczne
        self.logical_operators = {
            "i": "AND",
            "oraz": "AND",
            "także": "AND",
            "jednocześnie": "AND",
            "lub": "OR",
            "albo": "OR",
            "ewentualnie": "OR",
            "nie": "NOT",
            "bez": "NOT",
            "and": "AND",
            "or": "OR",
            "not": "NOT",
        }

        # Kierunki sortowania
        self.sort_directions = {
            "rosnąco": "ASC",
            "od najmniejszego": "ASC",
            "od najmniejszej": "ASC",
            "od najniższego": "ASC",
            "malejąco": "DESC",
            "od największego": "DESC",
            "od największej": "DESC",
            "od najwyższego": "DESC",
            "asc": "ASC",
            "ascending": "ASC",
            "desc": "DESC",
            "descending": "DESC",
        }

        # Funkcje agregujące
        self.aggregations = {
            "suma": "SUM",
            "łącznie": "SUM",
            "razem": "SUM",
            "średnia": "AVG",
            "średni": "AVG",
            "średnio": "AVG",
            "maksimum": "MAX",
            "maksymalny": "MAX",
            "maksymalna": "MAX",
            "najwyższy": "MAX",
            "najwyższa": "MAX",
            "minimum": "MIN",
            "minimalny": "MIN",
            "minimalna": "MIN",
            "najniższy": "MIN",
            "najniższa": "MIN",
            "liczba": "COUNT",
            "ilość": "COUNT",
            "sum": "SUM",
            "total": "SUM",
            "avg": "AVG",
            "average": "AVG",
            "mean": "AVG",
            "max": "MAX",
            "maximum": "MAX",
            "highest": "MAX",
            "min": "MIN",
            "minimum": "MIN",
            "lowest": "MIN",
            "count": "COUNT",
            "number": "COUNT",
            "quantity": "COUNT",
        }

    def parse(self, input_text: str) -> Dict[str, Any]:
        """
        Parsuje tekst w języku naturalnym na strukturę zapytania SQL.

        Args:
            input_text: Tekst wejściowy w języku naturalnym

        Returns:
            Strukturę danych reprezentującą zapytanie SQL
        """
        input_text = input_text.lower()

        # Wykrywanie głównej akcji (SELECT, INSERT, UPDATE, DELETE)
        action = self._detect_action(input_text)

        # Wykrywanie tabel
        tables = self._detect_tables(input_text)

        # Struktura zapytania
        query = {
            "action": action,
            "tables": tables,
            "original_text": input_text
        }

        # Dodatkowe elementy w zależności od akcji
        if action == "select":
            columns = self._detect_columns(input_text, tables)
            conditions = self._detect_conditions(input_text, tables)
            joins = self._detect_joins(input_text, tables)
            group_by = self._detect_group_by(input_text, tables)
            order_by = self._detect_order_by(input_text, tables)
            limit = self._detect_limit(input_text)

            query.update({
                "columns": columns,
                "conditions": conditions,
                "joins": joins,
                "group_by": group_by,
                "order_by": order_by,
                "limit": limit
            })
        elif action == "insert":
            # Wykrywanie wartości do wstawienia
            pass  # TODO: Implementacja insertów
        elif action == "update":
            # Wykrywanie wartości do aktualizacji i warunków
            pass  # TODO: Implementacja update'ów
        elif action == "delete":
            # Wykrywanie warunków usuwania
            conditions = self._detect_conditions(input_text, tables)
            query["conditions"] = conditions

        return query

    def _detect_action(self, text: str) -> str:
        """
        Wykrywa akcję SQL na podstawie tekstu.

        Args:
            text: Tekst wejściowy

        Returns:
            Nazwa akcji SQL
        """
        words = text.split()

        for action, keywords in self.actions.items():
            for keyword in keywords:
                if keyword in words:
                    return action

        # Domyślnie zakładamy SELECT
        return "select"

    def _detect_tables(self, text: str) -> List[str]:
        """
        Wykrywa tabele na podstawie tekstu.

        Args:
            text: Tekst wejściowy

        Returns:
            Lista nazw tabel
        """
        tables = []

        # Jeśli schemat jest dostępny, to używamy go do wykrywania tabel
        if self.schema and self.schema.tables:
            for table_name in self.schema.get_table_names():
                # Sprawdzamy czy nazwa tabeli znajduje się w tekście
                if table_name in text or any(syn in text for syn in self.schema.synonyms["tables"].get(table_name, [])):
                    tables.append(table_name)

            # Jeśli nie znaleziono żadnych tabel, próbujemy fuzzy matching
            if not tables:
                words = re.findall(r'\b\w+\b', text)
                for word in words:
                    if len(word) > 3:  # Ignoruj krótkie słowa
                        match = self.schema.find_table(word)
                        if match and match not in tables:
                            tables.append(match)

        return tables

    def _detect_columns(self, text: str, tables: List[str]) -> Dict[str, List[str]]:
        """
        Wykrywa kolumny na podstawie tekstu i tabel.

        Args:
            text: Tekst wejściowy
            tables: Lista tabel

        Returns:
            Słownik z kolumnami pogrupowanymi według tabel
        """
        columns = {table: [] for table in tables}
        all_columns = []  # Kolumny bez przypisanej tabeli

        # Wykrywanie funkcji agregujących
        aggregations = []
        for agg_key, agg_func in self.aggregations.items():
            if agg_key in text:
                # Znajdź słowo następujące po funkcji agregującej
                pattern = rf'{agg_key}\s+(\w+)'
                matches = re.finditer(pattern, text)
                for match in matches:
                    col_name = match.group(1)
                    aggregations.append((agg_func, col_name))

        # Jeśli mamy schemat, to próbujemy dopasować kolumny
        if self.schema and self.schema.tables:
            for table in tables:
                table_columns = self.schema.get_column_names(table)

                for col in table_columns:
                    # Sprawdzamy czy nazwa kolumny znajduje się w tekście
                    if col in text:
                        columns[table].append(col)
                    else:
                        # Sprawdzamy synonimy
                        col_key = f"{table}.{col}"
                        for synonym in self.schema.synonyms["columns"].get(col_key, []):
                            if synonym in text:
                                columns[table].append(col)
                                break

            # Jeśli nie znaleziono żadnych kolumn, próbujemy fuzzy matching
            if all(not cols for cols in columns.values()):
                words = re.findall(r'\b\w+\b', text)
                for word in words:
                    if len(word) > 3:  # Ignoruj krótkie słowa
                        for table in tables:
                            match = self.schema.find_column(table, word)
                            if match and match not in columns[table]:
                                columns[table].append(match)

        # Jeśli nie znaleziono kolumn dla tabel, dodaj wszystkie kolumny
        for table in tables:
            if not columns[table] and self.schema and table in self.schema.tables:
                columns[table] = list(self.schema.tables[table].keys())

        # Dodaj funkcje agregujące
        if aggregations:
            for agg_func, col_name in aggregations:
                # Sprawdź, do której tabeli należy kolumna
                for table in tables:
                    match = self.schema.find_column(table, col_name) if self.schema else None
                    if match:
                        columns[table].append(f"{agg_func}({match})")
                        break
                else:
                    # Jeśli nie znaleziono tabeli, dodaj do wszystkich kolumn
                    all_columns.append(f"{agg_func}({col_name})")

        # Jeśli nadal nie mamy kolumn, dodaj gwiazdkę
        if all(not cols for cols in columns.values()) and not all_columns:
            for table in tables:
                columns[table] = ["*"]

        return columns

    def _detect_conditions(self, text: str, tables: List[str]) -> List[Dict[str, Any]]:
        """
        Wykrywa warunki na podstawie tekstu i tabel.

        Args:
            text: Tekst wejściowy
            tables: Lista tabel

        Returns:
            Lista warunków
        """
        conditions = []

        # Wykrywanie prostych warunków: <kolumna> <operator> <wartość>
        for table in tables:
            if not self.schema:
                continue

            columns = self.schema.get_column_names(table)
            for col in columns:
                # Sprawdzamy różne wariacje warunku
                col_variants = [col] + self.schema.synonyms["columns"].get(f"{table}.{col}", [])

                for col_var in col_variants:

                    # Wzorzec: <wartość> <operator> <kolumna>
                    for op_key, op_val in self.operators.items():
                        pattern = rf'(["\']([^"\']+)["\']|(\d+))\s+{re.escape(op_key)}\s+{col_var}'
                        matches = re.finditer(pattern, text)
                        for match in matches:
                            value = match.group(2) or match.group(3)
                            conditions.append({
                                "table": table,
                                "column": col,
                                "operator": op_val,
                                "value": value
                            })

        # Wykrywanie specjalnych warunków (przedziały, IN, LIKE, itp.)
        for table in tables:
            if not self.schema:
                continue

            columns = self.schema.get_column_names(table)
            for col in columns:
                col_type = self.schema.get_column_type(table, col)

                # Wykrywanie warunków LIKE dla tekstów
                if col_type and "CHAR" in col_type.upper() or "TEXT" in col_type.upper() or "VARCHAR" in col_type.upper():
                    pattern = rf'(zawiera|contains|like|podobne do)\s+["\']([^"\']+)["\']'
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        value = match.group(2)
                        conditions.append({
                            "table": table,
                            "column": col,
                            "operator": "LIKE",
                            "value": f"%{value}%"
                        })

                # Wykrywanie warunków IN
                pattern = rf'{col}\s+(w|wśród|spośród|in|among)\s+\(([^)]+)\)'
                matches = re.finditer(pattern, text)
                for match in matches:
                    values = [v.strip(' "\'') for v in match.group(2).split(',')]
                    conditions.append({
                        "table": table,
                        "column": col,
                        "operator": "IN",
                        "values": values
                    })
                    conditions.append({
                        "table": table,
                        "column": col,
                        "operator": "IN",
                        "value": values
                    })

                    # Wykrywanie przedziałów (BETWEEN)
                pattern = rf'{col}\s+(między|between|od|from)\s+(\d+)\s+(do|i|and|to)\s+(\d+)'
                matches = re.finditer(pattern, text)
                for match in matches:
                    min_val = match.group(2)
                    max_val = match.group(4)
                    conditions.append({
                        "table": table,
                        "column": col,
                        "operator": "BETWEEN",
                        "value": (min_val, max_val)
                    })

                # Wykrywanie warunków dla dat
                if col_type and ("DATE" in col_type.upper() or "TIME" in col_type.upper()):
                    # Dzisiaj, wczoraj, itp.
                    date_patterns = [
                        (r'dzisiaj|today', "CURRENT_DATE"),
                        (r'wczoraj|yesterday', "DATE('now', '-1 day')"),
                        (r'(ostatni(e|ch)?|last)\s+(\d+)\s+(dni|day)', "DATE('now', '-\\3 day')"),
                        (r'(ostatni(e|ch)?|last)\s+(\d+)\s+(tygodni|tydzień|week)', "DATE('now', '-\\3 week')"),
                        (r'(ostatni(e|ch)?|last)\s+(\d+)\s+(miesięcy|miesiąc|month)', "DATE('now', '-\\3 month')"),
                        (r'(ostatni(e|ch)?|last)\s+(\d+)\s+(lat|rok|year)', "DATE('now', '-\\3 year')"),
                    ]

                    for pattern_tuple in date_patterns:
                        pattern_str, date_expr = pattern_tuple
                        if re.search(pattern_str, text):
                            match = re.search(r'(\d+)', pattern_str)
                            if match:
                                num = match.group(1)
                                date_expr = date_expr.replace('\\3', num)

                            conditions.append({
                                "table": table,
                                "column": col,
                                "operator": ">=",
                                "value": date_expr,
                                "is_expression": True
                            })

            return conditions

            def _detect_joins(self, text: str, tables: List[str]) -> List[Dict[str, Any]]:
                """
                Wykrywa joiny na podstawie tekstu i tabel.

                Args:
                    text: Tekst wejściowy
                    tables: Lista tabel

                Returns:
                    Lista joinów
                """
                joins = []

                # Jeśli mamy więcej niż jedną tabelę, szukamy relacji między nimi
                if len(tables) > 1 and self.schema:
                    for i in range(len(tables) - 1):
                        for j in range(i + 1, len(tables)):
                            from_table = tables[i]
                            to_table = tables[j]

                            # Szukanie ścieżki joinów
                            join_path = self.schema.find_joining_path(from_table, to_table)

                            if join_path:
                                joins.extend(join_path)

                return joins

            def _detect_group_by(self, text: str, tables: List[str]) -> Dict[str, List[str]]:
                """
                Wykrywa GROUP BY na podstawie tekstu i tabel.

                Args:
                    text: Tekst wejściowy
                    tables: Lista tabel

                Returns:
                    Słownik kolumn GROUP BY według tabel
                """
                result = {table: [] for table in tables}

                # Szukanie słów kluczowych
                group_patterns = [
                    r'grup(uj|owane|owana)(?: przez| by| według| po)? (\w+)',
                    r'group(?: by)? (\w+)',
                    r'według (\w+)',
                    r'pogrupowane (?:przez|po|według) (\w+)'
                ]

                for pattern in group_patterns:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        column_name = match.group(1)

                        # Znajdź odpowiednią tabelę i kolumnę
                        for table in tables:
                            if not self.schema:
                                result[table].append(column_name)
                                break

                            match_col = self.schema.find_column(table, column_name)
                            if match_col:
                                result[table].append(match_col)
                                break

                return result

            def _detect_order_by(self, text: str, tables: List[str]) -> List[Dict[str, Any]]:
                """
                Wykrywa ORDER BY na podstawie tekstu i tabel.

                Args:
                    text: Tekst wejściowy
                    tables: Lista tabel

                Returns:
                    Lista kolumn sortowania z kierunkiem
                """
                order_by = []

                # Szukanie słów kluczowych
                sort_patterns = [
                    r'sort(uj|owane|owana)(?: według| przez| by| po)? (\w+)',
                    r'order(?: by)? (\w+)',
                    r'uporządk(uj|owane|owana)(?: według| przez| po)? (\w+)'
                ]

                for pattern in sort_patterns:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        column_name = match.group(1)
                        direction = "ASC"  # Domyślny kierunek

                        # Sprawdź czy określono kierunek sortowania
                        for dir_key, dir_val in self.sort_directions.items():
                            if dir_key in text:
                                direction = dir_val
                                break

                        # Znajdź odpowiednią tabelę i kolumnę
                        for table in tables:
                            if not self.schema:
                                order_by.append({
                                    "table": table,
                                    "column": column_name,
                                    "direction": direction
                                })
                                break

                            match_col = self.schema.find_column(table, column_name)
                            if match_col:
                                order_by.append({
                                    "table": table,
                                    "column": match_col,
                                    "direction": direction
                                })
                                break

                return order_by

            def _detect_limit(self, text: str) -> Optional[int]:
                """
                Wykrywa LIMIT na podstawie tekstu.

                Args:
                    text: Tekst wejściowy

                Returns:
                    Wartość limitu lub None
                """
                # Wzorce dla limitów
                limit_patterns = [
                    r'(pierwszy(e|ch)?|pierwsze|first) (\d+)',
                    r'(górny(e|ch)?|górne|top) (\d+)',
                    r'(najlepszy(e|ch)?|najlepsze|best) (\d+)',
                    r'limit (\d+)',
                    r'ogranicz do (\d+)',
                    r'pokaż (\d+)',
                    r'wyświetl (\d+)',
                    r'(\d+) (pierwszy(e|ch)?|pierwsze|first)',
                    r'(\d+) (górny(e|ch)?|górne|top)',
                    r'(\d+) (najlepszy(e|ch)?|najlepsze|best)',
                ]

                for pattern in limit_patterns:
                    match = re.search(pattern, text)
                    if match:
                        try:
                            limit_value = int(match.group(1) if match.group(1).isdigit() else match.group(2) if len(
                                match.groups()) >= 2 and match.group(2).isdigit() else match.group(3))
                            return limit_value
                        except (ValueError, IndexError):
                            pass

                return None

        class SQLTranslator(AbstractTranslator):
            """
            Translator poleceń SQL z formatu pośredniego na zapytania SQL.
            """

            def __init__(self, dialect: str = "sqlite"):
                """
                Inicjalizuje translator SQL.

                Args:
                    dialect: Dialekt SQL (sqlite, mysql, postgresql)
                """
                self.dialect = dialect.lower()

            def translate(self, parsed_data: Dict[str, Any]) -> str:
                """
                Tłumaczy sparsowane dane na zapytanie SQL.

                Args:
                    parsed_data: Dane po parsowaniu

                Returns:
                    Zapytanie SQL
                """
                action = parsed_data.get("action", "select")

                if action == "select":
                    return self._translate_select(parsed_data)
                elif action == "insert":
                    return self._translate_insert(parsed_data)
                elif action == "update":
                    return self._translate_update(parsed_data)
                elif action == "delete":
                    return self._translate_delete(parsed_data)
                else:
                    raise ValueError(f"Nieobsługiwana akcja SQL: {action}")

            def _translate_select(self, parsed_data: Dict[str, Any]) -> str:
                """
                Tłumaczy zapytanie SELECT.

                Args:
                    parsed_data: Sparsowane dane

                Returns:
                    Zapytanie SQL SELECT
                """
                tables = parsed_data.get("tables", [])
                columns = parsed_data.get("columns", {})
                conditions = parsed_data.get("conditions", [])
                joins = parsed_data.get("joins", [])
                group_by = parsed_data.get("group_by", {})
                order_by = parsed_data.get("order_by", [])
                limit = parsed_data.get("limit")

                # Budowanie listy kolumn do wyboru
                select_parts = []

                # Jeśli są kolumny dla tabel
                for table in tables:
                    table_columns = columns.get(table, ["*"])
                    for col in table_columns:
                        if col == "*":
                            select_parts.append(f"{table}.*")
                        else:
                            # Obsługa funkcji agregujących
                            if "(" in col and ")" in col:
                                select_parts.append(f"{col}")
                            else:
                                select_parts.append(f"{table}.{col}")

                # Sprawdź czy są jakieś kolumny
                if not select_parts:
                    select_parts = ["*"]

                # Budowanie części FROM
                from_clause = f"{tables[0]}" if tables else ""

                # Budowanie części JOIN
                join_clauses = []
                processed_tables = set([tables[0]]) if tables else set()

                for join in joins:
                    from_table = join.get("from_table")
                    from_column = join.get("from_column")
                    to_table = join.get("to_table")
                    to_column = join.get("to_column")

                    if from_table in processed_tables and to_table not in processed_tables:
                        join_clauses.append(f"JOIN {to_table} ON {from_table}.{from_column} = {to_table}.{to_column}")
                        processed_tables.add(to_table)
                    elif to_table in processed_tables and from_table not in processed_tables:
                        join_clauses.append(f"JOIN {from_table} ON {to_table}.{to_column} = {from_table}.{from_column}")
                        processed_tables.add(from_table)

                # Dodawanie pozostałych tabel jako CROSS JOIN jeśli nie ma relacji
                for table in tables:
                    if table not in processed_tables:
                        if processed_tables:  # Jeśli już mamy jakieś tabele
                            join_clauses.append(f"CROSS JOIN {table}")
                        processed_tables.add(table)

                # Budowanie części WHERE
                where_conditions = []

                for cond in conditions:
                    table = cond.get("table")
                    column = cond.get("column")
                    operator = cond.get("operator")
                    value = cond.get("value")
                    is_expression = cond.get("is_expression", False)

                    if is_expression:
                        where_conditions.append(f"{table}.{column} {operator} {value}")
                    elif operator == "IN":
                        values_str = ", ".join([f"'{v}'" if not v.isdigit() else v for v in value])
                        where_conditions.append(f"{table}.{column} IN ({values_str})")
                    elif operator == "BETWEEN":
                        min_val, max_val = value
                        where_conditions.append(f"{table}.{column} BETWEEN {min_val} AND {max_val}")
                    elif operator == "LIKE":
                        where_conditions.append(f"{table}.{column} LIKE '{value}'")
                    else:
                        # Sprawdź czy wartość jest liczbą
                        if isinstance(value, str) and value.isdigit():
                            where_conditions.append(f"{table}.{column} {operator} {value}")
                        else:
                            where_conditions.append(f"{table}.{column} {operator} '{value}'")

                # Budowanie części GROUP BY
                group_by_clauses = []

                for table, cols in group_by.items():
                    for col in cols:
                        group_by_clauses.append(f"{table}.{col}")

                # Budowanie części ORDER BY
                order_by_clauses = []

                for order in order_by:
                    table = order.get("table")
                    column = order.get("column")
                    direction = order.get("direction", "ASC")
                    order_by_clauses.append(f"{table}.{column} {direction}")

                # Składanie zapytania
                query_parts = [f"SELECT {', '.join(select_parts)}"]

                if from_clause:
                    query_parts.append(f"FROM {from_clause}")

                if join_clauses:
                    query_parts.append(" ".join(join_clauses))

                if where_conditions:
                    query_parts.append(f"WHERE {' AND '.join(where_conditions)}")

                if group_by_clauses:
                    query_parts.append(f"GROUP BY {', '.join(group_by_clauses)}")

                if order_by_clauses:
                    query_parts.append(f"ORDER BY {', '.join(order_by_clauses)}")

                if limit is not None:
                    query_parts.append(f"LIMIT {limit}")

                return " ".join(query_parts)

            def _translate_insert(self, parsed_data: Dict[str, Any]) -> str:
                """
                Tłumaczy zapytanie INSERT.

                Args:
                    parsed_data: Sparsowane dane

                Returns:
                    Zapytanie SQL INSERT
                """
                # TODO: Implementacja zapytań INSERT
                return "INSERT not implemented yet"

            def _translate_update(self, parsed_data: Dict[str, Any]) -> str:
                """
                Tłumaczy zapytanie UPDATE.

                Args:
                    parsed_data: Sparsowane dane

                Returns:
                    Zapytanie SQL UPDATE
                """
                # TODO: Implementacja zapytań UPDATE
                return "UPDATE not implemented yet"

                def _translate_delete(self, parsed_data: Dict[str, Any]) -> str:
                    """
                    Tłumaczy zapytanie DELETE.

                    Args:
                        parsed_data: Sparsowane dane

                    Returns:
                        Zapytanie SQL DELETE
                    """
                    tables = parsed_data.get("tables", [])
                    conditions = parsed_data.get("conditions", [])

                    if not tables:
                        raise ValueError("Brak tabeli do usunięcia danych")

                    # W SQLite i większości baz DELETE działa tylko na jednej tabeli
                    table = tables[0]

                    # Budowanie części WHERE
                    where_conditions = []

                    for cond in conditions:
                        cond_table = cond.get("table")
                        column = cond.get("column")
                        operator = cond.get("operator")
                        value = cond.get("value")
                        is_expression = cond.get("is_expression", False)

                        # Używamy tylko warunków pasujących do tabeli DELETE
                        if cond_table == table:
                            if is_expression:
                                where_conditions.append(f"{column} {operator} {value}")
                            elif operator == "IN":
                                values_str = ", ".join([f"'{v}'" if not v.isdigit() else v for v in value])
                                where_conditions.append(f"{column} IN ({values_str})")
                            elif operator == "BETWEEN":
                                min_val, max_val = value
                                where_conditions.append(f"{column} BETWEEN {min_val} AND {max_val}")
                            elif operator == "LIKE":
                                where_conditions.append(f"{column} LIKE '{value}'")
                            else:
                                # Sprawdź czy wartość jest liczbą
                                if isinstance(value, str) and value.isdigit():
                                    where_conditions.append(f"{column} {operator} {value}")
                                else:
                                    where_conditions.append(f"{column} {operator} '{value}'")

                    # Składanie zapytania
                    query_parts = [f"DELETE FROM {table}"]

                    if where_conditions:
                        query_parts.append(f"WHERE {' AND '.join(where_conditions)}")

                    return " ".join(query_parts)

            # Inicjalizacja modułu
            def initialize_module(connection=None) -> Tuple[SQLParser, SQLTranslator, SQLExecutor]:
                """
                Inicjalizuje moduł Text-to-SQL.

                Args:
                    connection: Opcjonalne połączenie do bazy danych

                Returns:
                    Krotka (parser, translator, executor)
                """
                # Utworzenie schematu jeśli mamy połączenie
                schema = None
                if connection:
                    schema = SQLSchema()
                    schema.load_from_connection(connection)

                # Utworzenie komponentów
                parser = SQLParser(schema)
                translator = SQLTranslator()
                executor = SQLExecutor(connection)

                return parser, translator, executor


