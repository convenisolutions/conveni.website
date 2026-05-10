"""
Google Forms → CSV → Alle Berichte automatisch.

Einrichtung: python forms_sync.py --setup
Täglich:     python forms_sync.py
"""
import json
import csv
import sys
import subprocess
from pathlib import Path
from datetime import datetime

KONFIG_DATEI = Path(__file__).parent / "forms_config.json"
AUSGABE_CSV  = Path(__file__).parent / "kandidaten.csv"

# Mapping: Google Forms Spaltenname → interner Feldname
SPALTEN_MAPPING = {
    # Passe die linke Seite an deine Forms-Spaltennamen an
    "Nachname":                        "nachname",
    "Vorname":                         "vorname",
    "Geburtsdatum":                    "geburtsdatum",
    "Geschlecht":                      "geschlecht",
    "Nationalität":                    "nationalitaet",
    "Aufenthaltstitel":                "aufenthaltstitel",
    "Aufenthaltstitel gültig bis":     "aufenthaltstitel_gueltig_bis",
    "Einreisedatum":                   "einreisedatum",
    "Sprachniveau aktuell":            "sprachniveau_aktuell",
    "Alphabetisierungsbedarf":         "alphabetisierungsbedarf",
    "Beschäftigt":                     "beschaeftigt",
    "Arbeitgeber":                     "arbeitgeber",
    "Arbeitgeber Größe":               "arbeitgeber_groesse",
    "Berufsfeld":                      "berufsfeld",
    "Qualifikation / Abschluss":       "qualifikation_abschluss",
    "Qualifikation Fach":              "qualifikation_fach",
    "Anerkennungsverfahren":           "anerkennungsverfahren",
    "Integrationskurs verpflichtet":   "integrationskurs_verpflichtet",
    "E-Mail":                          "email",
    "Telefon":                         "telefon",
}


def konfig_einrichten():
    print("=== Google Forms Sync einrichten ===\n")
    print("So findest du die Spreadsheet-ID:")
    print("  1. Öffne dein Google Forms")
    print("  2. Klick auf 'Antworten' → grünes Tabellen-Icon (In Sheets öffnen)")
    print("  3. Die URL lautet: docs.google.com/spreadsheets/d/DEINE_ID/edit")
    print("  4. Kopiere DEINE_ID\n")
    print("Service Account (für automatischen Zugriff):")
    print("  1. console.cloud.google.com → Neues Projekt")
    print("  2. APIs → Google Sheets API aktivieren")
    print("  3. Anmeldedaten → Service Account erstellen")
    print("  4. JSON-Schlüssel herunterladen → als 'credentials.json' speichern")
    print("  5. credentials.json E-Mail-Adresse als Betrachter im Sheet freigeben\n")

    sheet_id = input("Spreadsheet-ID: ").strip()
    sheet_name = input("Tabellenblatt-Name [Formularantworten 1]: ").strip() or "Formularantworten 1"

    konfig = {"sheet_id": sheet_id, "sheet_name": sheet_name}
    with open(KONFIG_DATEI, "w") as f:
        json.dump(konfig, f, indent=2)
    print("\n✓ Konfiguration gespeichert.")
    print("Stelle sicher dass 'credentials.json' im workflow-Ordner liegt.")
    print("Test: python forms_sync.py --sync")


def sync_und_berichte(nur_sync=False):
    if not KONFIG_DATEI.exists():
        print("❌ Bitte zuerst: python forms_sync.py --setup")
        sys.exit(1)

    konfig = json.loads(KONFIG_DATEI.read_text())

    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("❌ Fehlend: pip install gspread google-auth")
        sys.exit(1)

    creds_datei = Path(__file__).parent / "credentials.json"
    if not creds_datei.exists():
        print("❌ credentials.json nicht gefunden. Siehe --setup.")
        sys.exit(1)

    print("→ Verbinde mit Google Sheets …")
    creds = Credentials.from_service_account_file(
        str(creds_datei),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(konfig["sheet_id"]).worksheet(konfig["sheet_name"])
    rows = sheet.get_all_records()

    if not rows:
        print("ℹ Keine Einträge im Sheet.")
        return

    # Spalten mappen
    ausgabe_zeilen = []
    for row in rows:
        zeile = {}
        for forms_name, intern in SPALTEN_MAPPING.items():
            zeile[intern] = row.get(forms_name, "")
        ausgabe_zeilen.append(zeile)

    # CSV schreiben
    felder = list(SPALTEN_MAPPING.values())
    with open(AUSGABE_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=felder)
        writer.writeheader()
        writer.writerows(ausgabe_zeilen)

    print(f"✓ {len(ausgabe_zeilen)} Kandidaten aus Google Forms geladen → kandidaten.csv")

    if nur_sync:
        return

    # Alle Berichte neu generieren
    print("→ Berichte werden regeneriert …")
    skripte = [
        ["python3", "status_manager.py",             "--liste"],
        ["python3", "dokumente_manager.py",          "--init-alle", str(AUSGABE_CSV)],
        ["python3", "generate_uebersicht.py",        str(AUSGABE_CSV)],
        ["python3", "generate_checklisten.py",       str(AUSGABE_CSV)],
        ["python3", "generate_dokumente_bericht.py", str(AUSGABE_CSV)],
        ["python3", "fristenwächter.py",             str(AUSGABE_CSV), "--html"],
    ]
    basis = Path(__file__).parent
    for cmd in skripte:
        result = subprocess.run(cmd, cwd=basis, capture_output=True, text=True)
        name = cmd[1]
        print(f"  {'✓' if result.returncode == 0 else '✗'} {name}")

    print(f"\n✓ Sync abgeschlossen – {datetime.now().strftime('%d.%m.%Y %H:%M')}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--setup" in args:
        konfig_einrichten()
    elif "--sync" in args:
        sync_und_berichte(nur_sync=True)
    else:
        sync_und_berichte()
