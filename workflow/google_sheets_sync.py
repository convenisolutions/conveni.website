"""
Google Sheets Direktanbindung – liest Kandidatendaten live aus Google Sheets.

EINRICHTUNG (einmalig, ca. 10 Minuten):
  Schritt 1: Google Cloud Console → console.cloud.google.com
             → Neues Projekt erstellen (z.B. "Conveni Workflow")
  Schritt 2: APIs & Dienste → Bibliothek → "Google Sheets API" → Aktivieren
  Schritt 3: APIs & Dienste → Anmeldedaten
             → Dienstkonto erstellen → Name: "conveni-workflow"
             → Schlüssel → Neuen Schlüssel erstellen → JSON → Herunterladen
             → Datei umbenennen in: credentials.json → in diesen Ordner legen
  Schritt 4: Google Sheet öffnen → Freigeben → E-Mail des Dienstkontos einfügen
             (steht in credentials.json unter "client_email") → Lesezugriff
  Schritt 5: Sheet-ID aus der URL kopieren:
             https://docs.google.com/spreadsheets/d/HIER_STEHT_DIE_ID/edit

VERWENDUNG:
  python google_sheets_sync.py --sheet-id DEINE_SHEET_ID
  python google_sheets_sync.py --sheet-id DEINE_SHEET_ID --blatt "Kandidaten"
  python google_sheets_sync.py --sheet-id DEINE_SHEET_ID --alle-scripts
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_VERFUEGBAR = True
except ImportError:
    GSPREAD_VERFUEGBAR = False

CREDENTIALS_DATEI = Path(__file__).parent / "credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# Mapping: Google-Sheets-Spaltenname → interner Feldname (Groß-/Kleinschreibung egal)
SPALTEN_MAPPING = {
    # Deutsch
    "nachname": "nachname",
    "name": "nachname",
    "vorname": "vorname",
    "geburtsdatum": "geburtsdatum",
    "geburtstag": "geburtsdatum",
    "geschlecht": "geschlecht",
    "nationalität": "nationalitaet",
    "nationalitaet": "nationalitaet",
    "staatsangehörigkeit": "nationalitaet",
    "aufenthaltstitel": "aufenthaltstitel",
    "aufenthaltstitel_gueltig_bis": "aufenthaltstitel_gueltig_bis",
    "gültig bis": "aufenthaltstitel_gueltig_bis",
    "gueltig_bis": "aufenthaltstitel_gueltig_bis",
    "einreisedatum": "einreisedatum",
    "sprachniveau": "sprachniveau_aktuell",
    "sprachniveau_aktuell": "sprachniveau_aktuell",
    "deutschkenntnisse": "sprachniveau_aktuell",
    "alphabetisierung": "alphabetisierungsbedarf",
    "alphabetisierungsbedarf": "alphabetisierungsbedarf",
    "beschäftigt": "beschaeftigt",
    "beschaeftigt": "beschaeftigt",
    "arbeitgeber": "arbeitgeber",
    "arbeitgeber_größe": "arbeitgeber_groesse",
    "arbeitgeber_groesse": "arbeitgeber_groesse",
    "betriebsgröße": "arbeitgeber_groesse",
    "berufsfeld": "berufsfeld",
    "beruf": "berufsfeld",
    "tätigkeit": "berufsfeld",
    "qualifikation": "qualifikation_abschluss",
    "qualifikation_abschluss": "qualifikation_abschluss",
    "abschluss": "qualifikation_abschluss",
    "qualifikation_fach": "qualifikation_fach",
    "fachrichtung": "qualifikation_fach",
    "anerkennung": "anerkennungsverfahren",
    "anerkennungsverfahren": "anerkennungsverfahren",
    "anerkennungsstatus": "anerkennungsverfahren",
    "integrationskurs_verpflichtet": "integrationskurs_verpflichtet",
    "verpflichtet": "integrationskurs_verpflichtet",
    "email": "email",
    "e-mail": "email",
    "telefon": "telefon",
    "handynummer": "telefon",
}

PFLICHTFELDER = [
    "nachname", "vorname", "sprachniveau_aktuell", "aufenthaltstitel",
    "beschaeftigt", "berufsfeld", "anerkennungsverfahren",
]


def _prueffe_einrichtung() -> bool:
    if not GSPREAD_VERFUEGBAR:
        print("FEHLER: gspread nicht installiert.")
        print("  → pip install gspread google-auth")
        return False
    if not CREDENTIALS_DATEI.exists():
        print(f"FEHLER: credentials.json nicht gefunden in: {CREDENTIALS_DATEI.parent}")
        print("  → Einrichtungsanleitung: Lies die Kommentare am Anfang dieser Datei")
        print("  → Oder führe aus: python google_sheets_sync.py --setup-hilfe")
        return False
    return True


def _zeige_setup_hilfe():
    hilfe = """
╔══════════════════════════════════════════════════════════════╗
║          Google Sheets Einrichtung – Schritt für Schritt     ║
╚══════════════════════════════════════════════════════════════╝

Schritt 1: Google Cloud Project erstellen
  → https://console.cloud.google.com
  → "Neues Projekt" → Name: "Conveni Workflow" → Erstellen

Schritt 2: Google Sheets API aktivieren
  → APIs & Dienste → Bibliothek
  → Suche: "Google Sheets API" → Aktivieren

Schritt 3: Dienstkonto (Service Account) erstellen
  → APIs & Dienste → Anmeldedaten
  → + Anmeldedaten erstellen → Dienstkonto
  → Name: "conveni-workflow" → Erstellen und fortfahren → Fertig
  → Auf das Dienstkonto klicken → Tab "Schlüssel"
  → Schlüssel hinzufügen → Neuen Schlüssel erstellen → JSON
  → Datei wird heruntergeladen → umbenennen in: credentials.json
  → Datei hierher kopieren: workflow/credentials.json

Schritt 4: Google Sheet freigeben
  → Dein Google Sheet öffnen
  → Freigeben (oben rechts)
  → E-Mail-Adresse des Dienstkontos einfügen
    (steht in credentials.json unter "client_email")
  → Berechtigung: Betrachter (Leserechte reichen)
  → Senden

Schritt 5: Sheet-ID herausfinden
  → URL deines Sheets:
    https://docs.google.com/spreadsheets/d/HIER_IST_DIE_SHEET_ID/edit
  → Nur die ID kopieren (der lange String zwischen /d/ und /edit)

Schritt 6: Test
  → python google_sheets_sync.py --sheet-id DEINE_ID --test

╔══════════════════════════════════════════════════════════════╗
║  Spaltenbezeichnungen in deinem Sheet (Groß-/Klein egal):    ║
╠══════════════════════════════════════════════════════════════╣
║  nachname | vorname | geburtsdatum | geschlecht              ║
║  nationalität | aufenthaltstitel | gültig bis                ║
║  sprachniveau | alphabetisierung | beschäftigt               ║
║  arbeitgeber | betriebsgröße | berufsfeld | abschluss        ║
║  anerkennung | email | telefon                               ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(hilfe)


def _normalisiere_spalten(df):
    """Benennt Spalten anhand des Mappings um, ignoriert Groß-/Kleinschreibung."""
    import pandas as pd
    neue_namen = {}
    for spalte in df.columns:
        key = spalte.strip().lower()
        if key in SPALTEN_MAPPING:
            neue_namen[spalte] = SPALTEN_MAPPING[key]
    df = df.rename(columns=neue_namen)

    # Fehlende Pflichtfelder melden
    fehlend = [f for f in PFLICHTFELDER if f not in df.columns]
    if fehlend:
        print(f"  ⚠ Folgende Spalten fehlen oder haben unbekannte Namen: {fehlend}")
        print(f"    Vorhandene Spalten: {list(df.columns)}")

    # Optionale Felder mit Standardwerten auffüllen
    defaults = {
        "geburtsdatum": "",
        "geschlecht": "",
        "aufenthaltstitel_gueltig_bis": "",
        "einreisedatum": "",
        "alphabetisierungsbedarf": "nein",
        "arbeitgeber": "–",
        "arbeitgeber_groesse": "mittel",
        "qualifikation_abschluss": "",
        "qualifikation_fach": "",
        "integrationskurs_verpflichtet": "nein",
        "email": "",
        "telefon": "",
        "nationalitaet": "",
    }
    for feld, standard in defaults.items():
        if feld not in df.columns:
            df[feld] = standard
    return df


def lade_von_sheets(sheet_id: str, blattname: str | None = None) -> "pd.DataFrame":
    """Lädt Kandidatendaten direkt aus Google Sheets und gibt DataFrame zurück."""
    import pandas as pd

    if not _prueffe_einrichtung():
        sys.exit(1)

    print(f"  Verbinde mit Google Sheets (ID: {sheet_id[:20]}...)")
    creds = Credentials.from_service_account_file(str(CREDENTIALS_DATEI), scopes=SCOPES)
    client = gspread.authorize(creds)

    try:
        spreadsheet = client.open_by_key(sheet_id)
    except gspread.exceptions.SpreadsheetNotFound:
        print("FEHLER: Sheet nicht gefunden. Bitte prüfen:")
        print("  1. Sheet-ID korrekt?")
        print("  2. Sheet mit Dienstkonto-E-Mail geteilt?")
        sys.exit(1)

    if blattname:
        worksheet = spreadsheet.worksheet(blattname)
    else:
        worksheet = spreadsheet.get_worksheet(0)

    print(f"  Blatt geladen: '{worksheet.title}'")
    daten = worksheet.get_all_records(numericise_ignore=["all"])

    if not daten:
        print("FEHLER: Sheet ist leer oder hat keine Kopfzeile.")
        sys.exit(1)

    df = pd.DataFrame(daten)
    df = _normalisiere_spalten(df)
    df = df[df["nachname"].astype(str).str.strip() != ""]  # Leerzeilen entfernen
    print(f"  {len(df)} Kandidaten geladen")
    return df


def main():
    parser = argparse.ArgumentParser(description="Google Sheets → Conveni Workflow")
    parser.add_argument("--sheet-id", help="Google Sheets ID aus der URL", default=None)
    parser.add_argument("--blatt", help="Name des Tabellenblatts (Standard: erstes Blatt)", default=None)
    parser.add_argument("--alle-scripts", action="store_true", help="Alle Workflow-Scripts ausführen")
    parser.add_argument("--speichern-als", help="Lokale CSV-Kopie speichern unter diesem Namen", default=None)
    parser.add_argument("--setup-hilfe", action="store_true", help="Einrichtungsanleitung anzeigen")
    parser.add_argument("--test", action="store_true", help="Verbindung testen ohne Script auszuführen")
    args = parser.parse_args()

    if args.setup_hilfe:
        _zeige_setup_hilfe()
        return

    if not args.sheet_id:
        print("FEHLER: --sheet-id fehlt.")
        print("Verwendung: python google_sheets_sync.py --sheet-id DEINE_SHEET_ID")
        print("Hilfe:      python google_sheets_sync.py --setup-hilfe")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Google Sheets Sync – {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*60}\n")

    df = lade_von_sheets(args.sheet_id, args.blatt)

    # Optionale lokale CSV-Kopie
    if args.speichern_als:
        csv_pfad = Path(__file__).parent / args.speichern_als
        df.to_csv(csv_pfad, index=False)
        print(f"  ✓ Lokale CSV-Kopie gespeichert: {csv_pfad.name}")

    if args.test:
        print("\n  ✓ Verbindung erfolgreich! Sheet kann gelesen werden.")
        print(f"  Spalten: {list(df.columns)}")
        return

    # Temporäre CSV für andere Scripts
    tmp_csv = Path(__file__).parent / "_sheets_export_tmp.csv"
    df.to_csv(tmp_csv, index=False)

    scripts = [
        "generate_checklisten.py",
        "generate_uebersicht.py",
        "generate_kalender.py",
        "generate_formulare.py",
        "generate_arbeitgeber_mappe.py",
        "generate_partnerschulen_bericht.py",
        "generate_qualitaet_bericht.py",
        "generate_dokumente_bericht.py",
        "generate_monatsbericht.py",
        "fristenwächter.py",
    ]

    if args.alle_scripts:
        print(f"\n  Starte alle Workflow-Scripts mit {len(df)} Kandidaten...\n")
        for script in scripts:
            print(f"  → {script}")
            result = subprocess.run(
                [sys.executable, str(Path(__file__).parent / script), str(tmp_csv)],
                capture_output=False
            )
            if result.returncode != 0:
                print(f"  ⚠ {script} mit Fehler beendet")
    else:
        print(f"\n  Daten geladen. Nächste Schritte:")
        for script in scripts:
            print(f"  → python {script} {tmp_csv.name}")
        print(f"\n  Oder alles auf einmal:")
        print(f"  → python google_sheets_sync.py --sheet-id {args.sheet_id} --alle-scripts")

    tmp_csv.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
