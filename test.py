from dialogware import DialogWare

system = DialogWare()

# Znajdowanie plików
result = system.process("znajdź wszystkie pliki PDF większe niż 5MB w katalogu dokumenty")
for file in result.data:
    print(file)

# Wykonywanie złożonych operacji
result = system.process("znajdź duplikaty plików w katalogu projekty i przenieś je do katalog_duplikaty")
print(result.data)