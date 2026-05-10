"""
Dashboard-Generator: Erzeugt eine Gesamtübersicht aller Kandidaten mit
Ampelstatus, Wiedervorlage-Kalender und Statistiken.
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from check_foerderung import pruefe_kandidat
from status_manager import status_initialisieren, status_holen, get_fortschritt, STATUSWERTE


def generiere_uebersicht(eingabe_pfad: str | None = None, ausgabe_ordner: str = "output"):
    if eingabe_pfad is None:
        eingabe_pfad = Path(__file__).parent / "kandidaten_vorlage.csv"
    eingabe = Path(eingabe_pfad)

    if not eingabe.exists():
        print(f"Fehler: Datei nicht gefunden: {eingabe}")
        sys.exit(1)

    suffix = eingabe.suffix.lower()
    df = pd.read_csv(eingabe) if suffix == ".csv" else pd.read_excel(eingabe)

    ausgabe = Path(__file__).parent / ausgabe_ordner
    ausgabe.mkdir(exist_ok=True)

    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))
    template = env.get_template("uebersicht.html")

    datum = datetime.now().strftime("%d.%m.%Y %H:%M")
    kandidaten = [pruefe_kandidat(zeile) for _, zeile in df.iterrows()]

    # Workflow-Status einlesen und pro Kandidat anreichern
    status_initialisieren(str(eingabe))
    for k in kandidaten:
        eintrag = status_holen(k["name"])
        if eintrag:
            status_key = eintrag.get("aktuell", "neu")
            k["workflow_status"] = {
                "key": status_key,
                "label": STATUSWERTE.get(status_key, {}).get("label", status_key),
                "farbe": STATUSWERTE.get(status_key, {}).get("farbe", "grau"),
                "fortschritt": get_fortschritt(status_key),
                "notiz": eintrag.get("notiz", ""),
            }
        else:
            k["workflow_status"] = {
                "key": "neu", "label": "Neu aufgenommen",
                "farbe": "grau", "fortschritt": 0, "notiz": "",
            }

    # Statistiken
    gesamt = len(kandidaten)
    rot = sum(1 for k in kandidaten if k["status_ampel"] == "rot")
    gelb = sum(1 for k in kandidaten if k["status_ampel"] == "gelb")
    gruen = sum(1 for k in kandidaten if k["status_ampel"] == "gruen")

    programme_zaehler: dict[str, int] = {}
    for k in kandidaten:
        for p in k["berechtigte_programme"]:
            n = p["name"].split("–")[0].strip().split("(")[0].strip()
            programme_zaehler[n] = programme_zaehler.get(n, 0) + 1

    alle_wiedervorlage = []
    for k in kandidaten:
        for t in k["wiedervorlage"]:
            alle_wiedervorlage.append({**t, "kandidat_name": k["name"]})
    alle_wiedervorlage.sort(key=lambda t: t["datum"])

    # Workflow-Statistik (Anzahl pro Status-Gruppe)
    workflow_fortschritt = {
        "aktiv": sum(1 for k in kandidaten if k["workflow_status"]["key"] not in ("neu", "abgebrochen", "pausiert")),
        "abgeschlossen": sum(1 for k in kandidaten if k["workflow_status"]["farbe"] == "gruen"),
        "neu": sum(1 for k in kandidaten if k["workflow_status"]["key"] == "neu"),
    }

    html = template.render(
        kandidaten=kandidaten,
        datum=datum,
        statistik={
            "gesamt": gesamt,
            "rot": rot,
            "gelb": gelb,
            "gruen": gruen,
        },
        workflow_fortschritt=workflow_fortschritt,
        programme_zaehler=sorted(programme_zaehler.items(), key=lambda x: -x[1]),
        alle_wiedervorlage=alle_wiedervorlage,
    )

    ausgabe_datei = ausgabe / "uebersicht.html"
    ausgabe_datei.write_text(html, encoding="utf-8")
    print(f"  ✓ Dashboard erstellt: {ausgabe_datei}")
    print(f"    Gesamt: {gesamt} | Rot: {rot} | Gelb: {gelb} | Grün: {gruen}")
    print(f"    Wiedervorlagen: {len(alle_wiedervorlage)}")
    print("    Im Browser öffnen → Datei → Drucken → Als PDF speichern\n")
    return str(ausgabe_datei)


if __name__ == "__main__":
    eingabe = sys.argv[1] if len(sys.argv) > 1 else None
    ausgabe = sys.argv[2] if len(sys.argv) > 2 else "output"
    generiere_uebersicht(eingabe, ausgabe)
