"""Simulerar att en artikel säljs på en specifik lagerplats i grossistens
varuhus, genom att direkt uppdatera lagerstatus-fältet i lager.dat (fast
breddformat). Detta är INTE en del av agenten - det representerar "det
andra systemet" (grossistens riktiga försäljningssystem) som ändrar
datan agenten senare läser.

Fältpositioner (se lager_copybook.txt):
  artikelnummer: 0-10
  namn:          10-45
  lagerstatus:   45-51
  kategori:      51-66
  plats:         66-81
"""
import sys

def sell_article(filepath, artikelnummer, plats, quantity):
    with open(filepath, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        an = line[0:10].strip()
        line_plats = line[66:81].strip()
        if an == artikelnummer and line_plats == plats:
            current_stock = int(line[45:51])
            new_stock = max(0, current_stock - quantity)
            new_line = line[0:45] + str(new_stock).rjust(6, "0") + line[51:]
            lines[i] = new_line
            with open(filepath, "w") as f:
                f.writelines(lines)
            print(f"Sålde {quantity} st av {artikelnummer} i {plats}: lagerstatus {current_stock} -> {new_stock}")
            return
    print(f"Artikel {artikelnummer} i {plats} hittades inte")

if __name__ == "__main__":
    filepath = "lager.dat"
    artikelnummer = sys.argv[1] if len(sys.argv) > 1 else "ART-00004"
    plats = sys.argv[2] if len(sys.argv) > 2 else "Tallmossen"
    quantity = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    sell_article(filepath, artikelnummer, plats, quantity)
