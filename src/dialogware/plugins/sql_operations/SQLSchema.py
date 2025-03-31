# Continue from existing code...

class SQLSchema:
    """
    Klasa reprezentująca schemat bazy danych.
    """

    def __init__(self):
        self.tables: Dict[str, Dict[str, str]] = {}
        self.relationships: List[Dict[str, str]] = []
        self.synonyms: Dict[str, Dict[str, List[str]]] = {
            "tables": {},
            "columns": {}
        }

    def add_table(self, table_name: str, columns: Dict[str, str]) -> None:
        """
        Dodaje tabelę do schematu.

        Args:
            table_name: Nazwa tabeli
            columns: Słownik kolumn (nazwa: typ)
        """
        self.tables[table_name.lower()] = {k.lower(): v for k, v in columns.items()}

    def add_relationship(self, from_table: str, from_column: str,
                         to_table: str, to_column: str,
                         relationship_type: str = "many-to-one") -> None:
        """
        Dodaje relację między tabelami.

        Args:
            from_table: Tabela źródłowa
            from_column: Kolumna źródłowa
            to_table: Tabela docelowa
            to_column: Kolumna docelowa
            relationship_type: Typ relacji
        """
        self.relationships.append({
            "from_table": from_table.lower(),
            "from_column": from_column.lower(),
            "to_table": to_table.lower(),
            "to_column": to_column.lower(),
            "type": relationship_type
        })

    def add_table_synonym(self, table_name: str, synonym: str) -> None:
        """
        Dodaje synonim dla tabeli.

        Args:
            table_name: Nazwa tabeli
            synonym: Synonim
        """
        table_name = table_name.lower()
        synonym = synonym.lower()

        if table_name not in self.synonyms["tables"]:
            self.synonyms["tables"][table_name] = []

        if synonym not in self.synonyms["tables"][table_name]:
            self.synonyms["tables"][table_name].append(synonym)

    def add_column_synonym(self, table_name: str, column_name: str, synonym: str) -> None:
        """
        Dodaje synonim dla kolumny.

        Args:
            table_name: Nazwa tabeli
            column_name: Nazwa kolumny
            synonym: Synonim
        """
        table_name = table_name.lower()
        column_name = column_name.lower()
        synonym = synonym.lower()

        column_key = f"{table_name}.{column_name}"
        if column_key not in self.synonyms["columns"]:
            self.synonyms["columns"][column_key] = []

        if synonym not in self.synonyms["columns"][column_key]:
            self.synonyms["columns"][column_key].append(synonym)

    def get_table_names(self) -> List[str]:
        """
        Zwraca listę nazw tabel.

        Returns:
            Lista nazw tabel
        """
        return list(self.tables.keys())

    def get_column_names(self, table_name: str) -> List[str]:
        """
        Zwraca listę nazw kolumn dla tabeli.

        Args:
            table_name: Nazwa tabeli

        Returns:
            Lista nazw kolumn
        """
        table_name = table_name.lower()
        if table_name in self.tables:
            return list(self.tables[table_name].keys())
        return []

    def get_column_type(self, table_name: str, column_name: str) -> Optional[str]:
        """
        Zwraca typ kolumny.

        Args:
            table_name: Nazwa tabeli
            column_name: Nazwa kolumny

        Returns:
            Typ kolumny lub None, jeśli nie znaleziono
        """
        table_name = table_name.lower()
        column_name = column_name.lower()

        if table_name in self.tables and column_name in self.tables[table_name]:
            return self.tables[table_name][column_name]
        return None

    def find_table(self, name: str, threshold: float = 0.7) -> Optional[str]:
        """
        Znajduje tabelę na podstawie nazwy z dopasowaniem rozmytym.

        Args:
            name: Nazwa lub synonim do znalezienia
            threshold: Próg podobieństwa

        Returns:
            Nazwa znalezionej tabeli lub None
        """
        name = name.lower()

        # Dokładne dopasowanie
        if name in self.tables:
            return name

        # Sprawdzenie synonimów
        for table, synonyms in self.synonyms["tables"].items():
            if name in synonyms:
                return table

        # Dopasowanie rozmyte
        best_match = None
        best_ratio = 0

        for table in self.tables:
            ratio = SequenceMatcher(None, name, table).ratio()
            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = table

        for table, synonyms in self.synonyms["tables"].items():
            for synonym in synonyms:
                ratio = SequenceMatcher(None, name, synonym).ratio()
                if ratio > best_ratio and ratio >= threshold:
                    best_ratio = ratio
                    best_match = table

        return best_match

    def find_column(self, table_name: str, column_name: str, threshold: float = 0.7) -> Optional[str]:
        """
        Znajduje kolumnę w tabeli na podstawie nazwy z dopasowaniem rozmytym.

        Args:
            table_name: Nazwa tabeli
            column_name: Nazwa lub synonim kolumny
            threshold: Próg podobieństwa

        Returns:
            Nazwa znalezionej kolumny lub None
        """
        table_name = table_name.lower()
        column_name = column_name.lower()

        if table_name not in self.tables:
            return None

        # Dokładne dopasowanie
        if column_name in self.tables[table_name]:
            return column_name

        # Sprawdzenie synonimów
        column_key = f"{table_name}.{column_name}"
        for col_key, synonyms in self.synonyms["columns"].items():
            if column_key == col_key or column_name in synonyms:
                return col_key.split(".", 1)[1]

        # Dopasowanie rozmyte
        best_match = None
        best_ratio = 0

        for column in self.tables[table_name]:
            ratio = SequenceMatcher(None, column_name, column).ratio()
            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = column

        for col_key, synonyms in self.synonyms["columns"].items():
            if col_key.startswith(f"{table_name}."):
                for synonym in synonyms:
                    ratio = SequenceMatcher(None, column_name, synonym).ratio()
                    if ratio > best_ratio and ratio >= threshold:
                        best_ratio = ratio
                        best_match = col_key.split(".", 1)[1]

        return best_match

    def find_joining_path(self, from_table: str, to_table: str) -> List[Dict[str, str]]:
        """
        Znajduje ścieżkę JOIN między tabelami.

        Args:
            from_table: Tabela początkowa
            to_table: Tabela końcowa

        Returns:
            Lista kroków JOINa
        """
        from_table = from_table.lower()
        to_table = to_table.lower()

        # Bezpośrednie połączenie
        for rel in self.relationships:
            if (rel["from_table"] == from_table and rel["to_table"] == to_table) or \
                    (rel["from_table"] == to_table and rel["to_table"] == from_table):
                return [{
                    "from_table": rel["from_table"],
                    "from_column": rel["from_column"],
                    "to_table": rel["to_table"],
                    "to_column": rel["to_column"]
                }]

        # TODO: Implementacja znajdowania wielostopniowych połączeń
        # Pominięte dla uproszczenia

        return []

    def load_from_connection(self, connection) -> None:
        """
        Ładuje schemat z połączenia bazodanowego.

        Args:
            connection: Połączenie do bazy danych (sqlite3, psycopg2, itp.)
        """
        if isinstance(connection, sqlite3.Connection):
            self._load_from_sqlite(connection)
        else:
            raise NotImplementedError("Obsługiwane jest tylko połączenie SQLite")

    def _load_from_sqlite(self, connection: sqlite3.Connection) -> None:
        """
        Ładuje schemat z połączenia SQLite.

        Args:
            connection: Połączenie SQLite
        """
        cursor = connection.cursor()

        # Pobranie listy tabel
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]

        for table_name in tables:
            # Pobranie informacji o kolumnach
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = {}
            for row in cursor.fetchall():
                column_name = row[1]
                column_type = row[2]
                columns[column_name] = column_type

            self.add_table(table_name, columns)

            # Automatyczne dodanie synonimów dla nazw tabel i kolumn
            self._add_automatic_synonyms(table_name, columns)

        # Wykrywanie relacji na podstawie nazw kolumn
        self._detect_relationships()

    def _add_automatic_synonyms(self, table_name: str, columns: Dict[str, str]) -> None:
        """
        Dodaje automatyczne synonimy dla tabel i kolumn.

        Args:
            table_name: Nazwa tabeli
            columns: Słownik kolumn
        """
        # Synonimy dla tabeli
        if "_" in table_name:
            self.add_table_synonym(table_name, table_name.replace("_", " "))

        # Standardowe transformacje nazw tabel (liczba pojedyncza <-> mnoga)
        if table_name.endswith("s"):
            self.add_table_synonym(table_name, table_name[:-1])  # customers -> customer
        else:
            self.add_table_synonym(table_name, f"{table_name}s")  # customer -> customers

        # Synonimy dla kolumn
        for column_name in columns:
            if "_" in column_name:
                self.add_column_synonym(table_name, column_name, column_name.replace("_", " "))

            # Standardowe prefiksy/sufiksy
            if column_name.startswith("id_"):
                self.add_column_synonym(table_name, column_name, column_name[3:])
            if column_name.endswith("_id"):
                self.add_column_synonym(table_name, column_name, column_name[:-3])

    def _detect_relationships(self) -> None:
        """
        Wykrywa relacje między tabelami na podstawie nazw kolumn.
        """
        # Proste wykrywanie na podstawie konwencji nazewniczych
        for table_name, columns in self.tables.items():
            for column_name in columns:
                # Szukanie kolumn typu _id lub zawierających _id_
                if column_name.endswith("_id") or "_id_" in column_name:
                    # Ekstrakcja nazwy docelowej tabeli
                    if column_name.endswith("_id"):
                        target_table = column_name[:-3]
                    else:
                        parts = column_name.split("_id_")
                        target_table = parts[1]

                    # Sprawdź czy tabela istnieje
                    if target_table in self.tables:
                        # Dodaj relację
                        self.add_relationship(
                            table_name, column_name,
                            target_table, "id",
                            "many-to-one"
                        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Konwertuje schemat do formatu słownika.

        Returns:
            Słownik reprezentujący schemat
        """
        return {
            "tables": self.tables,
            "relationships": self.relationships,
            "synonyms": self.synonyms
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SQLSchema':
        """
        Tworzy schemat z słownika.

        Args:
            data: Słownik z danymi schematu

        Returns:
            Obiekt schematu
        """
        schema = cls()
        schema.tables = data.get("tables", {})
        schema.relationships = data.get("relationships", [])
        schema.synonyms = data.get("synonyms", {"tables": {}, "columns": {}})
        return schema

    def save_to_file(self, file_path: str) -> None:
        """
        Zapisuje schemat do pliku JSON.

        Args:
            file_path: Ścieżka do pliku
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, file_path: str) -> 'SQLSchema':
        """
        Ładuje schemat z pliku JSON.

        Args:
            file_path: Ścieżka do pliku

        Returns:
            Obiekt schematu
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

