import asyncio
import os
import sqlite3
from typing import List, Dict, Any

from dialogware import DialogWare
from dialogware.plugins.sql_operations import initialize_module


async def main():
    """
    Główna funkcja demonstrująca możliwości systemu DialogWare.
    """
    print("Inicjalizacja systemu DialogWare: Text-to-Software")
    system = DialogWare()

    # Przygotowanie przykładowej bazy danych
    setup_example_database()

    # Demonstracja operacji na plikach
    print("\n=== Demonstracja operacji na plikach ===")
    await demonstrate_file_operations(system)

    # Demonstracja operacji SQL
    print("\n=== Demonstracja operacji SQL ===")
    await demonstrate_sql_operations(system)

    # Demonstracja generowania kodu
    print("\n=== Demonstracja generowania kodu ===")
    await demonstrate_code_generation(system)

    # Demonstracja pipeline'ów
    print("\n=== Demonstracja pipeline'ów ===")
    await demonstrate_pipelines(system)

    # Demonstracja debugowania
    print("\n=== Demonstracja debugowania ===")
    await demonstrate_debugging(system)

    print("\nDemonstracja zakończona. Dziękujemy za wypróbowanie DialogWare: Text-to-Software!")


async def demonstrate_file_operations(system: DialogWare):
    """
    Demonstruje operacje na plikach.
    """
    # Tworzenie plików tymczasowych
    os.makedirs("example", exist_ok=True)
    with open("example/document1.txt", "w") as f:
        f.write("To jest przykładowy dokument 1")
    with open("example/document2.txt", "w") as f:
        f.write("To jest przykładowy dokument 2")
    with open("example/report.csv", "w") as f:
        f.write("id,name,value\n1,Product A,100\n2,Product B,200\n3,Product C,300")

    # Wyszukiwanie plików
    print("\nWyszukiwanie plików tekstowych:")
    result = system.process("znajdź wszystkie pliki tekstowe w katalogu example")
    print_result(result)

    # Wyświetlanie szczegółów plików
    print("\nWyświetlanie szczegółów plików:")
    result = system.process("wyświetl informacje o plikach w katalogu example")
    print_result(result)

    # Tworzenie katalogów
    print("\nTworzenie katalogu:")
    result = system.process("utwórz katalog example/backup")
    print_result(result)

    # Kopiowanie plików
    print("\nKopiowanie plików:")
    result = system.process("kopiuj example/document1.txt do example/backup")
    print_result(result)


async def demonstrate_sql_operations(system: DialogWare):
    """
    Demonstruje operacje SQL.
    """
    # Połączenie z bazą danych
    conn = sqlite3.connect("example.db")

    # Inicjalizacja modułu SQL
    parser, translator, executor = initialize_module(conn)
    system.register_parser("sql", parser)
    system.register_translator("sql", translator)
    system.register_executor("sql", executor)

    # Zapytania SQL
    print("\nWyświetlanie klientów:")
    result = system.process("pokaż wszystkich klientów", domain="sql")
    print(f"Zapytanie SQL: {result.sql}")
    print_result(result)

    print("\nWyświetlanie zamówień:")
    result = system.process("pokaż 5 najnowszych zamówień", domain="sql")
    print(f"Zapytanie SQL: {result.sql}")
    print_result(result)

    print("\nWyświetlanie szczegółów:")
    result = system.process("pokaż 3 najlepszych klientów z największą sumą zamówień", domain="sql")
    print(f"Zapytanie SQL: {result.sql}")
    print_result(result)


async def demonstrate_code_generation(system: DialogWare):
    """
    Demonstruje generowanie kodu.
    """
    # Konfiguracja generatora kodu
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Brak klucza API Anthropic. Ustaw zmienną środowiskową ANTHROPIC_API_KEY.")
        print("Pomijam demonstrację generowania kodu.")
        return

    await system.setup_code_generator(
        api_key=api_key,
        provider="anthropic",
        cache_dir="./cache"
    )

    # Generowanie prostej funkcji
    print("\nGenerowanie funkcji konwersji CSV do Excel:")
    code = await system.generate_function(
        name="convert_csv_to_excel",
        params=["file_path", "output_path=None"],
        description="Converts CSV file to Excel format with proper column formatting",
        examples=[("data.csv", "data.xlsx")],
        language="python"
    )

    print(code)

    # Generowanie bardziej złożonej funkcji
    print("\nGenerowanie funkcji analizy tekstu:")
    code = await system.generate_function(
        name="analyze_sentiment",
        params=["text"],
        description="Analyzes the sentiment of the given text and returns a score between -1 (negative) and 1 (positive)",
        examples=[
            ("I love this product, it's amazing!", 0.9),
            ("This is the worst experience ever.", -0.8),
            ("The product is fine, nothing special.", 0.1)
        ],
        language="python"
    )

    print(code)


async def demonstrate_pipelines(system: DialogWare):
    """
    Demonstruje tworzenie i użycie pipeline'ów.
    """
    # Tworzenie pipeline'u z opisu
    print("\nTworzenie pipeline'u z opisu:")
    pipeline_text = """
    1. Znajdź wszystkie pliki CSV w katalogu example
    2. Wybierz pliki większe niż 100 bajtów
    3. Skopiuj je do katalogu example/backup
    4. Wyświetl podsumowanie operacji
    """

    pipeline = system.create_pipeline(pipeline_text)
    print("Pipeline utworzony. Wykonuję...")

    result = pipeline.execute("start")
    print("Wynik wykonania pipeline'u:")
    print(result)


async def demonstrate_debugging(system: DialogWare):
    """
    Demonstruje narzędzia debugowania.
    """
    # Debugowanie procesu
    print("\nDebugowanie przetwarzania polecenia:")
    debug_result = system.debug_process("znajdź pliki tekstowe w katalogu example")
    debug_result.visualize()


def setup_example_database():
    """
    Przygotowuje przykładową bazę danych.
    """
    print("Przygotowanie przykładowej bazy danych...")

    # Usuń istniejącą bazę
    if os.path.exists("example.db"):
        os.remove("example.db")

    # Utwórz nową bazę
    conn = sqlite3.connect("example.db")
    cursor = conn.cursor()

    # Utwórz tabele
    cursor.execute("""
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT,
        registration_date TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        order_date TEXT,
        total_amount REAL,
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL,
        category TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        price REAL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)

    # Wstaw przykładowe dane
    customers = [
        (1, "Jan Kowalski", "jan@example.com", "2022-01-01"),
        (2, "Anna Nowak", "anna@example.com", "2022-01-15"),
        (3, "Piotr Wiśniewski", "piotr@example.com", "2022-02-01"),
        (4, "Maria Dąbrowska", "maria@example.com", "2022-02-15"),
        (5, "Adam Lewandowski", "adam@example.com", "2022-03-01")
    ]

    cursor.executemany(
        "INSERT INTO customers (id, name, email, registration_date) VALUES (?, ?, ?, ?)",
        customers
    )

    orders = [
        (1, 1, "2022-03-01", 150.0),
        (2, 1, "2022-03-15", 200.0),
        (3, 2, "2022-03-10", 100.0),
        (4, 3, "2022-03-20", 300.0),
        (5, 4, "2022-03-25", 250.0),
        (6, 5, "2022-03-30", 180.0),
        (7, 2, "2022-04-05", 220.0),
        (8, 3, "2022-04-10", 190.0),
        (9, 1, "2022-04-15", 240.0),
        (10, 4, "2022-04-20", 170.0)
    ]

    cursor.executemany(
        "INSERT INTO orders (id, customer_id, order_date, total_amount) VALUES (?, ?, ?, ?)",
        orders
    )

    products = [
        (1, "Laptop", 3000.0, "Elektronika"),
        (2, "Smartphone", 1500.0, "Elektronika"),
        (3, "Słuchawki", 200.0, "Akcesoria"),
        (4, "Klawiatura", 150.0, "Akcesoria"),
        (5, "Mysz", 100.0, "Akcesoria"),
        (6, "Monitor", 800.0, "Elektronika"),
        (7, "Tablet", 1200.0, "Elektronika"),
        (8, "Torba na laptopa", 120.0, "Akcesoria"),
        (9, "Ładowarka", 50.0, "Akcesoria"),
        (10, "Pendrive", 80.0, "Akcesoria")
    ]

    cursor.executemany(
        "INSERT INTO products (id, name, price, category) VALUES (?, ?, ?, ?)",
        products
    )

    order_items = [
        (1, 1, 3, 1, 200.0),
        (2, 1, 5, 1, 100.0),
        (3, 2, 1, 1, 3000.0),
        (4, 3, 2, 1, 1500.0),
        (5, 4, 6, 1, 800.0),
        (6, 5, 7, 1, 1200.0),
        (7, 6, 4, 2, 300.0),
        (8, 7, 10, 3, 240.0),
        (9, 8, 8, 2, 240.0),
        (10, 9, 9, 4, 200.0),
        (11, 10, 5, 2, 200.0)
    ]

    cursor.executemany(
        "INSERT INTO order_items (id, order_id, product_id, quantity, price) VALUES (?, ?, ?, ?, ?)",
        order_items
    )

    conn.commit()
    conn.close()

    print("Baza danych przygotowana.")


def print_result(result):
    """
    Wyświetla rezultat wykonania komendy.
    """
    if not result.success:
        print(f"Błąd: {result.error}")
        return

    data = result.data

    if isinstance(data, list):
        if len(data) > 0:
            if isinstance(data[0], dict):
                print_table(data)
            else:
                for item in data:
                    print(f"- {item}")
        else:
            print("(brak danych)")
    elif isinstance(data, dict):
        for key, value in data.items():
            print(f"{key}: {value}")
    else:
        print(data)


def print_table(data: List[Dict[str, Any]]):
    """
    Wyświetla dane w formie tabeli.

    Args:
        data: Lista słowników z danymi
    """
    if not data:
        print("(brak danych)")
        return

    # Pobierz klucze dla nagłówków
    headers = list(data[0].keys())

    # Oblicz szerokość każdej kolumny
    col_widths = {}
    for header in headers:
        col_widths[header] = len(str(header))
        for row in data:
            if header in row:
                col_widths[header] = max(col_widths[header], len(str(row[header])))

    # Wyświetl nagłówki
    header_row = " | ".join(h.ljust(col_widths[h]) for h in headers)
    print(header_row)
    print("-" * len(header_row))

    # Wyświetl dane
    for row in data:
        row_str = " | ".join(str(row.get(h, "")).ljust(col_widths[h]) for h in headers)
        print(row_str)


if __name__ == "__main__":
    asyncio.run(main())