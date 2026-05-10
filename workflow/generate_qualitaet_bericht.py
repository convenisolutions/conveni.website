"""
Qualitätsbericht-Generator: HTML-Report mit KPIs, Kursträger-Rangliste,
Status-Verteilung und Kandidaten-Verlauf.
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from check_foerderung import pruefe_kandidat
from qualitaet_manager import berechne_kpis, bewerte_kursträger, _lade_qualitaet
from status_manager import _lade_status, get_fortschritt, STATUSWERTE


def generiere_qualitaet_bericht(eingabe_pfad=None, ausgabe_ordner="output"):
    eingabe = Path(eingabe_pfad) if eingabe_pfad else Path(__file__).parent / "kandidaten_vorlage.csv"
    ausgabe = Path(__file__).parent / ausgabe_ordner
    ausgabe.mkdir(exist_ok=True)

    df = pd.read_csv(eingabe) if eingabe.suffix == ".csv" else pd.read_excel(eingabe)
    kandidaten_foerderung = [pruefe_kandidat(zeile) for _, zeile in df.iterrows()]

    kpis = berechne_kpis()
    kursträger_ranking = bewerte_kursträger()
    qualitaet_daten = _lade_qualitaet()
    status_daten = _lade_status()

    # Kandidaten mit Status + Qualitätsdaten anreichern
    kandidaten_detail = []
    for k in kandidaten_foerderung:
        key = k["name"].strip().lower().replace(" ", "_")
        status_eintrag = status_daten.get(key, {})
        qualitaet_eintrag = qualitaet_daten.get(key, {})
        status_key = status_eintrag.get("aktuell", "neu")
        kandidaten_detail.append({
            "name": k["name"],
            "berufsfeld": k["berufsfeld"],
            "sprachniveau": k["sprachniveau"],
            "nationalitaet": k["nationalitaet"],
            "status_key": status_key,
            "status_label": status_eintrag.get("aktuell_label", "Neu aufgenommen"),
            "status_farbe": STATUSWERTE.get(status_key, {}).get("farbe", "grau"),
            "fortschritt": get_fortschritt(status_key),
            "notiz": status_eintrag.get("notiz", ""),
            "kurseintraege": qualitaet_eintrag.get("kurseintraege", []),
        })

    # Status-Verteilung für Balken-Diagramm
    status_verteilung: dict[str, dict] = {}
    for e in status_daten.values():
        s_key = e.get("aktuell", "neu")
        farbe = STATUSWERTE.get(s_key, {}).get("farbe", "grau")
        label = e.get("aktuell_label", "Unbekannt")
        if label not in status_verteilung:
            status_verteilung[label] = {"farbe": farbe, "anzahl": 0, "schritt": STATUSWERTE.get(s_key, {}).get("schritt", 0)}
        status_verteilung[label]["anzahl"] += 1

    status_verteilung_sorted = sorted(
        status_verteilung.items(),
        key=lambda x: x[1]["schritt"],
        reverse=True,
    )
    gesamt_kandidaten = max(len(status_daten), 1)

    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))
    template = env.get_template("qualitaet_bericht.html")
    datum = datetime.now().strftime("%d.%m.%Y %H:%M")

    html = template.render(
        kpis=kpis,
        kursträger_ranking=kursträger_ranking,
        kandidaten_detail=kandidaten_detail,
        status_verteilung=status_verteilung_sorted,
        gesamt_kandidaten=gesamt_kandidaten,
        datum=datum,
    )

    datei = ausgabe / "qualitaet_bericht.html"
    datei.write_text(html, encoding="utf-8")
    print(f"  ✓ Qualitätsbericht erstellt: {datei}")
    if kpis["kurs_gesamt"] > 0:
        print(f"    Prüfungen: {kpis['kurs_gesamt']} | Erfolgsquote: {kpis['erfolgsquote_pct']} %"
              f" | ⌀ Bewertung: {kpis['durchschnitt_bewertung']}")
    print(f"    Kandidaten: {kpis['kandidaten_gesamt']} | "
          f"Aktiv: {kpis['aktiv_in_kurs']} | Vermittelt: {kpis['vermittelt']}\n")
    return str(datei)


if __name__ == "__main__":
    eingabe = sys.argv[1] if len(sys.argv) > 1 else None
    generiere_qualitaet_bericht(eingabe)
