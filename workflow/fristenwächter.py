"""
Fristenwächter: Prüft täglich alle kritischen Fristen und erstellt einen Alert-Report.
Bei kritischen Alarmen wird automatisch auch ein HTML-Report erzeugt.

Ausführung:
  python fristenwächter.py
  python fristenwächter.py kandidaten_vorlage.csv
  python fristenwächter.py --html

Cron (täglich 08:00):
  Linux/Mac: 0 8 * * * cd /path/to/workflow && python fristenwächter.py
  Windows:   Aufgabenplanung → täglich 08:00 → python fristenwächter.py --html
"""

import sys
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime, date
from jinja2 import Environment, FileSystemLoader

from check_foerderung import pruefe_kandidat
from status_manager import _lade_status, STATUSWERTE

WARN_TAGE_ROT  = 30   # Aufenthaltstitel: rot wenn < 30 Tage verbleibend
WARN_TAGE_GELB = 90   # Aufenthaltstitel: gelb wenn < 90 Tage verbleibend
WV_ROT_TAGE    = 14   # Wiedervorlage (hoch): rot wenn < 14 Tage
WV_GELB_TAGE   = 30   # Wiedervorlage: gelb wenn < 30 Tage
STALE_TAGE     = 45   # Status unverändert → Hinweis


def _parse_datum(s) -> date | None:
    if not s or str(s).strip() in ("-", "–", "nan", ""):
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(s).strip(), fmt).date()
        except ValueError:
            continue
    return None


def pruefe_fristen(eingabe_pfad: str | None = None) -> dict:
    eingabe = Path(eingabe_pfad) if eingabe_pfad else Path(__file__).parent / "kandidaten_vorlage.csv"
    df = pd.read_csv(eingabe) if eingabe.suffix == ".csv" else pd.read_excel(eingabe)
    status_daten = _lade_status()
    heute = date.today()

    alarme_rot: list[dict] = []
    alarme_gelb: list[dict] = []
    alarme_grau: list[dict] = []

    for _, zeile in df.iterrows():
        k = pruefe_kandidat(zeile)
        name = k["name"]
        key = name.strip().lower().replace(" ", "_")
        s_eintrag = status_daten.get(key, {})

        # 1. Aufenthaltstitel-Ablauf
        ablauf = _parse_datum(k.get("aufenthaltstitel_ablauf"))
        if ablauf:
            tage = (ablauf - heute).days
            eintrag = {
                "kandidat": name,
                "kategorie": "Aufenthaltstitel-Ablauf",
                "aktion": "Verlängerungsantrag einreichen – Arbeitgeber informieren",
                "tage": tage,
            }
            if tage < 0:
                eintrag["beschreibung"] = (
                    f"BEREITS ABGELAUFEN am {ablauf.strftime('%d.%m.%Y')} "
                    f"({abs(tage)} Tage überfällig) – sofort handeln!"
                )
                alarme_rot.append(eintrag)
            elif tage <= WARN_TAGE_ROT:
                eintrag["beschreibung"] = (
                    f"Läuft ab {ablauf.strftime('%d.%m.%Y')} – nur noch {tage} Tage!"
                )
                alarme_rot.append(eintrag)
            elif tage <= WARN_TAGE_GELB:
                eintrag["beschreibung"] = (
                    f"Läuft ab {ablauf.strftime('%d.%m.%Y')} – noch {tage} Tage"
                )
                alarme_gelb.append(eintrag)

        # 2. Wiedervorlagen
        for wv in k.get("wiedervorlage", []):
            wv_datum = _parse_datum(wv.get("datum"))
            if not wv_datum:
                continue
            tage = (wv_datum - heute).days
            eintrag = {
                "kandidat": name,
                "kategorie": "Wiedervorlage",
                "beschreibung": f"{wv.get('beschreibung', '')} – fällig {wv_datum.strftime('%d.%m.%Y')}",
                "aktion": wv.get("aktion", ""),
                "tage": tage,
            }
            ist_hoch = wv.get("prioritaet") == "hoch"
            if tage < 0 or (ist_hoch and tage <= WV_ROT_TAGE):
                alarme_rot.append(eintrag)
            elif tage <= WV_GELB_TAGE:
                alarme_gelb.append(eintrag)

        # 3. Stagnierender Status
        letzter_str = s_eintrag.get("zuletzt_geaendert")
        if letzter_str:
            letzter = _parse_datum(letzter_str)
            if letzter:
                tage_stale = (heute - letzter).days
                aktuell = s_eintrag.get("aktuell", "neu")
                if tage_stale > STALE_TAGE and aktuell not in ("vermittelt", "abgebrochen", "pausiert"):
                    alarme_grau.append({
                        "kandidat": name,
                        "kategorie": "Status unverändert",
                        "beschreibung": (
                            f"Seit {tage_stale} Tagen im Status "
                            f"'{s_eintrag.get('aktuell_label', aktuell)}'"
                        ),
                        "aktion": "Fortschritt prüfen – nächste Schritte anstoßen",
                        "tage": tage_stale,
                    })

    alarme_rot.sort(key=lambda x: x["tage"])
    alarme_gelb.sort(key=lambda x: x["tage"])
    alarme_grau.sort(key=lambda x: -x["tage"])

    return {
        "datum": heute.strftime("%d.%m.%Y"),
        "rot": alarme_rot,
        "gelb": alarme_gelb,
        "grau": alarme_grau,
        "gesamt": len(alarme_rot) + len(alarme_gelb) + len(alarme_grau),
    }


def zeige_console_report(bericht: dict):
    print(f"\n{'='*62}")
    print(f"  FRISTENWÄCHTER – {bericht['datum']}")
    print(f"  {bericht['gesamt']} Einträge | "
          f"{len(bericht['rot'])} kritisch | "
          f"{len(bericht['gelb'])} bald fällig | "
          f"{len(bericht['grau'])} Hinweise")
    print(f"{'='*62}")

    if bericht["rot"]:
        print(f"\n  🔴 SOFORTIGER HANDLUNGSBEDARF ({len(bericht['rot'])})")
        print("  " + "-" * 58)
        for a in bericht["rot"]:
            print(f"  {a['kandidat']}: {a['kategorie']}")
            print(f"    {a['beschreibung']}")
            if a.get("aktion"):
                print(f"    → {a['aktion']}")

    if bericht["gelb"]:
        print(f"\n  🟡 BALD FÄLLIG ({len(bericht['gelb'])})")
        print("  " + "-" * 58)
        for a in bericht["gelb"]:
            print(f"  {a['kandidat']}: {a['beschreibung']}")
            if a.get("aktion"):
                print(f"    → {a['aktion']}")

    if bericht["grau"]:
        print(f"\n  ℹ  HINWEISE ({len(bericht['grau'])})")
        for a in bericht["grau"]:
            print(f"  {a['kandidat']}: {a['beschreibung']}")

    print()


def generiere_html_report(bericht: dict, ausgabe_ordner: str = "output"):
    ausgabe = Path(__file__).parent / ausgabe_ordner
    ausgabe.mkdir(exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))
    template = env.get_template("alarm_report.html")
    html = template.render(**bericht)
    datei = ausgabe / f"alarm_{date.today().isoformat()}.html"
    datei.write_text(html, encoding="utf-8")
    print(f"  ✓ Alarm-Report gespeichert: {datei}")
    return str(datei)


def main():
    parser = argparse.ArgumentParser(description="Fristenwächter – tägliche Fristen-Prüfung")
    parser.add_argument("csv", nargs="?", help="Kandidaten-CSV (Standard: kandidaten_vorlage.csv)")
    parser.add_argument("--html", action="store_true",
                        help="HTML-Report immer erzeugen (sonst nur bei kritischen Alarmen)")
    args = parser.parse_args()

    bericht = pruefe_fristen(args.csv)
    zeige_console_report(bericht)
    if args.html or bericht["rot"]:
        generiere_html_report(bericht)


if __name__ == "__main__":
    main()
