"""
Partnerschulen-Bericht: HTML-Übersicht aller Partnerschulen mit Kandidaten-Matching
und Akquise-Pipeline.
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from check_foerderung import pruefe_kandidat
from partnerschulen_manager import (
    _lade_schulen, finde_schulen_fuer_kandidat,
    KONTAKT_STATUSWERTE, initialisiere_beispieldaten,
)


def generiere_partnerschulen_bericht(eingabe_pfad=None, ausgabe_ordner="output"):
    eingabe = Path(eingabe_pfad) if eingabe_pfad else Path(__file__).parent / "kandidaten_vorlage.csv"
    ausgabe = Path(__file__).parent / ausgabe_ordner
    ausgabe.mkdir(exist_ok=True)

    df = pd.read_csv(eingabe) if eingabe.suffix == ".csv" else pd.read_excel(eingabe)
    kandidaten = [pruefe_kandidat(zeile) for _, zeile in df.iterrows()]

    schulen = _lade_schulen()
    if not schulen:
        print("Keine Schulen gefunden – initialisiere Beispieldaten …")
        initialisiere_beispieldaten()
        schulen = _lade_schulen()

    # Kandidaten-Matching
    matchings = []
    for k in kandidaten:
        passend = finde_schulen_fuer_kandidat(k)
        if passend:
            matchings.append({"kandidat": k, "schulen": passend})

    # Kandidaten-Namen pro Schule (für Schul-Detailansicht)
    kandidaten_pro_schule: dict[str, list[str]] = {s["id"]: [] for s in schulen}
    for m in matchings:
        for s in m["schulen"]:
            if s["id"] in kandidaten_pro_schule:
                kandidaten_pro_schule[s["id"]].append(m["kandidat"]["name"])

    # Angebots-Matrix: welche Schulen bieten welche Module?
    alle_angebote: set[str] = set()
    for s in schulen:
        alle_angebote.update(s["angebote"])
    alle_angebote_sorted = sorted(alle_angebote)

    # Akquise-Pipeline (nach Status gruppiert)
    pipeline: dict[str, list] = {k: [] for k in KONTAKT_STATUSWERTE}
    for s in schulen:
        pipeline[s["kontakt_status"]].append(s)

    # Statistiken
    aktive = [s for s in schulen if s["kontakt_status"] in ("aktiv", "vertrag")]
    in_akquise = [s for s in schulen if s["kontakt_status"] in ("angefragt", "angebot_erhalten")]
    potenzial = [s for s in schulen if s["kontakt_status"] == "noch_nicht"]

    bewertungen = [s["bewertung"] for s in schulen if s.get("bewertung")]
    avg_bewertung = round(sum(bewertungen) / len(bewertungen), 1) if bewertungen else None

    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))
    template = env.get_template("partnerschulen_bericht.html")
    datum = datetime.now().strftime("%d.%m.%Y %H:%M")

    html = template.render(
        schulen=schulen,
        matchings=matchings,
        kandidaten_pro_schule=kandidaten_pro_schule,
        alle_angebote=alle_angebote_sorted,
        pipeline=pipeline,
        statistik={
            "gesamt": len(schulen),
            "aktiv": len(aktive),
            "in_akquise": len(in_akquise),
            "potenzial": len(potenzial),
            "avg_bewertung": avg_bewertung,
            "matchings": len(matchings),
        },
        kontakt_statuswerte=KONTAKT_STATUSWERTE,
        datum=datum,
    )

    datei = ausgabe / "partnerschulen_bericht.html"
    datei.write_text(html, encoding="utf-8")
    print(f"  ✓ Partnerschulen-Bericht erstellt: {datei}")
    print(f"    Schulen: {len(schulen)} | Aktiv/Vertrag: {len(aktive)} | "
          f"In Akquise: {len(in_akquise)} | Potenzial: {len(potenzial)}")
    print(f"    {len(matchings)} von {len(kandidaten)} Kandidaten haben passende Schulen\n")
    return str(datei)


if __name__ == "__main__":
    eingabe = sys.argv[1] if len(sys.argv) > 1 else None
    generiere_partnerschulen_bericht(eingabe)
