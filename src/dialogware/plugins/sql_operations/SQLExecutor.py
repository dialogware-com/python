
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

class SQLExecutor(AbstractExecutor):
    """
    Wykonawca operacji SQL.
    """

    def __init__(self, connection=None):
        """
        Inicjalizuje wykonawcę SQL.

        Args:
            connection: Połączenie do bazy danych (sqlite3, psycopg2, itp.)
        """
        self.connection = connection
        self.last_query = None
        self.last_result = None

    def set_connection(self, connection) -> None:
        """
        Ustawia połączenie do bazy danych.

        Args:
            connection: Połączenie do bazy danych
        """
        self.connection = connection

    def execute(self, query: str) -> Any:
        """
        Wykonuje zapytanie SQL.

        Args:
            query: Zapytanie SQL do wykonania

        Returns:
            Wynik zapytania (dane lub informacja o statusie)
        """
        if not self.connection:
            raise ValueError("Brak połączenia do bazy danych")

        self.last_query = query

        try:
            cursor = self.connection.cursor()
            cursor.execute(query)

            # Sprawdź rodzaj zapytania
            query_type = query.strip().upper().split()[0]

            if query_type == "SELECT":
                # Pobranie nazw kolumn
                column_names = [description[0] for description in cursor.description]

                # Pobranie wyników
                rows = cursor.fetchall()

                # Konwersja na listę słowników
                result = []
                for row in rows:
                    result.append({column_names[i]: value for i, value in enumerate(row)})

                self.last_result = result
                return result
            else:
                # Dla INSERT, UPDATE, DELETE zwracamy informację o liczbie zmodyfikowanych wierszy
                affected_rows = cursor.rowcount
                self.connection.commit()

                self.last_result = {"affected_rows": affected_rows}
                return {"affected_rows": affected_rows}
        except Exception as e:
            self.connection.rollback()
            error_message = str(e)
            self.last_result = {"error": error_message}
            raise

    def execute_script(self, script: str) -> Any:
        """
        Wykonuje skrypt SQL (wiele zapytań).

        Args:
            script: Skrypt SQL do wykonania

        Returns:
            Wynik ostatniego zapytania
        """
        if not self.connection:
            raise ValueError("Brak połączenia do bazy danych")

        self.last_query = script

        try:
            cursor = self.connection.cursor()
            cursor.executescript(script)
            self.connection.commit()

            return {"status": "success", "message": "Script executed successfully"}
        except Exception as e:
            self.connection.rollback()
            error_message = str(e)
            self.last_result = {"error": error_message}
            raise

    def to_dataframe(self) -> 'pd.DataFrame':
        """
        Konwertuje ostatni wynik na DataFrame pandas.

        Returns:
            DataFrame z wynikami ostatniego zapytania
        """
        if not self.last_result or not isinstance(self.last_result, list):
            raise ValueError("Brak wyników zapytania SELECT do konwersji")

        return pd.DataFrame(self.last_result)

    def get_table_schema(self, table_name: str) -> Dict[str, str]:
        """
        Pobiera schemat tabeli.

        Args:
            table_name: Nazwa tabeli

        Returns:
            Słownik kolumn i ich typów
        """
        if not self.connection:
            raise ValueError("Brak połączenia do bazy danych")

        try:
            cursor = self.connection.cursor()

            # Dla SQLite
            if isinstance(self.connection, sqlite3.Connection):
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = {}
                for row in cursor.fetchall():
                    column_name = row[1]
                    column_type = row[2]
                    columns[column_name] = column_type
                return columns
            else:
                # Inne bazy danych
                raise NotImplementedError("Obsługiwane jest tylko połączenie SQLite")
        except Exception as e:
            raise ValueError(f"Błąd podczas pobierania schematu tabeli: {str(e)}")

    def get_database_schema(self) -> SQLSchema:
        """
        Pobiera pełny schemat bazy danych.

        Returns:
            Obiekt SQLSchema z informacjami o schemacie bazy
        """
        schema = SQLSchema()
        schema.load_from_connection(self.connection)
        return schema

