"""
Förderberechtigungs-Prüfung für Sprachkurse und berufliche Weiterbildung
Grundlage: DeuFöV (Deutschsprachförderverordnung), § 43/45a AufenthG,
           § 421 SGB III, IntV (Integrationskursverordnung), IQ-Netzwerk
Zielgruppe: Fachkräfte aus Drittstaaten (Philippinen, Vietnam)
"""

import pandas as pd
import sys
from datetime import datetime, date
from pathlib import Path

# ---------------------------------------------------------------------------
# Berufssprachkurs-Module (DeuFöV / BAMF) – vollständige Übersicht
# ---------------------------------------------------------------------------

# Welches BSK-Modul passt zu welchem Berufsfeld?
BSK_MODULE = {
    # Gesundheit & Soziales → BSK-900 Spezialkurs
    "Pflege":            ("BSK-Spezialkurs Pflege",   "900 UE", "A2–B2+", "BAMF-Formular 600-P"),
    "Altenpflege":       ("BSK-Spezialkurs Pflege",   "900 UE", "A2–B2+", "BAMF-Formular 600-P"),
    "Krankenpflege":     ("BSK-Spezialkurs Pflege",   "900 UE", "A2–B2+", "BAMF-Formular 600-P"),
    "Medizin":           ("BSK-Spezialkurs Medizin",  "900 UE", "B1–C1",  "BAMF-Formular 600-M"),
    "Arztpraxis":        ("BSK-Spezialkurs Medizin",  "900 UE", "B1–C1",  "BAMF-Formular 600-M"),
    "Erziehung":         ("BSK-Spezialkurs Pädagogik","900 UE", "A2–B2",  "BAMF-Formular 600"),
    # Handwerk / Industrie → BSK-510 Standard
    "Handwerk":          ("BSK-Standardkurs",         "510 UE", "A2–B1",  "BAMF-Formular 540"),
    "Bau":               ("BSK-Standardkurs",         "510 UE", "A2–B1",  "BAMF-Formular 540"),
    "Elektro":           ("BSK-Standardkurs",         "510 UE", "A2–B1",  "BAMF-Formular 540"),
    "Logistik":          ("BSK-Standardkurs",         "510 UE", "A2–B1",  "BAMF-Formular 540"),
    "Gastronomie":       ("BSK-Standardkurs",         "510 UE", "A2–B1",  "BAMF-Formular 540"),
    "Einzelhandel":      ("BSK-Standardkurs",         "510 UE", "A2–B1",  "BAMF-Formular 540"),
    # IT / Kaufmännisch → BSK-Fachkurs (höheres Niveau)
    "IT":                ("BSK-Fachkurs",             "400 UE", "B2–C1",  "BAMF-Formular 540"),
    "Ingenieur":         ("BSK-Fachkurs",             "400 UE", "B2–C1",  "BAMF-Formular 540"),
    "Kaufmännisch":      ("BSK-Fachkurs",             "400 UE", "B2–C1",  "BAMF-Formular 540"),
}
BSK_DEFAULT = ("BSK-Standardkurs", "510 UE", "A2–B1", "BAMF-Formular 540")

# ---------------------------------------------------------------------------
# Integrationskurs-Varianten (§ 43 AufenthG / IntV)
# ---------------------------------------------------------------------------

INTEGRATIONSKURS_TYPEN = {
    "alphabetisierung": {
        "name": "Alphabetisierungskurs",
        "ue": "900 UE Sprachkurs + 100 UE Orientierungskurs",
        "zielgruppe": "Personen ohne lateinische Schriftkenntnisse",
        "niveau_ziel": "A2–B1",
        "kosten": "Ca. 1,95 € / UE (Erlass bei geringem Einkommen möglich)",
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "Antrag auf Zulassung Alphabetisierungskurs (BAMF-Formular)",
            "Berechtigungsschein der Ausländerbehörde",
            "Ggf. Nachweis über fehlende Alphabetisierung (Kursträger-Einstufung)",
        ],
    },
    "allgemein": {
        "name": "Allgemeiner Integrationskurs",
        "ue": "660 UE Sprachkurs + 100 UE Orientierungskurs",
        "zielgruppe": "Drittstaatsangehörige mit Grundkenntnissen (A1–A2)",
        "niveau_ziel": "B1",
        "kosten": "Ca. 1,95 € / UE (Erlass bei geringem Einkommen möglich)",
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel / Niederlassungserlaubnis (Kopie)",
            "Antrag auf Zulassung zum Integrationskurs (BAMF-Formular 101)",
            "Berechtigungsschein der Ausländerbehörde (falls vorhanden)",
        ],
    },
    "intensiv": {
        "name": "Intensiv-Integrationskurs",
        "ue": "430 UE Sprachkurs + 30 UE Orientierungskurs",
        "zielgruppe": "Lernstarke Teilnehmer mit schnellem Lernerfolg",
        "niveau_ziel": "B1",
        "kosten": "Ca. 1,95 € / UE",
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "Antrag auf Zulassung Intensivkurs (BAMF-Formular 101)",
            "Einstufungstest beim Kursträger",
        ],
    },
    "frauen": {
        "name": "Frauen- / Elternkurs",
        "ue": "660 UE Sprachkurs + 100 UE Orientierungskurs",
        "zielgruppe": "Frauen mit Kinderbetreuungsbedarf / Elternteile",
        "niveau_ziel": "B1",
        "kosten": "Ca. 1,95 € / UE (Kostenübernahme Kinderbetreuung möglich)",
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "Antrag auf Zulassung Frauenkurs (BAMF-Formular 101)",
            "Nachweis Kinderbetreuungsbedarf (Geburtsurkunde Kind)",
        ],
    },
    "jugend": {
        "name": "Jugend-Integrationskurs",
        "ue": "900 UE Sprachkurs + 100 UE Orientierungskurs",
        "zielgruppe": "Junge Erwachsene unter 27 Jahren",
        "niveau_ziel": "B1",
        "kosten": "Ca. 1,95 € / UE",
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "Antrag auf Zulassung Jugendkurs (BAMF-Formular 101)",
            "Altersnachweis (unter 27 Jahre)",
        ],
    },
}

# ---------------------------------------------------------------------------
# Förderprogramme – vollständige Übersicht
# ---------------------------------------------------------------------------

PROGRAMME = {
    "Berufssprachkurs (BSK)": {
        "beschreibung": (
            "Berufssprachkurse nach § 45a AufenthG / DeuFöV. "
            "Speziell für die berufliche Integration in Deutschland. "
            "Spezialkurse für Pflege/Medizin mit 900 UE, Standardkurse mit 510 UE, "
            "Fachkurse (B2–C1) mit 400 UE."
        ),
        "foerderer": "BAMF",
        "kosten": "Ca. 2,07 € / UE Eigenanteil (bei Hartz-IV-Bezug: kostenfrei)",
        "niveau": ["A2", "B1", "B2", "C1"],
        "antrag_stelle": "BAMF-Kursträger vor Ort (bamf.de/kurstraeger)",
        "pflicht_dokumente": [
            "Reisepass (Kopie, alle Seiten)",
            "Aufenthaltstitel (Kopie, Vorder- und Rückseite)",
            "Arbeitsvertrag ODER Arbeitgeberbestätigung",
            "Einstufungstest beim Kursträger (wird dort durchgeführt)",
            "BAMF-Antragsformular (Nummer je nach Modul – siehe oben)",
        ],
    },
    "Integrationskurs": {
        "beschreibung": (
            "Sprach- und Orientierungskurs nach § 43 AufenthG / IntV. "
            "Verschiedene Kurstypen: Allgemein, Alphabetisierung, Intensiv, "
            "Frauen-/Elternkurs, Jugendkurs."
        ),
        "foerderer": "BAMF",
        "kosten": "Ca. 1,95 € / UE (Erlass bei geringem Einkommen möglich)",
        "niveau": ["A1", "A2"],
        "antrag_stelle": "BAMF direkt oder über Ausländerbehörde",
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "BAMF-Formular 101 (Antrag auf Zulassung)",
            "Berechtigungsschein der Ausländerbehörde (falls ausgestellt)",
        ],
    },
    "FbD – Förderung berufsbez. Deutschkenntnisse": {
        "beschreibung": (
            "ESF-gefördertes BAMF-Programm. Für Beschäftigte und Arbeitssuchende "
            "mit Bedarf an berufsbezogenem Deutsch (Niveau A2–C1). "
            "Ergänzt den BSK und ist oft kombinierbar."
        ),
        "foerderer": "BAMF / ESF",
        "kosten": "Kostenfrei für Teilnehmende",
        "niveau": ["A2", "B1", "B2", "C1"],
        "antrag_stelle": "FbD-Kursträger (bamf.de/fbd)",
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "Nachweis der Beschäftigung ODER Jobcenter-/AA-Bescheinigung",
            "Sprachnachweis (Zertifikat oder Einstufungstest)",
            "Anerkennungsbescheid ODER Nachweis laufendes Anerkennungsverfahren",
        ],
    },
    "§ 421 SGB III – Sprachkurs über Agentur für Arbeit": {
        "beschreibung": (
            "Förderung von Deutschkursen über die Bundesagentur für Arbeit "
            "für arbeitssuchend gemeldete Personen (Bildungsgutschein)."
        ),
        "foerderer": "Agentur für Arbeit / Jobcenter",
        "kosten": "Kostenfrei (Bildungsgutschein)",
        "niveau": ["A1", "A2", "B1", "B2"],
        "antrag_stelle": "Zuständige Agentur für Arbeit / Jobcenter",
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "Beratungsgespräch beim Arbeitsberater (Termin vereinbaren)",
            "Nachweis der Arbeitsuche / Arbeitslosigkeit",
            "Bildungsgutschein (wird bei Bewilligung ausgestellt)",
        ],
    },
    "Berufliche Weiterbildung – IQ Netzwerk": {
        "beschreibung": (
            "Kostenloses Beratungsangebot zur Anerkennung ausländischer Berufsabschlüsse "
            "und zu Qualifizierungsmaßnahmen (Nachqualifizierung, Anpassungsqualifizierung). "
            "Besonders relevant bei laufendem oder noch nicht beantragtem Anerkennungsverfahren."
        ),
        "foerderer": "IQ Netzwerk / BMAS / ESF",
        "kosten": "Beratung kostenfrei; Qualifizierungsmaßnahmen ggf. über AVGS oder Bildungsgutschein",
        "niveau": ["alle"],
        "antrag_stelle": "Nächste IQ-Beratungsstelle (netzwerk-iq.de)",
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "Ausländischer Berufsabschluss / Zeugnisse (Original + beglaubigte Übersetzung)",
            "Anerkennungsbescheid oder laufender Bescheid der zuständigen Stelle",
            "Lebenslauf (auf Deutsch)",
        ],
    },
    "Nachqualifizierung / Anpassungsqualifizierung": {
        "beschreibung": (
            "Gezielte berufliche Nachqualifizierung, um fehlende Kompetenzen zum deutschen "
            "Berufsabschluss zu ergänzen (v.a. Pflege, Medizin, Handwerk, Erziehung). "
            "Wird durch AVGS (Aktivierungs- und Vermittlungsgutschein) oder "
            "Bildungsgutschein der AA gefördert."
        ),
        "foerderer": "Agentur für Arbeit / Jobcenter / ESF",
        "kosten": "Kostenfrei bei Bewilligung über Bildungsgutschein / AVGS",
        "niveau": ["alle"],
        "antrag_stelle": "Agentur für Arbeit (nach IQ-Beratung)",
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "Anerkennungsbescheid mit Feststellung fehlender Kompetenzen (Defizitbescheid)",
            "Lebenslauf (auf Deutsch)",
            "Ausländische Berufsabschlüsse + beglaubigte Übersetzung",
            "Bildungsgutschein oder AVGS (wird von der AA ausgestellt)",
        ],
    },
}

SPRACHNIVEAU_RANG = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

# ---------------------------------------------------------------------------
# Integrationskurs-Typ ermitteln
# ---------------------------------------------------------------------------

def _waehle_integrationskurs_typ(niveau_rang: int, zeile: pd.Series) -> dict:
    """Wählt den passenden Integrationskurstyp basierend auf Kandidatenprofil."""
    alphabetisierung = str(zeile.get("alphabetisierungsbedarf", "nein")).strip().lower() in (
        "ja", "yes", "true", "1"
    )
    geschlecht = str(zeile.get("geschlecht", "")).strip().lower()
    geburtsdatum_raw = str(zeile.get("geburtsdatum", "")).strip()

    if alphabetisierung:
        return INTEGRATIONSKURS_TYPEN["alphabetisierung"]

    alter = None
    if geburtsdatum_raw:
        try:
            geb = datetime.strptime(geburtsdatum_raw, "%Y-%m-%d").date()
            alter = (date.today() - geb).days // 365
        except ValueError:
            pass

    if alter is not None and alter < 27:
        return INTEGRATIONSKURS_TYPEN["jugend"]

    if geschlecht in ("w", "weiblich", "female", "f"):
        return INTEGRATIONSKURS_TYPEN["frauen"]

    # Lernstarke Kandidaten (A2) → Intensivkurs vorschlagen
    if niveau_rang == 2:
        return INTEGRATIONSKURS_TYPEN["intensiv"]

    return INTEGRATIONSKURS_TYPEN["allgemein"]


# ---------------------------------------------------------------------------
# BSK-Modul ermitteln
# ---------------------------------------------------------------------------

def _waehle_bsk_modul(berufsfeld: str, niveau_rang: int) -> tuple:
    """Gibt (Modulname, UE, Niveau, Formular) zurück."""
    modul = BSK_MODULE.get(berufsfeld, BSK_DEFAULT)
    # B2+ Kandidaten ohne Spezialkurs → Fachkurs empfehlen
    if niveau_rang >= 4 and modul == BSK_DEFAULT:
        return ("BSK-Fachkurs", "400 UE", "B2–C1", "BAMF-Formular 540")
    return modul


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
        modulname, ue, niv_ziel, formular = _waehle_bsk_modul(berufsfeld, niveau_rang)
        prog = dict(PROGRAMME["Berufssprachkurs (BSK)"])
        prog["pflicht_dokumente"] = [
            d if "Formular" not in d else f"BAMF-Antragsformular ({formular})"
            for d in prog["pflicht_dokumente"]
        ]
        berechtigte_programme.append({
            "name": "Berufssprachkurs (BSK)",
            "details": prog,
            "empfohlenes_modul": f"{modulname} – {ue} – Zielniveau {niv_ziel}",
        })

    # --- Integrationskurs ---
    if niveau_rang <= 2:
        kurstyp = _waehle_integrationskurs_typ(niveau_rang, zeile)
        prog = dict(PROGRAMME["Integrationskurs"])
        prog["pflicht_dokumente"] = kurstyp["pflicht_dokumente"]
        prog["kosten"] = kurstyp["kosten"]
        berechtigte_programme.append({
            "name": f"Integrationskurs – {kurstyp['name']}",
            "details": prog,
            "empfohlenes_modul": (
                f"{kurstyp['name']} | {kurstyp['ue']} | "
                f"Zielniveau {kurstyp['niveau_ziel']} | {kurstyp['zielgruppe']}"
            ),
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
        prog = dict(PROGRAMME["FbD – Förderung berufsbez. Deutschkenntnisse"])
        if extra_dokumente:
            prog["pflicht_dokumente"] = prog["pflicht_dokumente"] + extra_dokumente
        berechtigte_programme.append({
            "name": "FbD – Förderung berufsbez. Deutschkenntnisse",
            "details": prog,
            "empfohlenes_modul": f"FbD-Kurs (kombinierbar mit BSK) – Niveau {niveau}–C1",
        })

    # --- § 421 SGB III ---
    if not beschaeftigt:
        berechtigte_programme.append({
            "name": "§ 421 SGB III – Sprachkurs über Agentur für Arbeit",
            "details": PROGRAMME["§ 421 SGB III – Sprachkurs über Agentur für Arbeit"],
            "empfohlenes_modul": "Bildungsgutschein beantragen (Beratungsgespräch bei AA vereinbaren)",
        })
        hinweise.append(
            "§ 421 SGB III: Kandidat muss sich als arbeitssuchend bei der Agentur für Arbeit melden."
        )

    # --- IQ Netzwerk (immer relevant wenn Anerkennung offen) ---
    if anerkennung in ("nicht beantragt", "laufend"):
        berechtigte_programme.append({
            "name": "Berufliche Weiterbildung – IQ Netzwerk",
            "details": PROGRAMME["Berufliche Weiterbildung – IQ Netzwerk"],
            "empfohlenes_modul": (
                "Anerkennungsberatung → netzwerk-iq.de"
                + (" | Anerkennungsverfahren einleiten!" if anerkennung == "nicht beantragt"
                   else " | Verfahren begleiten lassen")
            ),
        })

    # --- Nachqualifizierung (wenn Defizitbescheid vorliegt / laufend) ---
    if anerkennung == "laufend":
        berechtigte_programme.append({
            "name": "Nachqualifizierung / Anpassungsqualifizierung",
            "details": PROGRAMME["Nachqualifizierung / Anpassungsqualifizierung"],
            "empfohlenes_modul": (
                f"Anpassungsqualifizierung im Berufsfeld {berufsfeld} "
                f"(nach Defizitbescheid der Anerkennungsstelle)"
            ),
        })

    # --- Allgemeine Hinweise ---
    if "blaue karte" in aufenthaltstitel.lower():
        hinweise.append(
            "Blaue Karte EU: Niederlassungserlaubnis bereits nach 21 Monaten mit B1-Nachweis "
            "(§ 18c Abs. 3 AufenthG) – BSK-Abschluss strategisch nutzen!"
        )

    if berufsfeld in ("Pflege", "Altenpflege", "Krankenpflege", "Medizin", "Arztpraxis"):
        hinweise.append(
            f"Reglementierter Beruf ({berufsfeld}): Berufserlaubnis / Berufsanerkennung "
            "ist Pflichtvoraussetzung für Beschäftigung – bitte Anerkennungsstatus prüfen."
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
