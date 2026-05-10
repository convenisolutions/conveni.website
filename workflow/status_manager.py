"""
Kandidaten-Statusverwaltung – trackt den Bearbeitungsfortschritt jedes Kandidaten.
Status wird in workflow/status.json gespeichert und vom Dashboard eingelesen.

Verwendung:
  python status_manager.py --liste
  python status_manager.py --liste kandidaten_vorlage.csv
  python status_manager.py --setze "Nguyen Thi Lan" kurs_laeuft
  python status_manager.py --setze "Nguyen Thi Lan" kurs_laeuft --notiz "VHS München, startet 12.05."
  python status_manager.py --verlauf "Nguyen Thi Lan"
  python status_manager.py --zuruecksetzen "Nguyen Thi Lan"
"""

import json
import sys
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime, date

STATUS_DATEI = Path(__file__).parent / "status.json"

# Reihenfolge definiert den Workflow-Fortschritt
STATUSWERTE: dict[str, dict] = {
    "neu":                {"label": "Neu aufgenommen",               "farbe": "grau",   "schritt": 0},
    "kontakt":            {"label": "Erstkontakt erfolgt",           "farbe": "blau",   "schritt": 1},
    "dokumente_eingereicht": {"label": "Unterlagen vollständig",     "farbe": "blau",   "schritt": 2},
    "antrag_gestellt":    {"label": "Förderantrag eingereicht",      "farbe": "blau",   "schritt": 3},
    "einstufungstest":    {"label": "Einstufungstest absolviert",    "farbe": "blau",   "schritt": 4},
    "kurs_genehmigt":     {"label": "Kurs genehmigt / zugelassen",  "farbe": "orange", "schritt": 5},
    "kurs_laeuft":        {"label": "Kurs läuft",                   "farbe": "orange", "schritt": 6},
    "kurs_abgeschlossen": {"label": "Kurs abgeschlossen ✓",         "farbe": "gruen",  "schritt": 7},
    "anerkennung_laufend":{"label": "Anerkennungsverfahren läuft",  "farbe": "orange", "schritt": 5},
    "anerkennung_fertig": {"label": "Berufsanerkennung erhalten ✓", "farbe": "gruen",  "schritt": 8},
    "ne_beantragt":       {"label": "NE beantragt",                 "farbe": "orange", "schritt": 8},
    "ne_erhalten":        {"label": "Niederlassungserlaubnis ✓",    "farbe": "gruen",  "schritt": 9},
    "vermittelt":         {"label": "Erfolgreich vermittelt ✓",     "farbe": "gruen",  "schritt": 10},
    "abgebrochen":        {"label": "Abgebrochen",                  "farbe": "rot",    "schritt": -1},
    "pausiert":           {"label": "Pausiert",                     "farbe": "grau",   "schritt": -1},
}

MAX_SCHRITT = 10


def _kandidat_key(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def _lade_status() -> dict:
    if STATUS_DATEI.exists():
        return json.loads(STATUS_DATEI.read_text(encoding="utf-8"))
    return {}


def _speichere_status(daten: dict):
    STATUS_DATEI.write_text(
        json.dumps(daten, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )


def status_holen(name: str) -> dict | None:
    """Gibt den aktuellen Status-Eintrag für einen Kandidaten zurück."""
    return _lade_status().get(_kandidat_key(name))


def status_setzen(name: str, status: str, notiz: str = "") -> dict:
    """Setzt den Status eines Kandidaten und schreibt ihn in die status.json."""
    if status not in STATUSWERTE:
        print(f"Fehler: Unbekannter Status '{status}'")
        print(f"Gültige Werte: {', '.join(STATUSWERTE.keys())}")
        sys.exit(1)

    daten = _lade_status()
    key = _kandidat_key(name)
    heute = date.today().isoformat()

    eintrag = daten.get(key, {
        "name": name,
        "verlauf": [],
    })

    verlauf_eintrag = {
        "status": status,
        "label": STATUSWERTE[status]["label"],
        "datum": heute,
        "notiz": notiz,
    }

    eintrag["aktuell"] = status
    eintrag["aktuell_label"] = STATUSWERTE[status]["label"]
    eintrag["zuletzt_geaendert"] = heute
    eintrag["notiz"] = notiz
    eintrag["verlauf"] = eintrag.get("verlauf", []) + [verlauf_eintrag]

    daten[key] = eintrag
    _speichere_status(daten)
    return eintrag


def status_initialisieren(kandidaten_csv: str | None = None):
    """Legt 'neu'-Einträge für alle Kandidaten an, die noch keinen Status haben."""
    eingabe = Path(kandidaten_csv) if kandidaten_csv else Path(__file__).parent / "kandidaten_vorlage.csv"
    df = pd.read_csv(eingabe) if eingabe.suffix == ".csv" else pd.read_excel(eingabe)
    daten = _lade_status()
    neu = 0
    for _, zeile in df.iterrows():
        name = f"{zeile['vorname']} {zeile['nachname']}"
        key = _kandidat_key(name)
        if key not in daten:
            daten[key] = {
                "name": name,
                "aktuell": "neu",
                "aktuell_label": STATUSWERTE["neu"]["label"],
                "zuletzt_geaendert": date.today().isoformat(),
                "notiz": "",
                "verlauf": [{"status": "neu", "label": "Neu aufgenommen",
                             "datum": date.today().isoformat(), "notiz": "Automatisch initialisiert"}],
            }
            neu += 1
    _speichere_status(daten)
    if neu:
        print(f"  {neu} neue Kandidaten initialisiert.")
    return daten


def get_fortschritt(status: str) -> int:
    """Gibt den Fortschritt in % zurück (0–100)."""
    schritt = STATUSWERTE.get(status, {}).get("schritt", 0)
    if schritt < 0:
        return 0
    return round((schritt / MAX_SCHRITT) * 100)


def _liste_anzeigen(kandidaten_csv: str | None = None):
    daten = status_initialisieren(kandidaten_csv)
    if not daten:
        print("Keine Kandidaten mit Status gefunden.")
        return

    print(f"\n{'Kandidat':<30} {'Status':<35} {'Fortschritt':<15} {'Notiz'}")
    print("-" * 90)
    for key, eintrag in sorted(daten.items(), key=lambda x: x[1].get("zuletzt_geaendert", ""), reverse=True):
        status = eintrag.get("aktuell", "neu")
        fortschritt = get_fortschritt(status)
        balken = "█" * (fortschritt // 10) + "░" * (10 - fortschritt // 10)
        print(
            f"{eintrag['name']:<30} "
            f"{STATUSWERTE.get(status, {}).get('label', status):<35} "
            f"{balken} {fortschritt:>3}%  "
            f"{eintrag.get('notiz', '')[:30]}"
        )
    print()


def _verlauf_anzeigen(name: str):
    daten = _lade_status()
    key = _kandidat_key(name)
    eintrag = daten.get(key)
    if not eintrag:
        print(f"Kein Status-Eintrag gefunden für: {name}")
        return
    print(f"\nStatusverlauf: {eintrag['name']}")
    print("-" * 60)
    for v in eintrag.get("verlauf", []):
        print(f"  {v['datum']}  {v['label']:<35}  {v.get('notiz', '')}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Kandidaten-Statusverwaltung")
    parser.add_argument("--liste", nargs="?", const=True, metavar="CSV",
                        help="Alle Kandidaten mit Status anzeigen (optional: Pfad zur CSV)")
    parser.add_argument("--setze", nargs=2, metavar=("NAME", "STATUS"),
                        help="Status setzen: --setze 'Vorname Nachname' status_wert")
    parser.add_argument("--notiz", default="", help="Notiz zum Statuswechsel")
    parser.add_argument("--verlauf", metavar="NAME", help="Statusverlauf eines Kandidaten")
    parser.add_argument("--zuruecksetzen", metavar="NAME", help="Status eines Kandidaten auf 'neu' zurücksetzen")
    parser.add_argument("--statuswerte", action="store_true", help="Alle gültigen Statuswerte anzeigen")
    args = parser.parse_args()

    if args.statuswerte:
        print("\nGültige Statuswerte:")
        for k, v in STATUSWERTE.items():
            print(f"  {k:<25} → {v['label']}")
        print()
        return

    if args.liste is not None:
        csv_pfad = args.liste if isinstance(args.liste, str) else None
        _liste_anzeigen(csv_pfad)
        return

    if args.setze:
        name, status = args.setze
        eintrag = status_setzen(name, status, args.notiz)
        print(f"  ✓ Status gesetzt: {eintrag['name']} → {eintrag['aktuell_label']}")
        if args.notiz:
            print(f"    Notiz: {args.notiz}")
        return

    if args.verlauf:
        _verlauf_anzeigen(args.verlauf)
        return

    if args.zuruecksetzen:
        status_setzen(args.zuruecksetzen, "neu", "Manuell zurückgesetzt")
        print(f"  ✓ Status zurückgesetzt: {args.zuruecksetzen}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
