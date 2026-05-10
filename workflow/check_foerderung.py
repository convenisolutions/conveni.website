"""
Förderberechtigungs-Prüfung – Sprachkurse, Anerkennung & Arbeitgeberförderung
Grundlagen: DeuFöV, § 43/45a AufenthG, § 421/82/88 SGB III, IntV, BQFG, IQ-Netzwerk
Zielgruppe: Fachkräfte aus Drittstaaten (Philippinen, Vietnam)
"""

import pandas as pd
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

# ===========================================================================
# BSK-MODULE (DeuFöV / BAMF) – (Modulname, UE, Zielniveau, Antragsformular)
# ===========================================================================

BSK_MODULE = {
    "Pflege":          ("BSK-Spezialkurs Pflege",    "900 UE", "A2–B2+", "BAMF-Formular 600-P"),
    "Altenpflege":     ("BSK-Spezialkurs Pflege",    "900 UE", "A2–B2+", "BAMF-Formular 600-P"),
    "Krankenpflege":   ("BSK-Spezialkurs Pflege",    "900 UE", "A2–B2+", "BAMF-Formular 600-P"),
    "Medizin":         ("BSK-Spezialkurs Medizin",   "900 UE", "B1–C1",  "BAMF-Formular 600-M"),
    "Arztpraxis":      ("BSK-Spezialkurs Medizin",   "900 UE", "B1–C1",  "BAMF-Formular 600-M"),
    "Zahnmedizin":     ("BSK-Spezialkurs Medizin",   "900 UE", "B1–C1",  "BAMF-Formular 600-M"),
    "Erziehung":       ("BSK-Spezialkurs Pädagogik", "900 UE", "A2–B2",  "BAMF-Formular 600"),
    "Sozialpädagogik": ("BSK-Spezialkurs Pädagogik", "900 UE", "A2–B2",  "BAMF-Formular 600"),
    "Sozialarbeit":    ("BSK-Spezialkurs Pädagogik", "900 UE", "A2–B2",  "BAMF-Formular 600"),
    "Handwerk":        ("BSK-Standardkurs",          "510 UE", "A2–B1",  "BAMF-Formular 540"),
    "Bau":             ("BSK-Standardkurs",          "510 UE", "A2–B1",  "BAMF-Formular 540"),
    "Elektro":         ("BSK-Standardkurs",          "510 UE", "A2–B1",  "BAMF-Formular 540"),
    "Metall":          ("BSK-Standardkurs",          "510 UE", "A2–B1",  "BAMF-Formular 540"),
    "Logistik":        ("BSK-Standardkurs",          "510 UE", "A2–B1",  "BAMF-Formular 540"),
    "Gastronomie":     ("BSK-Standardkurs",          "510 UE", "A2–B1",  "BAMF-Formular 540"),
    "Einzelhandel":    ("BSK-Standardkurs",          "510 UE", "A2–B1",  "BAMF-Formular 540"),
    "Transport":       ("BSK-Standardkurs",          "510 UE", "A2–B1",  "BAMF-Formular 540"),
    "Reinigung":       ("BSK-Standardkurs",          "510 UE", "A2–B1",  "BAMF-Formular 540"),
    "IT":              ("BSK-Fachkurs",              "400 UE", "B2–C1",  "BAMF-Formular 540"),
    "Ingenieur":       ("BSK-Fachkurs",              "400 UE", "B2–C1",  "BAMF-Formular 540"),
    "Kaufmännisch":    ("BSK-Fachkurs",              "400 UE", "B2–C1",  "BAMF-Formular 540"),
    "Finanz":          ("BSK-Fachkurs",              "400 UE", "B2–C1",  "BAMF-Formular 540"),
    "Verwaltung":      ("BSK-Fachkurs",              "400 UE", "B2–C1",  "BAMF-Formular 540"),
}
BSK_DEFAULT = ("BSK-Standardkurs", "510 UE", "A2–B1", "BAMF-Formular 540")

BSK_EIGENANTEIL_PRO_UE = 2.07
BSK_GESAMTKOSTEN_PRO_UE_EST = 12.50

# ===========================================================================
# INTEGRATIONSKURS-VARIANTEN (§ 43 AufenthG / IntV)
# ===========================================================================

INTEGRATIONSKURS_TYPEN = {
    "alphabetisierung": {
        "name": "Alphabetisierungskurs",
        "ue": "900 UE Sprachkurs + 100 UE Orientierungskurs",
        "zielgruppe": "Personen ohne lateinische Schriftkenntnisse",
        "niveau_ziel": "A2–B1",
        "kosten_pro_ue": 1.95,
        "ue_zahl": 1000,
        "kosten": "Ca. 1,95 € / UE (Erlass bei geringem Einkommen möglich)",
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "BAMF-Antrag Alphabetisierungskurs (Formular 101-Alpha)",
            "Berechtigungsschein der Ausländerbehörde",
            "Einstufung durch Kursträger (bestätigt Bedarf)",
        ],
    },
    "jugend": {
        "name": "Jugend-Integrationskurs",
        "ue": "900 UE Sprachkurs + 100 UE Orientierungskurs",
        "zielgruppe": "Junge Erwachsene unter 27 Jahren",
        "niveau_ziel": "B1",
        "kosten_pro_ue": 1.95,
        "ue_zahl": 1000,
        "kosten": "Ca. 1,95 € / UE",
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "BAMF-Antrag Jugendkurs (Formular 101)",
            "Altersnachweis (unter 27 Jahre)",
        ],
    },
    "frauen": {
        "name": "Frauen- / Elternkurs",
        "ue": "660 UE Sprachkurs + 100 UE Orientierungskurs",
        "zielgruppe": "Frauen mit Kinderbetreuungsbedarf",
        "niveau_ziel": "B1",
        "kosten_pro_ue": 1.95,
        "ue_zahl": 760,
        "kosten": "Ca. 1,95 € / UE (Kinderbetreuungskosten ggf. erstattbar)",
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "BAMF-Antrag Frauenkurs (Formular 101)",
            "Nachweis Kinderbetreuungsbedarf (Geburtsurkunde Kind)",
        ],
    },
    "intensiv": {
        "name": "Intensiv-Integrationskurs",
        "ue": "430 UE Sprachkurs + 30 UE Orientierungskurs",
        "zielgruppe": "Lernstarke Teilnehmer mit schnellem Lernerfolg",
        "niveau_ziel": "B1",
        "kosten_pro_ue": 1.95,
        "ue_zahl": 460,
        "kosten": "Ca. 1,95 € / UE",
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "BAMF-Antrag Intensivkurs (Formular 101)",
            "Einstufungstest beim Kursträger",
        ],
    },
    "allgemein": {
        "name": "Allgemeiner Integrationskurs",
        "ue": "660 UE Sprachkurs + 100 UE Orientierungskurs",
        "zielgruppe": "Drittstaatsangehörige, Grundkenntnisse A1–A2",
        "niveau_ziel": "B1",
        "kosten_pro_ue": 1.95,
        "ue_zahl": 760,
        "kosten": "Ca. 1,95 € / UE (Erlass bei geringem Einkommen möglich)",
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel / Niederlassungserlaubnis (Kopie)",
            "BAMF-Antrag Integrationskurs (Formular 101)",
            "Berechtigungsschein der Ausländerbehörde (falls ausgestellt)",
        ],
    },
}

# ===========================================================================
# AUFENTHALTSWEG – § AufenthG Analyse
# ===========================================================================

AUFENTHALTSWEG_MAP = {
    "§ 16d": {
        "bezeichnung": "Anerkennungsaufenthalt (§ 16d AufenthG)",
        "beschreibung": "Für Drittstaatsangehörige zur Durchführung des Anerkennungsverfahrens und ggf. Qualifizierung in Deutschland.",
        "max_dauer": "Bis zu 2 Jahre (verlängerbar)",
        "beschaeftigung": "Im Anerkennungsbereich erlaubt (eingeschränkt)",
        "niederlassungserlaubnis_nach": "Wechsel zu § 18a/18b nach Anerkennung → dann 2–4 Jahre",
        "sprachziel_niederlassung": "B1",
        "besonderheiten": [
            "Qualifizierungsmaßnahmen sind ausdrücklich erlaubt und erwünscht",
            "BSK und FbD können parallel zum Anerkennungsverfahren genutzt werden",
            "Sprachkurse können von der ABH verpflichtend angeordnet werden",
        ],
        "naechster_schritt": "Anerkennungsverfahren abschließen → Aufenthaltstitel wechseln zu § 18a oder § 18b",
    },
    "§ 18a": {
        "bezeichnung": "Fachkraft mit Berufsausbildung (§ 18a AufenthG)",
        "beschreibung": "Für Personen mit in Deutschland anerkanntem, nicht-akademischen Berufsabschluss.",
        "max_dauer": "4 Jahre (verlängerbar)",
        "beschaeftigung": "Beliebige qualifizierte Beschäftigung",
        "niederlassungserlaubnis_nach": "4 Jahre regulär – oder 2 Jahre mit: B1-Nachweis + Vollzeitarbeit + 60 Monate Rentenversicherung",
        "sprachziel_niederlassung": "B1 (verkürzt auf 2 Jahre!)",
        "besonderheiten": [
            "B1-Nachweis halbiert die Wartezeit auf die Niederlassungserlaubnis",
            "Berufswechsel nach 2 Jahren möglich (Zustimmung der ABH)",
            "Familiennachzug möglich",
        ],
        "naechster_schritt": "B1-Sprachkurs priorisieren → Niederlassungserlaubnis § 9 bereits nach 2 Jahren möglich",
    },
    "§ 18b": {
        "bezeichnung": "Fachkraft mit akademischem Abschluss (§ 18b AufenthG)",
        "beschreibung": "Für Personen mit in Deutschland anerkanntem Hochschulabschluss.",
        "max_dauer": "4 Jahre (verlängerbar)",
        "beschaeftigung": "Beliebige qualifizierte Beschäftigung",
        "niederlassungserlaubnis_nach": "4 Jahre regulär – oder 2 Jahre mit B1 + Vollzeitarbeit",
        "sprachziel_niederlassung": "B1",
        "besonderheiten": [
            "Blaue Karte EU prüfen – ggf. vorteilhafter (NE nach 21 Monaten!)",
            "Familiennachzug möglich ohne Wartezeit",
        ],
        "naechster_schritt": "Blaue Karte EU prüfen (Gehaltsgrenze ca. 45.300 €/Jahr) – oder NE nach 2 Jahren mit B1",
    },
    "blaue karte": {
        "bezeichnung": "Blaue Karte EU (§ 18c AufenthG)",
        "beschreibung": "Für Hochschulabsolventen mit Mindestgehalt (2025: ca. 45.300 €/Jahr brutto; Mangelberufe MINT/Pflege: ca. 35.100 €/Jahr).",
        "max_dauer": "4 Jahre",
        "beschaeftigung": "Tätigkeitsbereich des Abschlusses (erste 2 Jahre)",
        "niederlassungserlaubnis_nach": "21 Monate mit B1-Nachweis – oder 33 Monate ohne Sprachnachweis",
        "sprachziel_niederlassung": "B1 spart 12 Monate – DRINGEND empfohlen!",
        "besonderheiten": [
            "Familiennachzug sofort, ohne Wartezeit",
            "EU-Mobilität: nach 18 Monaten Arbeit in anderen EU-Staaten erlaubt",
            "B1-Zertifikat spart 12 Monate bis zur Niederlassungserlaubnis",
            "Günstigste Route zu Niederlassungserlaubnis aller Aufenthaltstitel",
        ],
        "naechster_schritt": "BSK/FbD sofort starten → B1-Zertifikat anstreben → NE nach 21 Monaten beantragen",
    },
    "§ 19": {
        "bezeichnung": "Niederlassungserlaubnis (§ 9 / § 19 AufenthG)",
        "beschreibung": "Unbefristetes Aufenthaltsrecht – höchste Aufenthaltsform.",
        "max_dauer": "Unbefristet",
        "beschaeftigung": "Beliebig",
        "niederlassungserlaubnis_nach": "Bereits vorhanden",
        "sprachziel_niederlassung": "Bereits erfüllt",
        "besonderheiten": [
            "Einbürgerung nach 5 Jahren möglich (§ 10 StAG), bei besonderem Engagement 3 Jahre",
            "B2-Kenntnisse können Einbürgerungsverfahren beschleunigen",
        ],
        "naechster_schritt": "Einbürgerungsvoraussetzungen prüfen – B2-Kurs für beschleunigte Einbürgerung empfohlen",
    },
}

# ===========================================================================
# ANERKENNUNGSSTELLEN nach Berufsfeld
# ===========================================================================

ANERKENNUNGSSTELLEN = {
    "Pflege": {
        "stelle_typ": "Landesamt für Gesundheit (Bundesland-abhängig)",
        "beispiele": "Bayern: ZBFS | NRW: BezReg Münster | BW: Regierungspräsidium | Berlin: LaGeSo",
        "verfahren": "Gleichwertigkeitsprüfung → bei Defiziten: Kenntnisprüfung (KSP) oder Anpassungslehrgang",
        "dauer": "3–6 Monate",
        "kosten": "Ca. 100–400 € (Bundesland-abhängig)",
        "reglementiert": True,
        "portal": "anerkennung-in-deutschland.de",
        "hinweis": "Für PHL/VNM: Teildokumentenanerkennung und Kenntnisprüfung häufig notwendig. Berufserlaubnis (§ 2 KrPflG) als Zwischenlösung möglich.",
    },
    "Altenpflege": {
        "stelle_typ": "Landesamt für Gesundheit / Regierungspräsidium",
        "beispiele": "Bayern: ZBFS | NRW: BezReg Münster | BW: Regierungspräsidium",
        "verfahren": "Gleichwertigkeitsprüfung → ggf. Anpassungslehrgang oder Kenntnisprüfung",
        "dauer": "3–6 Monate",
        "kosten": "Ca. 100–400 €",
        "reglementiert": True,
        "portal": "anerkennung-in-deutschland.de",
        "hinweis": "Seit 01.01.2020 gilt das Pflegeberufegesetz: Altenpflege, Kinderkrankenpflege und Gesundheits-/Krankenpflege sind zusammengeführt.",
    },
    "Krankenpflege": {
        "stelle_typ": "Landesamt für Gesundheit",
        "beispiele": "Bayern: ZBFS | NRW: BezReg Münster",
        "verfahren": "Gleichwertigkeitsprüfung → Kenntnisprüfung oder Anpassungslehrgang",
        "dauer": "3–6 Monate",
        "kosten": "Ca. 100–350 €",
        "reglementiert": True,
        "portal": "anerkennung-in-deutschland.de",
        "hinweis": "Vorläufige Berufserlaubnis möglich, um bereits während des Verfahrens zu arbeiten.",
    },
    "Medizin": {
        "stelle_typ": "Zuständige Landesärztekammer",
        "beispiele": "Bayerische LÄK | Ärztekammer NRW | Ärztekammer Hamburg | LÄK Baden-Württemberg",
        "verfahren": "Approbation (§ 3 BÄO) – bei Drittstaaten: Gleichwertigkeitsprüfung + ggf. Kenntnisprüfung",
        "dauer": "6–18 Monate",
        "kosten": "Ca. 300–700 €",
        "reglementiert": True,
        "portal": "bundesaerztekammer.de",
        "hinweis": "Vor Antrag: Alle Dokumente beglaubigt übersetzen lassen. Berufserlaubnis (§ 10 BÄO) als Zwischenlösung für max. 2 Jahre. B2-Niveau oft Voraussetzung für Approbation.",
    },
    "Arztpraxis": {
        "stelle_typ": "Zuständige Landesärztekammer",
        "verfahren": "Approbation (§ 3 BÄO)",
        "dauer": "6–18 Monate",
        "kosten": "Ca. 300–700 €",
        "reglementiert": True,
        "portal": "bundesaerztekammer.de",
        "hinweis": "Siehe Medizin. B2-Sprachnachweis ist Pflichtvoraussetzung.",
    },
    "Erziehung": {
        "stelle_typ": "Zuständiges Landesjugendamt / Kultusministerium",
        "beispiele": "Bayern: StMAS | NRW: MKJFGFI | BW: KM BW",
        "verfahren": "Gleichwertigkeitsprüfung nach BQFG → ggf. Anpassungsqualifizierung",
        "dauer": "2–4 Monate",
        "kosten": "Ca. 50–200 €",
        "reglementiert": True,
        "portal": "anerkennung-in-deutschland.de",
    },
    "Handwerk": {
        "stelle_typ": "Handwerkskammer (HWK) im zuständigen Bezirk",
        "beispiele": "HWK München | HWK Düsseldorf | HWK Hamburg | HWK Berlin",
        "verfahren": "Gleichwertigkeitsprüfung nach BQFG; bei Meisterberufen: evtl. Meisterprüfung",
        "dauer": "2–4 Monate",
        "kosten": "Ca. 100–300 €",
        "reglementiert": False,
        "portal": "anerkennung-in-deutschland.de",
        "hinweis": "Für zulassungspflichtige Handwerke (Anlage A HwO) ist Gleichwertigkeit mit HWK erforderlich.",
    },
    "Bau": {
        "stelle_typ": "Handwerkskammer (HWK) oder IHK",
        "verfahren": "Gleichwertigkeitsprüfung nach BQFG",
        "dauer": "2–4 Monate",
        "kosten": "Ca. 100–250 €",
        "reglementiert": False,
        "portal": "anerkennung-in-deutschland.de",
    },
    "Elektro": {
        "stelle_typ": "Handwerkskammer (HWK)",
        "verfahren": "Gleichwertigkeitsprüfung nach BQFG",
        "dauer": "2–4 Monate",
        "kosten": "Ca. 100–250 €",
        "reglementiert": False,
        "portal": "anerkennung-in-deutschland.de",
    },
    "IT": {
        "stelle_typ": "Keine formale Anerkennung nötig (nicht reglementiert)",
        "verfahren": "Direkteinstieg möglich – ggf. informelle Kompetenzfeststellung über IHK",
        "dauer": "–",
        "kosten": "0 €",
        "reglementiert": False,
        "portal": "–",
        "hinweis": "IT-Berufe sind nicht reglementiert. Ausländische Zeugnisse können zum Nachweis vorgelegt werden, sind aber nicht zwingend notwendig.",
    },
    "Ingenieur": {
        "stelle_typ": "ENIC/NARIC-Stelle (Kultusministerkonferenz) + ggf. Ingenieurkammer",
        "beispiele": "anabin-Datenbank (KMK) für Hochschulabschlüsse",
        "verfahren": "Akademische Anerkennung über KMK/anabin; Berufsanerkennung über Ingenieurkammer (bundeslandabhängig)",
        "dauer": "2–4 Monate",
        "kosten": "Ca. 100–300 €",
        "reglementiert": False,
        "portal": "anabin.kmk.org",
    },
    "Kaufmännisch": {
        "stelle_typ": "IHK (Industrie- und Handelskammer)",
        "beispiele": "IHK München | IHK NRW | IHK Berlin",
        "verfahren": "Gleichwertigkeitsprüfung nach BQFG",
        "dauer": "2–3 Monate",
        "kosten": "Ca. 50–200 €",
        "reglementiert": False,
        "portal": "anerkennung-in-deutschland.de",
    },
    "Gastronomie": {
        "stelle_typ": "IHK oder Handwerkskammer (je nach Tätigkeit)",
        "verfahren": "Gleichwertigkeitsprüfung (optional, da nicht reglementiert)",
        "dauer": "1–3 Monate",
        "kosten": "Ca. 50–150 €",
        "reglementiert": False,
        "portal": "anerkennung-in-deutschland.de",
    },
    "Logistik": {
        "stelle_typ": "IHK",
        "verfahren": "Gleichwertigkeitsprüfung nach BQFG",
        "dauer": "2–3 Monate",
        "kosten": "Ca. 50–200 €",
        "reglementiert": False,
        "portal": "anerkennung-in-deutschland.de",
    },
}
ANERKENNUNGSSTELLE_DEFAULT = {
    "stelle_typ": "IHK oder zuständige Kammer (je nach Berufsfeld prüfen)",
    "verfahren": "Gleichwertigkeitsprüfung nach BQFG",
    "dauer": "2–4 Monate",
    "kosten": "Ca. 100–300 €",
    "reglementiert": False,
    "portal": "anerkennung-in-deutschland.de",
}

REGLEMENTIERTE_BERUFE = {
    "Pflege", "Altenpflege", "Krankenpflege", "Medizin", "Arztpraxis", "Zahnmedizin",
    "Erziehung", "Sozialpädagogik",
}

# ===========================================================================
# FÖRDERPROGRAMME – vollständige Übersicht
# ===========================================================================

PROGRAMME = {
    "Berufssprachkurs (BSK)": {
        "beschreibung": (
            "Berufssprachkurse nach § 45a AufenthG / DeuFöV. Berufsfeld-spezifische Module: "
            "Pflege/Medizin 900 UE, Standard 510 UE, Fachkurs (B2–C1) 400 UE."
        ),
        "foerderer": "BAMF",
        "kosten": "Ca. 2,07 € / UE Eigenanteil (bei ALG-II: kostenfrei)",
        "antrag_stelle": "BAMF-Kursträger vor Ort (bamf.de/servicenummer: 0800 8 67467)",
        "niveau": ["A2", "B1", "B2", "C1"],
        "pflicht_dokumente": [
            "Reisepass (Kopie, alle Seiten)",
            "Aufenthaltstitel (Kopie, Vorder- und Rückseite)",
            "Arbeitsvertrag ODER Arbeitgeberbestätigung",
            "Einstufungstest beim Kursträger (wird dort durchgeführt)",
            "BAMF-Antragsformular (Nummer je nach Modul)",
        ],
    },
    "Integrationskurs": {
        "beschreibung": (
            "Sprach- und Orientierungskurs nach § 43 AufenthG / IntV. Varianten: "
            "Allgemein, Alphabetisierung, Intensiv, Frauen-/Elternkurs, Jugendkurs."
        ),
        "foerderer": "BAMF",
        "kosten": "Ca. 1,95 € / UE (Erlass bei geringem Einkommen möglich)",
        "antrag_stelle": "BAMF direkt (bamf.de) oder über Ausländerbehörde",
        "niveau": ["A1", "A2"],
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "BAMF-Formular 101 (Antrag auf Zulassung)",
            "Berechtigungsschein der Ausländerbehörde (falls ausgestellt)",
        ],
    },
    "FbD – Förderung berufsbez. Deutschkenntnisse": {
        "beschreibung": (
            "ESF-gefördertes BAMF-Programm (kostenfrei). Für Beschäftigte und Arbeitssuchende "
            "A2–C1. Ideal in Kombination mit BSK."
        ),
        "foerderer": "BAMF / ESF",
        "kosten": "Kostenfrei für Teilnehmende",
        "antrag_stelle": "FbD-Kursträger (bamf.de/fbd)",
        "niveau": ["A2", "B1", "B2", "C1"],
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
        "antrag_stelle": "Zuständige Agentur für Arbeit / Jobcenter",
        "niveau": ["A1", "A2", "B1", "B2"],
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "Beratungsgespräch beim Arbeitsberater (Termin vereinbaren)",
            "Nachweis der Arbeitsuche / Arbeitslosigkeit",
            "Bildungsgutschein (wird bei Bewilligung ausgestellt)",
        ],
    },
    "IQ Netzwerk – Anerkennungsberatung": {
        "beschreibung": (
            "Kostenlose, neutrale Beratung zur Anerkennung ausländischer Berufsabschlüsse, "
            "zum Ablauf des Anerkennungsverfahrens und zu Qualifizierungsmaßnahmen."
        ),
        "foerderer": "IQ Netzwerk / BMAS / ESF",
        "kosten": "Kostenfrei",
        "antrag_stelle": "Nächste IQ-Beratungsstelle (netzwerk-iq.de) – telefonisch, online oder vor Ort",
        "niveau": ["alle"],
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "Ausländischer Berufsabschluss / Zeugnisse (Original + beglaubigte Übersetzung)",
            "Lebenslauf (auf Deutsch)",
        ],
    },
    "Nachqualifizierung / Anpassungsqualifizierung": {
        "beschreibung": (
            "Gezielte berufliche Nachqualifizierung zum Schließen von Kompetenzlücken, "
            "die im Anerkennungsbescheid (Defizitbescheid) festgestellt wurden. "
            "Finanzierung über AVGS oder Bildungsgutschein der Agentur für Arbeit."
        ),
        "foerderer": "Agentur für Arbeit / Jobcenter / ESF",
        "kosten": "Kostenfrei bei Bewilligung über Bildungsgutschein / AVGS",
        "antrag_stelle": "Agentur für Arbeit (nach IQ-Beratung und Defizitbescheid)",
        "niveau": ["alle"],
        "pflicht_dokumente": [
            "Reisepass (Kopie)",
            "Aufenthaltstitel (Kopie)",
            "Anerkennungsbescheid mit Defizitfeststellung",
            "Lebenslauf (auf Deutsch)",
            "Ausländische Berufsabschlüsse + beglaubigte Übersetzung",
            "Bildungsgutschein oder AVGS (wird von der AA ausgestellt)",
        ],
    },
    "Qualifizierungschancengesetz (§ 82 SGB III)": {
        "beschreibung": (
            "Arbeitgeberförderung: Zuschuss zu Lehrgangskosten UND Lohnkostenzuschuss während "
            "der Weiterbildung. Staffelung nach Betriebsgröße. Antrag VOR Kursstart stellen!"
        ),
        "foerderer": "Agentur für Arbeit",
        "kosten": "Für Arbeitgeber: Restbetrag nach Förderung (je nach Betriebsgröße)",
        "antrag_stelle": "Zuständige Agentur für Arbeit (Arbeitgeber stellt Antrag VOR Kursstart)",
        "niveau": ["alle"],
        "foerder_staffel": {
            "klein":  {"label": "Klein (<10 MA)",    "lehrgang": "100%", "lohn": "75%"},
            "mittel": {"label": "Mittel (10–249 MA)", "lehrgang": "50%",  "lohn": "50%"},
            "gross":  {"label": "Groß (≥250 MA)",     "lehrgang": "25%",  "lohn": "25%"},
        },
        "pflicht_dokumente": [
            "Antrag des Arbeitgebers bei der AA VOR Kursbeginn",
            "Weiterbildungsvertrag / Kursangebot mit Kosten",
            "Nachweis Betriebsgröße",
            "Arbeitsvertrag des Arbeitnehmers",
        ],
    },
    "Eingliederungszuschuss (§ 88 SGB III)": {
        "beschreibung": (
            "Lohnkostenzuschuss für Arbeitgeber bei Neueinstellung von Fachkräften "
            "mit erschwerter Vermittlung. Bis zu 50% des Lohns für bis zu 12 Monate "
            "(bei Schwerbehinderten bis 24 Monate). Antrag VOR Arbeitsaufnahme stellen!"
        ),
        "foerderer": "Agentur für Arbeit",
        "kosten": "Für Arbeitgeber: Restlohn nach Förderung",
        "antrag_stelle": "Agentur für Arbeit – Antrag MUSS vor Arbeitsaufnahme gestellt werden",
        "niveau": ["alle"],
        "pflicht_dokumente": [
            "Antrag des Arbeitgebers bei der AA VOR Arbeitsaufnahme",
            "Stellenbeschreibung",
            "Künftiger Arbeitsvertrag",
            "Nachweis der Eingliederungsschwierigkeiten (z.B. lange Jobsuche, Sprachbarriere)",
        ],
    },
    "Bildungsprämie": {
        "beschreibung": (
            "Staatlicher Prämiengutschein von bis zu 500 € für berufliche Weiterbildung. "
            "Bedingung: Bruttojahreseinkommen ≤ 20.000 € (allein) oder ≤ 40.000 € (gemeinsam). "
            "Eigenanteil mind. 50 % der Kurskosten."
        ),
        "foerderer": "Bundesministerium für Bildung und Forschung (BMBF)",
        "kosten": "Eigenanteil mind. 50% der Kurskosten (max. 500 € Zuschuss)",
        "antrag_stelle": "Bildungsprämie-Beratungsstelle (bildungspraemie.info) vor Kursbeginn",
        "niveau": ["alle"],
        "pflicht_dokumente": [
            "Beratungsgespräch bei Bildungsprämie-Beratungsstelle",
            "Einkommensnachweis (Lohnabrechnung oder Steuerbescheid)",
            "Kursangebot mit Preisangabe",
            "Prämiengutschein (wird in der Beratung ausgestellt)",
        ],
    },
}

SPRACHNIVEAU_RANG = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

# ===========================================================================
# HILFSFUNKTIONEN
# ===========================================================================

def _waehle_integrationskurs_typ(niveau_rang: int, zeile: pd.Series) -> dict:
    alphabetisierung = str(zeile.get("alphabetisierungsbedarf", "nein")).strip().lower() in (
        "ja", "yes", "true", "1"
    )
    if alphabetisierung:
        return INTEGRATIONSKURS_TYPEN["alphabetisierung"]

    geschlecht = str(zeile.get("geschlecht", "")).strip().lower()
    geburtsdatum_raw = str(zeile.get("geburtsdatum", "")).strip()
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
    if niveau_rang == 2:
        return INTEGRATIONSKURS_TYPEN["intensiv"]
    return INTEGRATIONSKURS_TYPEN["allgemein"]


def _waehle_bsk_modul(berufsfeld: str, niveau_rang: int) -> tuple:
    modul = BSK_MODULE.get(berufsfeld, BSK_DEFAULT)
    if niveau_rang >= 4 and modul == BSK_DEFAULT:
        return ("BSK-Fachkurs", "400 UE", "B2–C1", "BAMF-Formular 540")
    return modul


def _analyse_aufenthaltsweg(aufenthaltstitel: str) -> dict:
    t = aufenthaltstitel.lower()
    if "blaue karte" in t or "blue card" in t or "§ 18c" in t:
        return AUFENTHALTSWEG_MAP["blaue karte"]
    if "§ 16d" in t or "16d" in t or "anerkennungsaufenthalt" in t:
        return AUFENTHALTSWEG_MAP["§ 16d"]
    if "§ 18a" in t or "18a" in t:
        return AUFENTHALTSWEG_MAP["§ 18a"]
    if "§ 18b" in t or "18b" in t:
        return AUFENTHALTSWEG_MAP["§ 18b"]
    if "niederlassungserlaubnis" in t or "§ 9" in t or "§ 19" in t:
        return AUFENTHALTSWEG_MAP["§ 19"]
    return {
        "bezeichnung": aufenthaltstitel,
        "beschreibung": "Aufenthaltstitel nicht automatisch zugeordnet – bitte manuell prüfen.",
        "max_dauer": "–",
        "beschaeftigung": "–",
        "niederlassungserlaubnis_nach": "–",
        "sprachziel_niederlassung": "B1 (Standardvoraussetzung)",
        "besonderheiten": [],
        "naechster_schritt": "Aufenthaltsweg mit der Ausländerbehörde klären.",
    }


def _ermittle_anerkennungsstelle(berufsfeld: str) -> dict:
    return ANERKENNUNGSSTELLEN.get(berufsfeld, ANERKENNUNGSSTELLE_DEFAULT)


def _berechne_kosten(berechtigte_programme: list) -> dict:
    details = []
    eigenanteil_gesamt = 0.0
    foerderung_gesamt = 0.0

    for prog in berechtigte_programme:
        name = prog["name"]
        if "BSK" in name:
            modul_text = prog.get("empfohlenes_modul", "")
            ue = 510
            if "900" in modul_text:
                ue = 900
            elif "400" in modul_text:
                ue = 400
            eigenanteil = round(ue * BSK_EIGENANTEIL_PRO_UE, 2)
            gesamtkosten = round(ue * BSK_GESAMTKOSTEN_PRO_UE_EST, 2)
            foerderung = round(gesamtkosten - eigenanteil, 2)
            details.append({
                "programm": name,
                "ue": ue,
                "eigenanteil": eigenanteil,
                "foerderung": foerderung,
                "foerderer": "BAMF",
                "hinweis": "Eigenanteil entfällt bei ALG-II-Bezug",
            })
            eigenanteil_gesamt += eigenanteil
            foerderung_gesamt += foerderung
        elif "Integrationskurs" in name:
            for typ in INTEGRATIONSKURS_TYPEN.values():
                if typ["name"] in name:
                    ue = typ["ue_zahl"]
                    eigenanteil = round(ue * typ["kosten_pro_ue"], 2)
                    details.append({
                        "programm": name,
                        "ue": ue,
                        "eigenanteil": eigenanteil,
                        "foerderung": 0,
                        "foerderer": "BAMF",
                        "hinweis": "Kostenbefreiung bei Hilfebedürftigkeit möglich",
                    })
                    eigenanteil_gesamt += eigenanteil
                    break
        elif "FbD" in name:
            details.append({
                "programm": name,
                "ue": "variabel",
                "eigenanteil": 0,
                "foerderung": 0,
                "foerderer": "BAMF / ESF",
                "hinweis": "Vollständig kostenfrei für Teilnehmende",
            })
        elif "IQ Netzwerk" in name or "§ 421" in name or "Bildungsprämie" not in name:
            details.append({
                "programm": name,
                "ue": "–",
                "eigenanteil": 0,
                "foerderung": 0,
                "foerderer": "Verschiedene",
                "hinweis": "Kostenfrei oder über Gutschein",
            })

    return {
        "eigenanteil_gesamt": eigenanteil_gesamt,
        "foerderung_gesamt": foerderung_gesamt,
        "details": details,
        "hinweis": (
            "Eigenanteil BSK kann bei geringem Einkommen oder ALG-II-Bezug vollständig erlassen werden. "
            "Integrationskurs: Kostenbefreiung auf Antrag möglich."
        ),
    }


def _erstelle_naechste_schritte(
    beschaeftigt: bool,
    niveau_rang: int,
    anerkennung: str,
    berufsfeld: str,
    aufenthaltsweg: dict,
    berechtigte_programme: list,
    tage_bis_ablauf: int | None,
) -> list:
    schritte = []
    nr = 1

    # SOFORT
    if tage_bis_ablauf is not None and tage_bis_ablauf < 90:
        schritte.append({
            "nr": nr, "prioritaet": "sofort",
            "schritt": "Aufenthaltstitel verlängern",
            "details": f"Läuft in {tage_bis_ablauf} Tagen ab – Termin bei der Ausländerbehörde sofort vereinbaren!",
            "verantwortlich": "Kandidat + Conveni",
        }); nr += 1

    if berufsfeld in REGLEMENTIERTE_BERUFE and anerkennung == "nicht beantragt":
        schritte.append({
            "nr": nr, "prioritaet": "sofort",
            "schritt": f"Anerkennungsverfahren einleiten ({berufsfeld})",
            "details": (
                f"Reglementierter Beruf: Anerkennung ist Pflichtvoraussetzung für die Beschäftigung. "
                f"Zuständige Stelle: {ANERKENNUNGSSTELLEN.get(berufsfeld, ANERKENNUNGSSTELLE_DEFAULT)['stelle_typ']}. "
                "IQ-Netzwerk kostenlos kontaktieren: netzwerk-iq.de"
            ),
            "verantwortlich": "Kandidat + Conveni",
        }); nr += 1

    # DIESE WOCHE
    if any("BSK" in p["name"] for p in berechtigte_programme):
        schritte.append({
            "nr": nr, "prioritaet": "diese_woche",
            "schritt": "Einstufungstest beim BSK-Kursträger vereinbaren",
            "details": "BAMF-Servicenummer: 0800 8 67467 (kostenfrei) – Kursträger in der Nähe finden und Einstufungstest vereinbaren.",
            "verantwortlich": "Kandidat + Conveni",
        }); nr += 1

    if anerkennung in ("nicht beantragt", "laufend"):
        schritte.append({
            "nr": nr, "prioritaet": "diese_woche",
            "schritt": "IQ-Netzwerk Beratungstermin vereinbaren",
            "details": "Kostenlose Beratung zur Anerkennung und Qualifizierung. Online-Termin möglich: netzwerk-iq.de",
            "verantwortlich": "Conveni für Kandidaten buchen",
        }); nr += 1

    if not beschaeftigt:
        schritte.append({
            "nr": nr, "prioritaet": "diese_woche",
            "schritt": "Als arbeitssuchend bei der Agentur für Arbeit melden",
            "details": "Notwendig für Bildungsgutschein (§ 421 SGB III) und Jobcenter-Unterstützung. Online: arbeitsagentur.de",
            "verantwortlich": "Kandidat",
        }); nr += 1

    # DIESEN MONAT
    if any("BSK" in p["name"] for p in berechtigte_programme):
        schritte.append({
            "nr": nr, "prioritaet": "diesen_monat",
            "schritt": "BSK-Antrag einreichen",
            "details": "Formular beim Kursträger ausfüllen + Arbeitgeberbestätigung + Aufenthaltstitel + Reisepass einreichen.",
            "verantwortlich": "Kandidat + Arbeitgeber",
        }); nr += 1

    if any("Integrationskurs" in p["name"] for p in berechtigte_programme):
        schritte.append({
            "nr": nr, "prioritaet": "diesen_monat",
            "schritt": "Integrationskurs anmelden (BAMF-Formular 101)",
            "details": "Antrag direkt beim BAMF oder über Ausländerbehörde. Kursträger online finden: bamf.de",
            "verantwortlich": "Kandidat + Conveni",
        }); nr += 1

    if any("FbD" in p["name"] for p in berechtigte_programme):
        schritte.append({
            "nr": nr, "prioritaet": "diesen_monat",
            "schritt": "FbD-Kurs beantragen (kostenfrei, kombinierbar mit BSK)",
            "details": "FbD-Kursträger in der Nähe finden: bamf.de/fbd",
            "verantwortlich": "Kandidat",
        }); nr += 1

    if beschaeftigt and any("Qualifizierungschancengesetz" in p["name"] for p in berechtigte_programme):
        schritte.append({
            "nr": nr, "prioritaet": "diesen_monat",
            "schritt": "Qualifizierungschancengesetz-Antrag (Arbeitgeber) – VOR Kursstart!",
            "details": "Arbeitgeber muss Antrag VOR Kursstart bei der Agentur für Arbeit stellen. Bis zu 100% Lehrgangskosten + Lohnkostenzuschuss.",
            "verantwortlich": "Arbeitgeber (Conveni unterstützen)",
        }); nr += 1

    # LANGFRISTIG
    ne_ziel = aufenthaltsweg.get("sprachziel_niederlassung", "B1")
    schritte.append({
        "nr": nr, "prioritaet": "langfristig",
        "schritt": f"Sprachziel {ne_ziel} für Niederlassungserlaubnis erreichen",
        "details": aufenthaltsweg.get("niederlassungserlaubnis_nach", ""),
        "verantwortlich": "Kandidat",
    }); nr += 1

    if anerkennung == "laufend":
        schritte.append({
            "nr": nr, "prioritaet": "langfristig",
            "schritt": "Anerkennungsverfahren aktiv verfolgen und Defizitbescheid auswerten",
            "details": "Nach Defizitbescheid: Anpassungsqualifizierung über Bildungsgutschein/AVGS beantragen.",
            "verantwortlich": "Kandidat + Conveni",
        }); nr += 1

    return schritte


def _erstelle_wiedervorlage(
    aufenthaltstitel_gueltig_bis: str | None,
    anerkennung: str,
    berufsfeld: str,
    berechtigte_programme: list,
) -> list:
    termine = []
    heute = date.today()

    if aufenthaltstitel_gueltig_bis:
        try:
            ablauf = datetime.strptime(aufenthaltstitel_gueltig_bis, "%Y-%m-%d").date()
            erinnerung = ablauf - timedelta(days=90)
            prioritaet = "hoch" if (ablauf - heute).days < 90 else "mittel"
            termine.append({
                "datum": ablauf,
                "datum_str": ablauf.strftime("%d.%m.%Y"),
                "erinnerung_str": erinnerung.strftime("%d.%m.%Y"),
                "beschreibung": "Aufenthaltstitel läuft ab",
                "aktion": "Verlängerung bei der Ausländerbehörde beantragen (90 Tage vorher!)",
                "prioritaet": prioritaet,
            })
        except ValueError:
            pass

    if anerkennung == "nicht beantragt" and berufsfeld in REGLEMENTIERTE_BERUFE:
        ziel = heute + timedelta(days=30)
        termine.append({
            "datum": ziel,
            "datum_str": ziel.strftime("%d.%m.%Y"),
            "erinnerung_str": heute.strftime("%d.%m.%Y"),
            "beschreibung": "Anerkennungsverfahren einleiten",
            "aktion": f"Unterlagen vorbereiten + IQ-Netzwerk kontaktieren (netzwerk-iq.de)",
            "prioritaet": "hoch",
        })

    if any("BSK" in p["name"] for p in berechtigte_programme):
        kursstart = heute + timedelta(days=45)
        termine.append({
            "datum": kursstart,
            "datum_str": kursstart.strftime("%d.%m.%Y"),
            "erinnerung_str": (heute + timedelta(days=7)).strftime("%d.%m.%Y"),
            "beschreibung": "BSK-Kursstart anstreben",
            "aktion": "Einstufungstest + Antragsformular einreichen (BAMF-Servicenummer: 0800 8 67467)",
            "prioritaet": "mittel",
        })

    if any("Qualifizierungschancengesetz" in p["name"] for p in berechtigte_programme):
        antrag = heute + timedelta(days=14)
        termine.append({
            "datum": antrag,
            "datum_str": antrag.strftime("%d.%m.%Y"),
            "erinnerung_str": heute.strftime("%d.%m.%Y"),
            "beschreibung": "Qualifizierungschancengesetz – Arbeitgeber-Antrag",
            "aktion": "Arbeitgeber muss VOR Kursstart Antrag bei der Agentur für Arbeit stellen!",
            "prioritaet": "hoch",
        })

    termine.sort(key=lambda t: t["datum"])
    return termine


def _berechne_status_ampel(
    hinweise: list,
    wiedervorlage: list,
    berechtigte_programme: list,
) -> str:
    for h in hinweise:
        if "DRINGEND" in h:
            return "rot"
    for t in wiedervorlage:
        if t["prioritaet"] == "hoch":
            return "rot"
    if not berechtigte_programme:
        return "rot"
    if any(t["prioritaet"] == "mittel" for t in wiedervorlage):
        return "gelb"
    if hinweise:
        return "gelb"
    return "gruen"


def _ermittle_arbeitgeber_foerderung(
    beschaeftigt: bool,
    arbeitgeber_groesse: str,
    berufsfeld: str,
) -> list:
    if not beschaeftigt:
        return []
    groesse = arbeitgeber_groesse.strip().lower()
    staffel_key = "klein" if groesse in ("klein", "small", "<10") else (
        "gross" if groesse in ("groß", "gross", "large", "groß", "250+") else "mittel"
    )
    prog = dict(PROGRAMME["Qualifizierungschancengesetz (§ 82 SGB III)"])
    staffel = prog["foerder_staffel"][staffel_key]
    return [
        {
            "name": "Qualifizierungschancengesetz (§ 82 SGB III)",
            "details": prog,
            "empfohlenes_modul": (
                f"Betriebsgröße: {staffel['label']} → "
                f"Lehrgangskosten: {staffel['lehrgang']} übernommen | "
                f"Lohnkostenzuschuss: {staffel['lohn']}"
            ),
        },
        {
            "name": "Eingliederungszuschuss (§ 88 SGB III)",
            "details": PROGRAMME["Eingliederungszuschuss (§ 88 SGB III)"],
            "empfohlenes_modul": "Bis 50% Lohnkostenzuschuss für 12 Monate – Antrag VOR Arbeitsaufnahme!",
        },
    ]


# ===========================================================================
# HAUPTFUNKTION
# ===========================================================================

def pruefe_kandidat(zeile: pd.Series) -> dict:
    name = f"{zeile['vorname']} {zeile['nachname']}"
    niveau = str(zeile.get("sprachniveau_aktuell", "")).strip().upper()
    beschaeftigt = str(zeile.get("beschaeftigt", "")).strip().lower() in ("ja", "yes", "true", "1")
    berufsfeld = str(zeile.get("berufsfeld", "")).strip()
    anerkennung = str(zeile.get("anerkennungsverfahren", "")).strip().lower()
    nationalitaet = str(zeile.get("nationalitaet", "")).strip()
    aufenthaltstitel = str(zeile.get("aufenthaltstitel", "")).strip()
    arbeitgeber_groesse = str(zeile.get("arbeitgeber_groesse", "mittel")).strip()
    qualifikation_abschluss = str(zeile.get("qualifikation_abschluss", "")).strip()
    email = str(zeile.get("email", "")).strip()
    telefon = str(zeile.get("telefon", "")).strip()
    arbeitgeber = str(zeile.get("arbeitgeber", "")).strip()

    niveau_rang = SPRACHNIVEAU_RANG.get(niveau, 0)
    berechtigte_programme = []
    hinweise = []

    # Aufenthaltstitel-Ablaufdatum
    gueltig_bis_raw = str(zeile.get("aufenthaltstitel_gueltig_bis", "")).strip()
    gueltig_bis_date = None
    tage_bis_ablauf = None
    if gueltig_bis_raw:
        try:
            gueltig_bis_date = datetime.strptime(gueltig_bis_raw, "%Y-%m-%d").date()
            tage_bis_ablauf = (gueltig_bis_date - date.today()).days
            if tage_bis_ablauf < 90:
                hinweise.append(
                    f"DRINGEND: Aufenthaltstitel läuft in {tage_bis_ablauf} Tagen ab "
                    f"({gueltig_bis_date.strftime('%d.%m.%Y')}) – Verlängerung sofort beantragen!"
                )
        except ValueError:
            pass

    # --- BSK ---
    if niveau_rang >= 2 and beschaeftigt:
        modulname, ue, niv_ziel, formular = _waehle_bsk_modul(berufsfeld, niveau_rang)
        prog = dict(PROGRAMME["Berufssprachkurs (BSK)"])
        prog["pflicht_dokumente"] = [
            f"BAMF-Antragsformular ({formular})" if "Formular" in d else d
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
        extra_dok = []
        if anerkennung == "nicht beantragt":
            extra_dok.append("Einleitung des Anerkennungsverfahrens empfohlen (steigert FbD-Berechtigung)")
        prog = dict(PROGRAMME["FbD – Förderung berufsbez. Deutschkenntnisse"])
        if extra_dok:
            prog["pflicht_dokumente"] = prog["pflicht_dokumente"] + extra_dok
        berechtigte_programme.append({
            "name": "FbD – Förderung berufsbez. Deutschkenntnisse",
            "details": prog,
            "empfohlenes_modul": f"FbD-Kurs (kombinierbar mit BSK) – Niveau {niveau}→C1",
        })

    # --- § 421 SGB III ---
    if not beschaeftigt:
        berechtigte_programme.append({
            "name": "§ 421 SGB III – Sprachkurs über Agentur für Arbeit",
            "details": PROGRAMME["§ 421 SGB III – Sprachkurs über Agentur für Arbeit"],
            "empfohlenes_modul": "Bildungsgutschein beantragen (Beratungsgespräch bei AA vereinbaren)",
        })
        hinweise.append("§ 421 SGB III: Kandidat muss sich als arbeitssuchend bei der Agentur für Arbeit melden.")

    # --- IQ Netzwerk ---
    if anerkennung in ("nicht beantragt", "laufend"):
        berechtigte_programme.append({
            "name": "IQ Netzwerk – Anerkennungsberatung",
            "details": PROGRAMME["IQ Netzwerk – Anerkennungsberatung"],
            "empfohlenes_modul": (
                "Kostenlose Erstberatung → netzwerk-iq.de"
                + (" | DRINGEND: Anerkennungsverfahren einleiten!" if anerkennung == "nicht beantragt"
                   else " | Laufendes Verfahren begleiten lassen")
            ),
        })

    # --- Nachqualifizierung ---
    if anerkennung == "laufend":
        berechtigte_programme.append({
            "name": "Nachqualifizierung / Anpassungsqualifizierung",
            "details": PROGRAMME["Nachqualifizierung / Anpassungsqualifizierung"],
            "empfohlenes_modul": (
                f"Anpassungsqualifizierung {berufsfeld} "
                "(nach Defizitbescheid der Anerkennungsstelle)"
            ),
        })

    # --- Arbeitgeberförderung ---
    arbeitgeber_foerderung = _ermittle_arbeitgeber_foerderung(
        beschaeftigt, arbeitgeber_groesse, berufsfeld
    )
    for p in arbeitgeber_foerderung:
        berechtigte_programme.append(p)

    # --- Bildungsprämie (bei geringem Einkommen) ---
    if beschaeftigt:
        berechtigte_programme.append({
            "name": "Bildungsprämie",
            "details": PROGRAMME["Bildungsprämie"],
            "empfohlenes_modul": "Bis 500 € Prämiengutschein – Einkommensvoraussetzung prüfen (bildungspraemie.info)",
        })

    # --- Hinweise für reglementierte Berufe ---
    if berufsfeld in REGLEMENTIERTE_BERUFE:
        hinweise.append(
            f"Reglementierter Beruf ({berufsfeld}): Berufserlaubnis/Berufsanerkennung ist "
            "Pflichtvoraussetzung – bitte Anerkennungsstatus dringend prüfen."
        )

    # --- Blaue Karte EU ---
    if "blaue karte" in aufenthaltstitel.lower():
        hinweise.append(
            "Blaue Karte EU: Niederlassungserlaubnis bereits nach 21 Monaten mit B1-Nachweis "
            "(§ 18c Abs. 3 AufenthG). BSK-Abschluss strategisch nutzen!"
        )

    # --- FbD Anerkennung Hinweis ---
    if anerkennung == "nicht beantragt" and niveau_rang >= 2:
        hinweise.append(
            "FbD: Anerkennungsverfahren sollte zeitnah eingeleitet werden "
            "(steigert Fördermöglichkeiten erheblich)."
        )

    # --- Analyse ---
    aufenthaltsweg = _analyse_aufenthaltsweg(aufenthaltstitel)
    anerkennungsstelle = _ermittle_anerkennungsstelle(berufsfeld)
    kosten = _berechne_kosten(berechtigte_programme)
    naechste_schritte = _erstelle_naechste_schritte(
        beschaeftigt, niveau_rang, anerkennung, berufsfeld,
        aufenthaltsweg, berechtigte_programme, tage_bis_ablauf
    )
    wiedervorlage = _erstelle_wiedervorlage(
        gueltig_bis_raw if gueltig_bis_raw else None,
        anerkennung, berufsfeld, berechtigte_programme
    )
    status_ampel = _berechne_status_ampel(hinweise, wiedervorlage, berechtigte_programme)

    return {
        "name": name,
        "nationalitaet": nationalitaet,
        "sprachniveau": niveau,
        "beschaeftigt": beschaeftigt,
        "berufsfeld": berufsfeld,
        "arbeitgeber": arbeitgeber,
        "aufenthaltstitel": aufenthaltstitel,
        "qualifikation_abschluss": qualifikation_abschluss,
        "email": email,
        "telefon": telefon,
        "aufenthaltsweg": aufenthaltsweg,
        "anerkennungsstelle": anerkennungsstelle,
        "berechtigte_programme": berechtigte_programme,
        "kosten": kosten,
        "naechste_schritte": naechste_schritte,
        "wiedervorlage": wiedervorlage,
        "hinweise": hinweise,
        "status_ampel": status_ampel,
        "aufenthaltstitel_ablauf": gueltig_bis_date.strftime("%d.%m.%Y") if gueltig_bis_date else "–",
    }


# ===========================================================================
# KONSOLENAUSGABE
# ===========================================================================

def main():
    if len(sys.argv) < 2:
        eingabe = Path(__file__).parent / "kandidaten_vorlage.csv"
    else:
        eingabe = Path(sys.argv[1])

    if not eingabe.exists():
        print(f"Fehler: Datei nicht gefunden: {eingabe}")
        sys.exit(1)

    suffix = eingabe.suffix.lower()
    df = pd.read_csv(eingabe) if suffix == ".csv" else pd.read_excel(eingabe)

    print(f"\n{'='*70}")
    print(f"  FÖRDERBERECHTIGUNGS-PRÜFUNG – {datetime.now().strftime('%d.%m.%Y')}")
    print(f"  Kandidaten gesamt: {len(df)}")
    print(f"{'='*70}\n")

    for _, zeile in df.iterrows():
        r = pruefe_kandidat(zeile)
        ampel = {"gruen": "✓", "gelb": "⚡", "rot": "⚠"}.get(r["status_ampel"], "?")
        print(f"{ampel} {r['name']} ({r['nationalitaet']}) | {r['aufenthaltstitel']}")
        print(f"  Niveau: {r['sprachniveau']} | Berufsfeld: {r['berufsfeld']} | "
              f"Beschäftigt: {'Ja' if r['beschaeftigt'] else 'Nein'}")
        print(f"  Aufenthaltsweg: {r['aufenthaltsweg']['bezeichnung']}")
        print(f"  NE möglich nach: {r['aufenthaltsweg']['niederlassungserlaubnis_nach']}")
        print(f"  Förderprogramme ({len(r['berechtigte_programme'])}):")
        for p in r["berechtigte_programme"]:
            print(f"    ✓ {p['name']}")
            print(f"      → {p['empfohlenes_modul']}")
        print(f"  Kosten-Eigenanteil gesamt: ca. {r['kosten']['eigenanteil_gesamt']:.0f} €")
        print(f"  Nächste Schritte ({len(r['naechste_schritte'])}):")
        for s in r["naechste_schritte"][:3]:
            print(f"    [{s['prioritaet'].upper()}] {s['schritt']}")
        if r["hinweise"]:
            for h in r["hinweise"]:
                print(f"  ⚠ {h}")
        print()


if __name__ == "__main__":
    main()
