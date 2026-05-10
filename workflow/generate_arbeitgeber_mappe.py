"""
Arbeitgeber-Mappe: Generiert pro Arbeitgeber ein eigenes Dokument mit
allen Kandidaten, ihren Förderungen, Pflichten und nächsten Schritten.

Verwendung:
  python generate_arbeitgeber_mappe.py kandidaten_vorlage.csv
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader

from check_foerderung import pruefe_kandidat, PROGRAMME


AG_FOERDER_STAFFEL = {
    "klein":  {"label": "Klein (< 10 Mitarbeiter)",    "lehrgang": "100 %", "lohn": "75 %",
               "lehrgang_pct": 100, "lohn_pct": 75},
    "mittel": {"label": "Mittel (10 – 249 Mitarbeiter)","lehrgang": "50 %",  "lohn": "50 %",
               "lehrgang_pct": 50,  "lohn_pct": 50},
    "groß":   {"label": "Groß (≥ 250 Mitarbeiter)",    "lehrgang": "25 %",  "lohn": "25 %",
               "lehrgang_pct": 25,  "lohn_pct": 25},
}

AG_PFLICHTEN_ALLGEMEIN = [
    "Arbeitgeberbestätigung für jeden BSK-/FbD-Antrag ausstellen (mit Firmenstempel + Unterschrift)",
    "Freistellung der Mitarbeiter für Kurszeiten sicherstellen (ggf. im Arbeitsvertrag ergänzen)",
    "Aktuelle Arbeitsverträge für Förderanträge bereithalten",
    "Aufenthaltstitel-Ablaufdaten im Blick behalten – bei Ablauf sofort Conveni informieren",
    "Änderungen im Arbeitsverhältnis (Kündigung, Stundenreduzierung) sofort Conveni melden",
]

AG_PFLICHTEN_QUALIFIZIERUNG = [
    "Antrag Qualifizierungschancengesetz (§ 82 SGB III) VOR Kursbeginn bei der Agentur für Arbeit stellen!",
    "Weiterbildungsvertrag / Kursangebot mit Kosten bei der Agentur für Arbeit einreichen",
    "Nachweis der Betriebsgröße bei der Agentur für Arbeit vorlegen",
]

AG_PFLICHTEN_EINGLIEDERUNG = [
    "Antrag auf Eingliederungszuschuss (§ 88 SGB III) MUSS vor Arbeitsaufnahme gestellt werden!",
    "Ansprechpartner bei der zuständigen Agentur für Arbeit kontaktieren",
]


def _normalisiere_groesse(groesse: str) -> str:
    g = str(groesse).strip().lower()
    if g in ("groß", "gross", "large", "groß", "250+", "≥250"):
        return "groß"
    if g in ("klein", "small", "<10", "10>"):
        return "klein"
    return "mittel"


def _berechne_ag_foerderung(kandidaten: list, groesse: str) -> dict:
    staffel = AG_FOERDER_STAFFEL[groesse]
    bsk_kandidaten = [k for k in kandidaten if any("BSK" in p["name"] for p in k["berechtigte_programme"])]
    eigenanteil_gesamt = sum(k["kosten"]["eigenanteil_gesamt"] for k in bsk_kandidaten)
    foerderung_gesamt = sum(k["kosten"]["foerderung_gesamt"] for k in bsk_kandidaten)
    ag_anteil_lehrgang = round(foerderung_gesamt * (staffel["lehrgang_pct"] / 100), 2)

    return {
        "staffel": staffel,
        "bsk_kandidaten_anzahl": len(bsk_kandidaten),
        "eigenanteil_kandidaten_gesamt": eigenanteil_gesamt,
        "foerdervolumen_gesamt": foerderung_gesamt,
        "ag_erstattung_lehrgang": ag_anteil_lehrgang,
        "hinweis": (
            f"Bei {len(bsk_kandidaten)} BSK-Kandidaten: "
            f"BAMF übernimmt ca. {foerderung_gesamt:.0f} € Kurskosten; "
            f"Sie erhalten zusätzlich {staffel['lohn']} Lohnkostenzuschuss "
            f"über das Qualifizierungschancengesetz."
        ),
    }


def _baue_ag_naechste_schritte(kandidaten: list, ag_foerderung: dict) -> list:
    schritte = []
    nr = 1

    # Dringende Aufenthaltstitel
    ablauf_dringend = [
        k for k in kandidaten
        if any("DRINGEND" in h for h in k["hinweise"])
    ]
    if ablauf_dringend:
        namen = ", ".join(k["name"] for k in ablauf_dringend)
        schritte.append({
            "nr": nr, "prioritaet": "sofort",
            "schritt": "Aufenthaltstitel-Verlängerung unterstützen",
            "details": f"Betroffene Mitarbeiter: {namen}. Bescheinigung des Arbeitgebers für ABH bereitstellen.",
        }); nr += 1

    # Qualifizierungschancengesetz
    if ag_foerderung["bsk_kandidaten_anzahl"] > 0:
        schritte.append({
            "nr": nr, "prioritaet": "sofort",
            "schritt": "Qualifizierungschancengesetz beantragen – VOR Kursbeginn!",
            "details": (
                f"Antrag bei der Agentur für Arbeit stellen (für {ag_foerderung['bsk_kandidaten_anzahl']} Mitarbeiter). "
                f"Lehrgangskosten-Übernahme: {ag_foerderung['staffel']['lehrgang']}. "
                f"Lohnkostenzuschuss während Kurs: {ag_foerderung['staffel']['lohn']}."
            ),
        }); nr += 1

    # Arbeitgeberbestätigungen
    bsk_kandidaten = [k for k in kandidaten if any("BSK" in p["name"] for p in k["berechtigte_programme"])]
    if bsk_kandidaten:
        namen = ", ".join(k["name"] for k in bsk_kandidaten)
        schritte.append({
            "nr": nr, "prioritaet": "diese_woche",
            "schritt": "Arbeitgeberbestätigungen ausstellen",
            "details": f"Für BSK-Anträge nötig: {namen}. Mit Firmenstempel und Unterschrift der Geschäftsführung.",
        }); nr += 1

    # Einstufungstests
    schritte.append({
        "nr": nr, "prioritaet": "diese_woche",
        "schritt": "Mitarbeiter zu Einstufungstests anmelden",
        "details": "BAMF-Kursträger in der Nähe kontaktieren. BAMF-Servicenummer: 0800 8 67467 (kostenfrei).",
    }); nr += 1

    # Anerkennung offen
    anerkennung_offen = [
        k for k in kandidaten
        if k.get("berufsfeld") in {"Pflege", "Altenpflege", "Krankenpflege", "Medizin", "Arztpraxis", "Erziehung"}
        and any("IQ Netzwerk" in p["name"] for p in k["berechtigte_programme"])
    ]
    if anerkennung_offen:
        namen = ", ".join(k["name"] for k in anerkennung_offen)
        schritte.append({
            "nr": nr, "prioritaet": "diesen_monat",
            "schritt": "Anerkennungsverfahren begleiten (reglementierte Berufe)",
            "details": (
                f"Betroffene Mitarbeiter: {namen}. "
                "Als Arbeitgeber: Arbeitgeberbestätigung für die Anerkennungsstelle ausstellen; "
                "ggf. Berufserlaubnis als Zwischenlösung beantragen."
            ),
        }); nr += 1

    return schritte


def generiere_arbeitgeber_mappen(eingabe_pfad=None, ausgabe_ordner="output"):
    eingabe = Path(eingabe_pfad) if eingabe_pfad else Path(__file__).parent / "kandidaten_vorlage.csv"
    if not eingabe.exists():
        print(f"Fehler: Datei nicht gefunden: {eingabe}"); return

    df = pd.read_csv(eingabe) if eingabe.suffix == ".csv" else pd.read_excel(eingabe)
    ausgabe = Path(__file__).parent / ausgabe_ordner
    ausgabe.mkdir(exist_ok=True)

    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))
    template = env.get_template("arbeitgeber_mappe.html")
    datum = datetime.now().strftime("%d.%m.%Y")

    # Kandidaten analysieren und nach Arbeitgeber gruppieren
    ag_gruppen: dict[str, dict] = defaultdict(lambda: {"kandidaten": [], "groesse": "mittel", "arbeitgeber": ""})

    for _, zeile in df.iterrows():
        arbeitgeber = str(zeile.get("arbeitgeber", "Unbekannt")).strip()
        if arbeitgeber.lower() in ("", "arbeitssuchend", "–", "-", "nan"):
            continue
        r = pruefe_kandidat(zeile)
        ag_gruppen[arbeitgeber]["kandidaten"].append(r)
        ag_gruppen[arbeitgeber]["arbeitgeber"] = arbeitgeber
        ag_gruppen[arbeitgeber]["groesse"] = _normalisiere_groesse(
            str(zeile.get("arbeitgeber_groesse", "mittel"))
        )

    gesamt_mappen = 0
    for ag_name, ag_daten in ag_gruppen.items():
        kandidaten = ag_daten["kandidaten"]
        groesse = ag_daten["groesse"]
        ag_foerderung = _berechne_ag_foerderung(kandidaten, groesse)
        naechste_schritte = _baue_ag_naechste_schritte(kandidaten, ag_foerderung)

        # Alle Wiedervorlagen dieser Firma
        alle_wv = []
        for k in kandidaten:
            for t in k["wiedervorlage"]:
                alle_wv.append({**t, "kandidat_name": k["name"]})
        alle_wv.sort(key=lambda t: t["datum"])

        # Pflichten zusammenstellen
        pflichten = list(AG_PFLICHTEN_ALLGEMEIN)
        if ag_foerderung["bsk_kandidaten_anzahl"] > 0:
            pflichten += AG_PFLICHTEN_QUALIFIZIERUNG

        html = template.render(
            ag_name=ag_name,
            ag_groesse=AG_FOERDER_STAFFEL[groesse]["label"],
            kandidaten=kandidaten,
            ag_foerderung=ag_foerderung,
            naechste_schritte=naechste_schritte,
            pflichten=pflichten,
            wiedervorlage=alle_wv,
            datum=datum,
        )

        dateiname = f"arbeitgeber_{ag_name.lower().replace(' ', '_').replace('.', '')[:40]}_mappe.html"
        (ausgabe / dateiname).write_text(html, encoding="utf-8")
        print(f"  ✓ {dateiname}  ({len(kandidaten)} Kandidaten)")
        gesamt_mappen += 1

    print(f"\n  {gesamt_mappen} Arbeitgeber-Mappen erstellt in: {ausgabe.resolve()}")
    print("  Im Browser öffnen → Drucken → Als PDF speichern → an Arbeitgeber senden\n")


if __name__ == "__main__":
    eingabe = sys.argv[1] if len(sys.argv) > 1 else None
    generiere_arbeitgeber_mappen(eingabe)
