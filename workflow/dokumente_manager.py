"""
Dokumenten-Verwaltung: Trackt welche Unterlagen pro Kandidat vorhanden/fehlend sind.
Speichert in workflow/dokumente.json.

Verwendung:
  python dokumente_manager.py --init-alle kandidaten_vorlage.csv
  python dokumente_manager.py --liste
  python dokumente_manager.py --kandidat "Nguyen Thi Lan"
  python dokumente_manager.py --setze "Nguyen Thi Lan" reisepass vorhanden
  python dokumente_manager.py --setze "Nguyen Thi Lan" bamf_antrag angefordert --notiz "E-Mail 10.05."
"""

import json
import sys
import argparse
import pandas as pd
from pathlib import Path
from datetime import date

DOKUMENTE_DATEI = Path(__file__).parent / "dokumente.json"

DOKUMENT_TYPEN: dict[str, dict] = {
    "reisepass":           {"label": "Reisepass / Personalausweis",      "pflicht": True,  "fuer": "alle"},
    "aufenthaltstitel":    {"label": "Aufenthaltstitel (§ X AufenthG)",  "pflicht": True,  "fuer": "alle"},
    "meldebescheinigung":  {"label": "Meldebescheinigung",               "pflicht": True,  "fuer": "alle"},
    "lichtbild":           {"label": "Biometrisches Lichtbild",          "pflicht": True,  "fuer": "alle"},
    "lebenslauf":          {"label": "Lebenslauf (deutsch)",             "pflicht": True,  "fuer": "alle"},
    "qualifikationsnachweis": {"label": "Berufsqualifikation / Zeugnis", "pflicht": True,  "fuer": "alle"},
    "krankenversicherung": {"label": "Krankenversicherungsnachweis",     "pflicht": True,  "fuer": "alle"},
    "ab_bestaetigung":     {"label": "Arbeitgeberbestätigung (BSK)",     "pflicht": False, "fuer": "beschaeftigt"},
    "bamf_antrag":         {"label": "BAMF-Antrag (unterschrieben)",     "pflicht": False, "fuer": "foerderung"},
    "einstufungstest":     {"label": "Einstufungstest-Ergebnis",         "pflicht": False, "fuer": "foerderung"},
    "anerkennung_antrag":  {"label": "Anerkennungsantrag",               "pflicht": False, "fuer": "reglementiert"},
    "arbeitsvertrag":      {"label": "Arbeitsvertrag (Kopie)",           "pflicht": False, "fuer": "beschaeftigt"},
}

STATUS_WERTE = {
    "vorhanden":     {"label": "Vorhanden ✓",    "farbe": "gruen"},
    "fehlend":       {"label": "Fehlend",         "farbe": "rot"},
    "angefordert":   {"label": "Angefordert …",  "farbe": "orange"},
    "nicht_relevant":{"label": "Nicht relevant",  "farbe": "grau"},
}


def _kandidat_key(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def _lade_dokumente() -> dict:
    if DOKUMENTE_DATEI.exists():
        return json.loads(DOKUMENTE_DATEI.read_text(encoding="utf-8"))
    return {}


def _speichere_dokumente(daten: dict):
    DOKUMENTE_DATEI.write_text(
        json.dumps(daten, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )


def _erstelle_leeren_eintrag(name: str) -> dict:
    return {
        "name": name,
        "zuletzt_geaendert": date.today().isoformat(),
        "dokumente": {k: {"status": "fehlend", "notiz": "", "datum": ""} for k in DOKUMENT_TYPEN},
    }


def initialisiere_alle(kandidaten_csv: str | None = None):
    eingabe = Path(kandidaten_csv) if kandidaten_csv else Path(__file__).parent / "kandidaten_vorlage.csv"
    df = pd.read_csv(eingabe) if eingabe.suffix == ".csv" else pd.read_excel(eingabe)
    daten = _lade_dokumente()
    neu = 0
    for _, zeile in df.iterrows():
        name = f"{zeile['vorname']} {zeile['nachname']}"
        key = _kandidat_key(name)
        if key not in daten:
            daten[key] = _erstelle_leeren_eintrag(name)
            neu += 1
    _speichere_dokumente(daten)
    print(f"  {neu} neue Kandidaten-Einträge angelegt (gesamt: {len(daten)})")


def setze_dokument_status(name: str, dok_typ: str, status: str, notiz: str = ""):
    if dok_typ not in DOKUMENT_TYPEN:
        print(f"Fehler: Unbekannter Dokumenttyp '{dok_typ}'")
        print(f"Gültige Typen: {', '.join(DOKUMENT_TYPEN.keys())}")
        sys.exit(1)
    if status not in STATUS_WERTE:
        print(f"Fehler: Unbekannter Status '{status}'")
        print(f"Gültige Werte: {', '.join(STATUS_WERTE.keys())}")
        sys.exit(1)

    daten = _lade_dokumente()
    key = _kandidat_key(name)
    if key not in daten:
        daten[key] = _erstelle_leeren_eintrag(name)

    daten[key]["dokumente"][dok_typ] = {
        "status": status,
        "notiz": notiz,
        "datum": date.today().isoformat(),
    }
    daten[key]["zuletzt_geaendert"] = date.today().isoformat()
    _speichere_dokumente(daten)
    label = DOKUMENT_TYPEN[dok_typ]["label"]
    status_label = STATUS_WERTE[status]["label"]
    print(f"  ✓ {name}: {label} → {status_label}")


def hole_fehlende_dokumente(name: str) -> list[str]:
    daten = _lade_dokumente()
    eintrag = daten.get(_kandidat_key(name), {})
    fehlend = []
    for typ, dok in eintrag.get("dokumente", {}).items():
        if dok["status"] == "fehlend":
            fehlend.append(DOKUMENT_TYPEN[typ]["label"])
    return fehlend


def berechne_vollstaendigkeit(eintrag: dict) -> int:
    """Gibt den Vollständigkeitsgrad in % zurück (nur Pflicht-Dokumente)."""
    pflicht_typen = [k for k, v in DOKUMENT_TYPEN.items() if v["pflicht"]]
    vorhanden = sum(
        1 for t in pflicht_typen
        if eintrag.get("dokumente", {}).get(t, {}).get("status") == "vorhanden"
    )
    return round(vorhanden / len(pflicht_typen) * 100) if pflicht_typen else 0


def _liste_anzeigen():
    daten = _lade_dokumente()
    if not daten:
        print("Keine Dokument-Einträge. Bitte --init-alle ausführen.")
        return

    print(f"\n{'Kandidat':<28} {'Vollständig':>12}  {'Fehlend'}")
    print("-" * 80)
    for key, eintrag in sorted(daten.items(), key=lambda x: berechne_vollstaendigkeit(x[1])):
        pct = berechne_vollstaendigkeit(eintrag)
        fehlend = [
            DOKUMENT_TYPEN[t]["label"]
            for t, d in eintrag["dokumente"].items()
            if d["status"] == "fehlend" and DOKUMENT_TYPEN[t]["pflicht"]
        ]
        balken = "█" * (pct // 10) + "░" * (10 - pct // 10)
        fehlend_str = ", ".join(fehlend[:3]) + ("…" if len(fehlend) > 3 else "")
        print(f"{eintrag['name']:<28} {balken} {pct:>3}%  {fehlend_str}")
    print()


def _kandidat_anzeigen(name: str):
    daten = _lade_dokumente()
    eintrag = daten.get(_kandidat_key(name))
    if not eintrag:
        print(f"Kein Eintrag für: {name}")
        return

    print(f"\nDokumenten-Status: {eintrag['name']}")
    print(f"Vollständigkeit (Pflicht-Docs): {berechne_vollstaendigkeit(eintrag)} %")
    print("-" * 60)
    for typ, meta in DOKUMENT_TYPEN.items():
        dok = eintrag["dokumente"].get(typ, {"status": "fehlend", "notiz": ""})
        status_label = STATUS_WERTE.get(dok["status"], {}).get("label", dok["status"])
        pflicht = "✱" if meta["pflicht"] else " "
        notiz = f" – {dok['notiz']}" if dok.get("notiz") else ""
        print(f"  {pflicht} {meta['label']:<38} {status_label}{notiz}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Dokumenten-Verwaltung pro Kandidat")
    parser.add_argument("--init-alle", nargs="?", const=True, metavar="CSV",
                        help="Alle Kandidaten aus CSV initialisieren")
    parser.add_argument("--liste", action="store_true", help="Übersicht alle Kandidaten")
    parser.add_argument("--kandidat", metavar="NAME", help="Dokumentenstatus eines Kandidaten anzeigen")
    parser.add_argument("--setze", nargs=3, metavar=("NAME", "DOKUMENT", "STATUS"),
                        help="Status setzen: --setze 'Name' reisepass vorhanden")
    parser.add_argument("--notiz", default="", help="Notiz zum Status-Update")
    parser.add_argument("--doktypen", action="store_true", help="Alle gültigen Dokumenttypen anzeigen")
    args = parser.parse_args()

    if args.doktypen:
        print("\nGültige Dokumenttypen:")
        for k, v in DOKUMENT_TYPEN.items():
            pflicht = "✱ Pflicht" if v["pflicht"] else "  Optional"
            print(f"  {k:<22} {pflicht}  – {v['label']}")
        print()
        return

    if args.init_alle is not None:
        csv = args.init_alle if isinstance(args.init_alle, str) else None
        initialisiere_alle(csv)
        return

    if args.liste:
        _liste_anzeigen()
        return

    if args.kandidat:
        _kandidat_anzeigen(args.kandidat)
        return

    if args.setze:
        name, dok_typ, status = args.setze
        setze_dokument_status(name, dok_typ, status, args.notiz)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
