"""
Checklisten-Generator: Erzeugt pro Kandidat eine druckfertige HTML-Checkliste.
Führe zuerst check_foerderung.py aus oder rufe dieses Script direkt auf.
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from check_foerderung import pruefe_kandidat


def generiere_checklisten(eingabe_pfad: str | None = None, ausgabe_ordner: str = "output"):
    if eingabe_pfad is None:
        eingabe_pfad = Path(__file__).parent / "kandidaten_vorlage.csv"
    eingabe = Path(eingabe_pfad)

    if not eingabe.exists():
        print(f"Fehler: Datei nicht gefunden: {eingabe}")
        sys.exit(1)

    suffix = eingabe.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(eingabe)
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(eingabe)
    else:
        print("Fehler: Bitte CSV oder Excel-Datei angeben.")
        sys.exit(1)

    ausgabe = Path(__file__).parent / ausgabe_ordner
    ausgabe.mkdir(exist_ok=True)

    template_pfad = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_pfad)))
    template = env.get_template("checkliste.html")

    datum = datetime.now().strftime("%d.%m.%Y")
    generiert = []

    for _, zeile in df.iterrows():
        ergebnis = pruefe_kandidat(zeile)
        html = template.render(kandidat=ergebnis, datum=datum)

        dateiname = (
            f"{zeile['nachname'].lower()}_{zeile['vorname'].split()[0].lower()}_checkliste.html"
        )
        ausgabe_datei = ausgabe / dateiname
        ausgabe_datei.write_text(html, encoding="utf-8")
        generiert.append((ergebnis["name"], str(ausgabe_datei)))
        print(f"  ✓ Checkliste erstellt: {ausgabe_datei.name}")

    print(f"\n{len(generiert)} Checkliste(n) gespeichert in: {ausgabe.resolve()}")
    print("Tipp: Im Browser öffnen → Datei → Drucken → Als PDF speichern\n")
    return generiert


if __name__ == "__main__":
    eingabe = sys.argv[1] if len(sys.argv) > 1 else None
    ausgabe = sys.argv[2] if len(sys.argv) > 2 else "output"
    generiere_checklisten(eingabe, ausgabe)
