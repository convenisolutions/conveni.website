"""
Dokumenten-Bericht: HTML-Dashboard mit Vollständigkeits-Übersicht und fehlenden Unterlagen.
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from dokumente_manager import (
    _lade_dokumente, berechne_vollstaendigkeit,
    initialisiere_alle, DOKUMENT_TYPEN, STATUS_WERTE,
)


def generiere_dokumente_bericht(eingabe_pfad=None, ausgabe_ordner="output"):
    eingabe = Path(eingabe_pfad) if eingabe_pfad else Path(__file__).parent / "kandidaten_vorlage.csv"
    ausgabe = Path(__file__).parent / ausgabe_ordner
    ausgabe.mkdir(exist_ok=True)

    initialisiere_alle(str(eingabe))
    daten = _lade_dokumente()

    kandidaten_detail = []
    for key, eintrag in daten.items():
        vollst = berechne_vollstaendigkeit(eintrag)
        fehlende_pflicht = [
            {"typ": typ, "label": DOKUMENT_TYPEN[typ]["label"]}
            for typ, d in eintrag["dokumente"].items()
            if d["status"] == "fehlend" and DOKUMENT_TYPEN[typ]["pflicht"]
        ]
        angefordert = [
            {"typ": typ, "label": DOKUMENT_TYPEN[typ]["label"], "notiz": d.get("notiz", "")}
            for typ, d in eintrag["dokumente"].items()
            if d["status"] == "angefordert"
        ]
        kandidaten_detail.append({
            "name": eintrag["name"],
            "vollstaendigkeit": vollst,
            "fehlende_pflicht": fehlende_pflicht,
            "angefordert": angefordert,
            "dokumente": eintrag["dokumente"],
        })

    kandidaten_detail.sort(key=lambda x: x["vollstaendigkeit"])

    vollstaendig = sum(1 for k in kandidaten_detail if k["vollstaendigkeit"] == 100)
    kritisch = sum(1 for k in kandidaten_detail if k["vollstaendigkeit"] < 50)

    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))
    template = env.get_template("dokumente_bericht.html")
    datum = datetime.now().strftime("%d.%m.%Y %H:%M")

    html = template.render(
        kandidaten=kandidaten_detail,
        dokument_typen=DOKUMENT_TYPEN,
        status_werte=STATUS_WERTE,
        statistik={
            "gesamt": len(kandidaten_detail),
            "vollstaendig": vollstaendig,
            "kritisch": kritisch,
            "avg_vollstaendigkeit": round(
                sum(k["vollstaendigkeit"] for k in kandidaten_detail) / len(kandidaten_detail)
            ) if kandidaten_detail else 0,
        },
        datum=datum,
    )

    datei = ausgabe / "dokumente_bericht.html"
    datei.write_text(html, encoding="utf-8")
    print(f"  ✓ Dokumenten-Bericht erstellt: {datei}")
    print(f"    Kandidaten: {len(kandidaten_detail)} | "
          f"Vollständig: {vollstaendig} | Kritisch (<50 %): {kritisch}\n")
    return str(datei)


if __name__ == "__main__":
    eingabe = sys.argv[1] if len(sys.argv) > 1 else None
    generiere_dokumente_bericht(eingabe)
