"""
Förderberechtigungs-Prüfung für Sprachkurse
Grundlage: DeuFöV (Deutschsprachförderverordnung), § 45a AufenthG, § 421 SGB III
Zielgruppe: Fachkräfte aus Drittstaaten (Philippinen, Vietnam)
"""

import pandas as pd
import sys
from datetime import datetime, date
from pathlib import Path

# ---------------------------------------------------------------------------
# Förderprogramme und ihre Kriterien
# ---------------------------------------------------------------------------

PROGRAMME = {
    "Berufssprachkurs (BSK)": {
        "beschreibung": (
            "Berufssprachkurse nach § 45a AufenthG / DeuFöV. "
            "Speziell für berufliche Integration in Deutschland."
        ),
        "foerderer": "BAMF",
        "kosten": "Kostenfrei oder stark subventioniert (ca. 2,07 € / UE Eigenanteil)",
        "niveau": ["A2", "B1", "B2", "C1"],
        "spezialmodule": {
            "Pflege": "BSK-Modul Pflege (900 UE)",
            "Medizin": "BSK-Modul Medizin",
            "Handwerk": "BSK-Standardkurs (510 UE)",
            "IT": "BSK-Standardkurs (510 UE)",
            "Gastronomie": "BSK-Standardkurs (510 UE)",
        },
        "pflicht_dokumente": [
            "Reisepass (Kopie, alle Seiten)",
            "Aufenthaltstitel (Kopie, Vorder- und Rückseite)",
            "Arbeitsvertrag ODER Arbeitgeberbestätigung (bei Beschäftigung)",
            "Nachweis aktuelles Sprachniveau (Einstufungstest beim Kursträger)",
            "Ausgefülltes BAMF-Antragsformular (Formular 540)",
        ],
    },
    "FbD – Förderung berufsbez. Deutschkenntnisse": {
        "beschreibung": (
            "ESF-gefördertes Programm über BAMF. Für Beschäftigte und Arbeitssuchende "
            "mit Bedarf an berufsbezogenem Deutsch."
        ),
        "foerderer": "BAMF / ESF",
        "kosten": "Kostenfrei für Teilnehmende",
        "niveau": ["A2", "B1", "B2", "C1"],
        "spezialmodule": {},
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "Nachweis der Beschäftigung ODER Jobcenter-/AA-Bescheinigung",
            "Sprachnachweis (Zertifikat oder Einstufungstest)",
            "Anerkennungsbescheid ODER Nachweis laufendes Anerkennungsverfahren",
        ],
    },
    "Integrationskurs": {
        "beschreibung": (
            "Sprach- und Orientierungskurs nach § 43 AufenthG. "
            "Für Drittstaatsangehörige im frühen Aufenthaltsstadium."
        ),
        "foerderer": "BAMF",
        "kosten": "Ca. 1,95 € / UE (Ermäßigung / Erlass möglich)",
        "niveau": ["A1", "A2"],
        "spezialmodule": {},
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel / Niederlassungserlaubnis (Kopie)",
            "Ausgefüllter Antrag auf Zulassung zum Integrationskurs",
            "Ggf. Berechtigungsschein der Ausländerbehörde",
        ],
    },
    "§ 421 SGB III – Sprachkurs über Agentur für Arbeit": {
        "beschreibung": (
            "Förderung von Deutschkursen über die Bundesagentur für Arbeit "
            "für arbeitssuchend gemeldete Personen."
        ),
        "foerderer": "Agentur für Arbeit / Jobcenter",
        "kosten": "Kostenfrei (Bildungsgutschein)",
        "niveau": ["A1", "A2", "B1", "B2"],
        "spezialmodule": {},
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "Beratungsgespräch beim Arbeitsberater (Termin vereinbaren)",
            "Nachweis der Arbeitsuche / Arbeitlosigkeit",
            "Bildungsgutschein (wird bei Bewilligung ausgestellt)",
        ],
    },
}

SPRACHNIVEAU_RANG = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

# ---------------------------------------------------------------------------
# Berechtigungsprüfung
# ---------------------------------------------------------------------------

def pruefe_kandidat(zeile: pd.Series) -> dict:
    """Prüft Förderberechtigung für einen Kandidaten und gibt Ergebnis zurück."""
    name = f"{zeile['vorname']} {zeile['nachname']}"
    niveau = str(zeile.get("sprachniveau_aktuell", "")).strip().upper()
    beschaeftigt = str(zeile.get("beschaeftigt", "")).strip().lower() in ("ja", "yes", "true", "1")
    berufsfeld = str(zeile.get("berufsfeld", "")).strip()
    anerkennung = str(zeile.get("anerkennungsverfahren", "")).strip().lower()
    nationalitaet = str(zeile.get("nationalitaet", "")).strip()
    aufenthaltstitel = str(zeile.get("aufenthaltstitel", "")).strip()

    niveau_rang = SPRACHNIVEAU_RANG.get(niveau, 0)
    berechtigte_programme = []
    hinweise = []

    # --- Berufssprachkurs (BSK) ---
    if niveau_rang >= 2 and beschaeftigt:
        prog = PROGRAMME["Berufssprachkurs (BSK)"].copy()
        module = prog["spezialmodule"].get(berufsfeld, "BSK-Standardkurs (510 UE)")
        berechtigte_programme.append({
            "name": "Berufssprachkurs (BSK)",
            "details": prog,
            "empfohlenes_modul": module,
        })

    # --- FbD ---
    if niveau_rang >= 2 and (beschaeftigt or "arbeitssuchend" in aufenthaltstitel.lower()):
        extra_dokumente = []
        if anerkennung == "nicht beantragt":
            hinweise.append(
                "FbD: Anerkennungsverfahren sollte zeitnah eingeleitet werden "
                "(steigert Fördermöglichkeiten deutlich)."
            )
            extra_dokumente.append("Einleitung des Anerkennungsverfahrens empfohlen")
        prog = PROGRAMME["FbD – Förderung berufsbez. Deutschkenntnisse"].copy()
        if extra_dokumente:
            prog = dict(prog)
            prog["pflicht_dokumente"] = prog["pflicht_dokumente"] + extra_dokumente
        berechtigte_programme.append({
            "name": "FbD – Förderung berufsbez. Deutschkenntnisse",
            "details": prog,
            "empfohlenes_modul": "Standardkurs",
        })

    # --- Integrationskurs ---
    if niveau_rang <= 2:
        berechtigte_programme.append({
            "name": "Integrationskurs",
            "details": PROGRAMME["Integrationskurs"],
            "empfohlenes_modul": f"Integrationskurs (660 UE Sprachkurs + 100 UE Orientierung)",
        })

    # --- § 421 SGB III ---
    if not beschaeftigt:
        berechtigte_programme.append({
            "name": "§ 421 SGB III – Sprachkurs über Agentur für Arbeit",
            "details": PROGRAMME["§ 421 SGB III – Sprachkurs über Agentur für Arbeit"],
            "empfohlenes_modul": "Bildungsgutschein beantragen",
        })
        hinweise.append(
            "§ 421 SGB III: Kandidat muss sich als arbeitssuchend bei der Agentur für Arbeit melden."
        )

    # --- Allgemeine Hinweise ---
    if "blaue karte" in aufenthaltstitel.lower():
        hinweise.append(
            "Blaue Karte EU: Besondere Privilegien beim Familiennachzug und Niederlassungserlaubnis – "
            "prüfen, ob Sprachkurse als Anerkennungsleistung anrechenbar sind."
        )

    # Aufenthaltstitel-Ablaufdatum prüfen
    gueltig_bis_raw = str(zeile.get("aufenthaltstitel_gueltig_bis", "")).strip()
    if gueltig_bis_raw:
        try:
            gueltig_bis = datetime.strptime(gueltig_bis_raw, "%Y-%m-%d").date()
            tage_verbleibend = (gueltig_bis - date.today()).days
            if tage_verbleibend < 90:
                hinweise.append(
                    f"DRINGEND: Aufenthaltstitel läuft in {tage_verbleibend} Tagen ab "
                    f"({gueltig_bis_raw}) – Verlängerung sofort beantragen!"
                )
        except ValueError:
            pass

    return {
        "name": name,
        "nationalitaet": nationalitaet,
        "sprachniveau": niveau,
        "beschaeftigt": beschaeftigt,
        "berufsfeld": berufsfeld,
        "berechtigte_programme": berechtigte_programme,
        "hinweise": hinweise,
    }


# ---------------------------------------------------------------------------
# Hauptfunktion
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        eingabe = Path(__file__).parent / "kandidaten_vorlage.csv"
    else:
        eingabe = Path(sys.argv[1])

    if not eingabe.exists():
        print(f"Fehler: Datei nicht gefunden: {eingabe}")
        sys.exit(1)

    suffix = eingabe.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(eingabe)
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(eingabe)
    else:
        print("Fehler: Bitte CSV oder Excel-Datei angeben.")
        sys.exit(1)

    print(f"\n{'='*65}")
    print(f"  FÖRDERBERECHTIGUNGS-PRÜFUNG – {datetime.now().strftime('%d.%m.%Y')}")
    print(f"  Kandidaten gesamt: {len(df)}")
    print(f"{'='*65}\n")

    ergebnisse = []
    for _, zeile in df.iterrows():
        ergebnis = pruefe_kandidat(zeile)
        ergebnisse.append(ergebnis)

        print(f"Kandidat: {ergebnis['name']} ({ergebnis['nationalitaet']})")
        print(f"  Sprachniveau: {ergebnis['sprachniveau']} | "
              f"Beschäftigt: {'Ja' if ergebnis['beschaeftigt'] else 'Nein'} | "
              f"Berufsfeld: {ergebnis['berufsfeld']}")
        print(f"  Förderprogramme ({len(ergebnis['berechtigte_programme'])}):")
        for prog in ergebnis["berechtigte_programme"]:
            print(f"    ✓ {prog['name']}")
            print(f"      → {prog['empfohlenes_modul']}")
            print(f"      → Förderung durch: {prog['details']['foerderer']}")
        if ergebnis["hinweise"]:
            print(f"  Hinweise:")
            for h in ergebnis["hinweise"]:
                print(f"    ⚠ {h}")
        print()

    return ergebnisse


if __name__ == "__main__":
    main()
