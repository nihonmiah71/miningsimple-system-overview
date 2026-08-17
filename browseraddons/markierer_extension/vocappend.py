import os

def verarbeite_tsv(tsv_pfad, ziel_pfad):
    # 1. Read words from the TSV file
    woerter = []
    with open(tsv_pfad, 'r', encoding='utf-8') as f:
        for zeile in f:
            # Removes line breaks and whitespace at the beginning/end of the line
            wort = zeile.strip()
            # Only add if the line is not empty (e.g., the header line "Word" or blank lines)
            if wort:
                woerter.append(wort)
    
    if not woerter:
        print("No words found in the TSV file.")
        return

    # 2. Create string: Each word gets a "@" prefix
    # Example: ['A', 'B'] becomes "@A@B"
    ergebnis_string = "".join(f"@{wort}" for wort in woerter)
    
    # 3. Append seamlessly to the target file ('a' stands for append)
    # Since we use 'write()' and do not add a line break,
    # the string is appended seamlessly to the end of the file.
    with open(ziel_pfad, 'a', encoding='utf-8') as f:
        f.write(ergebnis_string)

    print(f"Successfully appended {len(woerter)} words seamlessly to '{ziel_pfad}'.")

# Define paths
tsv_datei = "extracted_fields1.tsv"
ziel_datei = "vocliste.txt"

# Run program
if __name__ == "__main__":
    # If the TSV file is in the same folder as the script, it will be found this way
    verarbeite_tsv(tsv_datei, ziel_datei)