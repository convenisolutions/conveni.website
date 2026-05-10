"""
Monatsbericht-Generator: Fasst alle Aktivitäten des aktuellen (oder gewählten)
Monats zusammen und erstellt einen druckfertigen HTML-Report.

Verwendung:
  python generate_monatsbericht.py
  python generate_monatsbericht.py kandidaten_vorlage.csv
  python generate_monatsbericht.py --monat 4 --jahr 2026
"""

import sys
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader

from check_foerderung import pruefe_kandidat
from status_manager import _lade_status, STATUSWERTE, get_fortschritt
from qualitaet_manager import _lade_qualitaet, berechne_kpis


def _parse_datum(s) -> date | None:
    if not s or str(s).strip() in ("-", "–", "nan", ""):
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(str(s).strip(), fmt).date()
        except ValueError:
            continue
    return None


def generiere_monatsbericht(
    eingabe_pfad=None,
    monat: int | None = None,
    jahr: int | None = None,
    ausgabe_ordner: str = "output",
):
    heute = date.today()
    monat = monat or heute.month
    jahr = jahr or heute.year
    monat_start = date(jahr, monat, 1)
    monat_ende = date(jahr + 1, 1, 1) if monat == 12 else date(jahr, monat + 1, 1)
    monat_str = monat_start.strftime("%B %Y")

    eingabe = Path(eingabe_pfad) if eingabe_pfad else Path(__file__).parent / "kandidaten_vorlage.csv"
    ausgabe = Path(__file__).parent / ausgabe_ordner
    ausgabe.mkdir(exist_ok=True)

    df = pd.read_csv(eingabe) if eingabe.suffix == ".csv" else pd.read_excel(eingabe)
    kandidaten = [pruefe_kandidat(zeile) for _, zeile in df.iterrows()]

    status_daten = _lade_status()
    qualitaet_daten = _lade_qualitaet()
    kpis = berechne_kpis()

    # ── Status-Bewegungen dieses Monats ─────────────────────────────────────
    status_bewegungen: list[dict] = []
    neu_diesen_monat = 0
    for eintrag in status_daten.values():
        for v in eintrag.get("verlauf", []):
            v_datum = _parse_datum(v.get("datum"))
            if not v_datum or not (monat_start <= v_datum < monat_ende):
                continue
            status_bewegungen.append({
                "kandidat": eintrag["name"],
                "status": v["status"],
                "label": v["label"],
                "datum_str": v_datum.strftime("%d.%m."),
                "notiz": v.get("notiz", ""),
            })
            if v["status"] == "neu":
                neu_diesen_monat += 1
    status_bewegungen.sort(key=lambda x: x["datum_str"], reverse=True)

    # ── Kursabschlüsse dieses Monats ────────────────────────────────────────
    kurse_diesen_monat: list[dict] = []
    for k_daten in qualitaet_daten.values():
        for e in k_daten.get("kurseintraege", []):
            abschluss = _parse_datum(e.get("abschluss_datum"))
            if abschluss and monat_start <= abschluss < monat_ende:
                kurse_diesen_monat.append({
                    "kandidat": k_daten["name"],
                    "modul": e["modul"],
                    "ergebnis": e["pruefungsergebnis"],
                    "niveau": e.get("erreichtes_niveau", ""),
                    "kurstraeger": e["kurstraeger_name"],
                    "datum_str": abschluss.strftime("%d.%m."),
                })

    # ── Wiedervorlagen dieses Monats ────────────────────────────────────────
    wv_diesen_monat: list[dict] = []
    for k in kandidaten:
        for wv in k.get("wiedervorlage", []):
            wv_datum = _parse_datum(wv.get("datum"))
            if wv_datum and monat_start <= wv_datum < monat_ende:
                wv_diesen_monat.append({
                    **wv,
                    "kandidat": k["name"],
                    "datum_str": wv_datum.strftime("%d.%m."),
                })
    wv_diesen_monat.sort(key=lambda x: x["datum_str"])

    # ── Fördervolumen ────────────────────────────────────────────────────────
    foerder_gesamt = sum(k["kosten"]["foerderung_gesamt"] for k in kandidaten)
    eigenanteil_gesamt = sum(k["kosten"]["eigenanteil_gesamt"] for k in kandidaten)

    # ── Programm-Verteilung ──────────────────────────────────────────────────
    programme_zaehler: dict[str, int] = defaultdict(int)
    for k in kandidaten:
        for p in k["berechtigte_programme"]:
            n = p["name"].split("–")[0].strip().split("(")[0].strip()
            programme_zaehler[n] += 1

    # ── Aktuelle Status-Verteilung ───────────────────────────────────────────
    status_aktuell: dict[tuple, int] = defaultdict(int)
    for e in status_daten.values():
        farbe = STATUSWERTE.get(e.get("aktuell", "neu"), {}).get("farbe", "grau")
        label = e.get("aktuell_label", "Neu")
        status_aktuell[(label, farbe)] += 1
    status_aktuell_sorted = sorted(status_aktuell.items(), key=lambda x: -x[1])

    # ── Offene Wiedervorlagen (alle zukünftigen) ─────────────────────────────
    alle_wv_offen: list[dict] = []
    for k in kandidaten:
        for wv in k.get("wiedervorlage", []):
            wv_datum = _parse_datum(wv.get("datum"))
            if wv_datum and wv_datum >= heute:
                alle_wv_offen.append({**wv, "kandidat": k["name"]})
    alle_wv_offen.sort(key=lambda x: x.get("datum", ""))

    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))
    template = env.get_template("monatsbericht.html")

    html = template.render(
        monat_str=monat_str,
        datum=datetime.now().strftime("%d.%m.%Y %H:%M"),
        kpis=kpis,
        neu_diesen_monat=neu_diesen_monat,
        status_bewegungen=status_bewegungen,
        kurse_diesen_monat=kurse_diesen_monat,
        wv_diesen_monat=wv_diesen_monat,
        wv_offen_naechste=alle_wv_offen[:10],
        programme_zaehler=sorted(programme_zaehler.items(), key=lambda x: -x[1]),
        status_aktuell=status_aktuell_sorted,
        foerder_gesamt=foerder_gesamt,
        eigenanteil_gesamt=eigenanteil_gesamt,
        kandidaten_gesamt=len(kandidaten),
    )

    datei = ausgabe / f"monatsbericht_{jahr}_{monat:02d}.html"
    datei.write_text(html, encoding="utf-8")
    print(f"  ✓ Monatsbericht {monat_str}: {datei}")
    print(f"    Kandidaten: {len(kandidaten)} | Neue: {neu_diesen_monat} | "
          f"Status-Bewegungen: {len(status_bewegungen)} | Kursabschlüsse: {len(kurse_diesen_monat)}")
    return str(datei)


def main():
    parser = argparse.ArgumentParser(description="Monatsbericht-Generator")
    parser.add_argument("csv", nargs="?", help="Kandidaten-CSV (Standard: kandidaten_vorlage.csv)")
    parser.add_argument("--monat", type=int, metavar="M", help="Monat (1–12, Standard: aktueller Monat)")
    parser.add_argument("--jahr", type=int, metavar="J", help="Jahr (Standard: aktuelles Jahr)")
    args = parser.parse_args()

    generiere_monatsbericht(args.csv, monat=args.monat, jahr=args.jahr)


if __name__ == "__main__":
    main()
