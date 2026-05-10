"""
BAMF-Formular-Ausfüllhilfe: Generiert pro Kandidat eine vorausgefüllte
Ausfüllhilfe für die relevanten BAMF-Antragsformulare.

Unterstützte Formulare:
  - BAMF Formular 540    → BSK Standard (Handwerk, Gastronomie, IT, …)
  - BAMF Formular 600-P  → BSK Spezialkurs Pflege / Altenpflege
  - BAMF Formular 600-M  → BSK Spezialkurs Medizin
  - BAMF Formular 101    → Integrationskurs (alle Varianten)

Die Ausfüllhilfe zeigt Feld für Feld, was in das offizielle BAMF-Formular
eingetragen werden muss. Das offizielle Formular immer zusätzlich beim
BAMF-Kursträger oder unter bamf.de herunterladen und unterschreiben.
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from check_foerderung import pruefe_kandidat, BSK_MODULE, BSK_DEFAULT


FORMULAR_FELDER = {
    "540": {
        "titel": "BAMF Formular 540 – Antrag auf Zulassung zum Berufssprachkurs (BSK Standard)",
        "abschnitte": [
            {
                "titel": "Abschnitt A: Angaben zur antragstellenden Person",
                "felder": [
                    ("Familienname",           "{nachname}"),
                    ("Vorname(n)",             "{vorname}"),
                    ("Geburtsdatum",           "{geburtsdatum_formatiert}"),
                    ("Staatsangehörigkeit",    "{nationalitaet}"),
                    ("Telefon / Mobil",        "{telefon}"),
                    ("E-Mail-Adresse",         "{email}"),
                ],
            },
            {
                "titel": "Abschnitt B: Aufenthaltsstatus",
                "felder": [
                    ("Art des Aufenthaltstitels",      "{aufenthaltstitel}"),
                    ("Aufenthaltstitel gültig bis",    "{aufenthaltstitel_ablauf}"),
                    ("Ausstellende Behörde",           "→ Bitte bei der Ausländerbehörde nachfragen"),
                ],
            },
            {
                "titel": "Abschnitt C: Beschäftigung",
                "felder": [
                    ("Name des Arbeitgebers",          "{arbeitgeber}"),
                    ("Berufsbezeichnung / Tätigkeit",  "{berufsfeld}"),
                    ("Beschäftigt seit",               "→ Laut Arbeitsvertrag eintragen"),
                ],
            },
            {
                "titel": "Abschnitt D: Sprachkenntnisse",
                "felder": [
                    ("Aktuelles Deutschniveau",        "{sprachniveau}"),
                    ("Gewünschtes Zielniveau",         "{bsk_zielniveau}"),
                ],
            },
            {
                "titel": "Abschnitt E: Gewünschter Kurs",
                "felder": [
                    ("Kurstyp",                        "{bsk_modulname}"),
                    ("Unterrichtseinheiten (UE)",      "{bsk_ue}"),
                    ("Antragsformular Nummer",         "{bsk_formular}"),
                ],
            },
            {
                "titel": "Unterschriften",
                "felder": [
                    ("Datum",                          "→ Aktuelles Datum eintragen"),
                    ("Unterschrift Antragsteller/in",  "→ Kandidat unterschreibt"),
                    ("Unterschrift Arbeitgeber",       "→ Arbeitgeber unterschreibt + Firmenstempel"),
                ],
            },
        ],
    },
    "600-P": {
        "titel": "BAMF Formular 600-P – Antrag BSK Spezialkurs Pflege",
        "abschnitte": [
            {
                "titel": "Abschnitt A: Angaben zur antragstellenden Person",
                "felder": [
                    ("Familienname",                   "{nachname}"),
                    ("Vorname(n)",                     "{vorname}"),
                    ("Geburtsdatum",                   "{geburtsdatum_formatiert}"),
                    ("Staatsangehörigkeit",            "{nationalitaet}"),
                    ("Telefon / Mobil",                "{telefon}"),
                    ("E-Mail-Adresse",                 "{email}"),
                ],
            },
            {
                "titel": "Abschnitt B: Aufenthaltsstatus",
                "felder": [
                    ("Art des Aufenthaltstitels",      "{aufenthaltstitel}"),
                    ("Aufenthaltstitel gültig bis",    "{aufenthaltstitel_ablauf}"),
                ],
            },
            {
                "titel": "Abschnitt C: Pflegeeinrichtung (Arbeitgeber)",
                "felder": [
                    ("Name der Pflegeeinrichtung",     "{arbeitgeber}"),
                    ("Art der Einrichtung",            "→ z.B. Krankenhaus / Pflegeheim / ambulanter Pflegedienst"),
                    ("Berufsbezeichnung",              "{berufsfeld}"),
                    ("Anerkennungsstatus",             "{anerkennungsstatus}"),
                ],
            },
            {
                "titel": "Abschnitt D: Sprachkenntnisse",
                "felder": [
                    ("Aktuelles Deutschniveau",        "{sprachniveau}"),
                    ("Zielniveau BSK Pflege",          "B2+ (Pflege-Spezialkurs)"),
                    ("Unterrichtseinheiten",           "900 UE"),
                ],
            },
            {
                "titel": "Abschnitt E: Berufsanerkennung Pflege",
                "felder": [
                    ("Zuständige Anerkennungsstelle",  "{anerkennungsstelle_typ}"),
                    ("Status Anerkennungsverfahren",   "{anerkennungsstatus}"),
                    ("Vorläufige Berufserlaubnis",     "→ Ja / Nein (bitte angeben)"),
                ],
            },
            {
                "titel": "Unterschriften",
                "felder": [
                    ("Datum",                          "→ Aktuelles Datum"),
                    ("Unterschrift Kandidat/in",       "→ Kandidat unterschreibt"),
                    ("Unterschrift Pflegeeinrichtung", "→ Arbeitgeber + Stempel"),
                ],
            },
        ],
    },
    "600-M": {
        "titel": "BAMF Formular 600-M – Antrag BSK Spezialkurs Medizin",
        "abschnitte": [
            {
                "titel": "Abschnitt A: Angaben zur Person",
                "felder": [
                    ("Familienname",                   "{nachname}"),
                    ("Vorname(n)",                     "{vorname}"),
                    ("Geburtsdatum",                   "{geburtsdatum_formatiert}"),
                    ("Staatsangehörigkeit",            "{nationalitaet}"),
                    ("Telefon / Mobil",                "{telefon}"),
                    ("E-Mail-Adresse",                 "{email}"),
                ],
            },
            {
                "titel": "Abschnitt B: Aufenthaltsstatus",
                "felder": [
                    ("Art des Aufenthaltstitels",      "{aufenthaltstitel}"),
                    ("Aufenthaltstitel gültig bis",    "{aufenthaltstitel_ablauf}"),
                ],
            },
            {
                "titel": "Abschnitt C: Medizinische Einrichtung",
                "felder": [
                    ("Name der Einrichtung",           "{arbeitgeber}"),
                    ("Art der Einrichtung",            "→ z.B. Krankenhaus / Arztpraxis / MVZ"),
                    ("Fachrichtung / Berufsbezeichnung", "{berufsfeld}"),
                ],
            },
            {
                "titel": "Abschnitt D: Approbation / Berufserlaubnis",
                "felder": [
                    ("Anerkennungsstatus",             "{anerkennungsstatus}"),
                    ("Zuständige Ärztekammer",         "{anerkennungsstelle_typ}"),
                    ("Berufserlaubnis § 10 BÄO",       "→ Ja / Nein (bitte angeben)"),
                ],
            },
            {
                "titel": "Abschnitt E: Sprachkenntnisse",
                "felder": [
                    ("Aktuelles Niveau",               "{sprachniveau}"),
                    ("Zielniveau",                     "C1 (Voraussetzung für Approbation)"),
                    ("Unterrichtseinheiten",           "900 UE"),
                ],
            },
            {
                "titel": "Unterschriften",
                "felder": [
                    ("Datum",                          "→ Aktuelles Datum"),
                    ("Unterschrift Kandidat/in",       "→ Kandidat unterschreibt"),
                    ("Unterschrift mediz. Einrichtung","→ Arbeitgeber + Stempel"),
                ],
            },
        ],
    },
    "101": {
        "titel": "BAMF Formular 101 – Antrag auf Zulassung zum Integrationskurs",
        "abschnitte": [
            {
                "titel": "Abschnitt A: Angaben zur Person",
                "felder": [
                    ("Familienname",                   "{nachname}"),
                    ("Vorname(n)",                     "{vorname}"),
                    ("Geburtsdatum",                   "{geburtsdatum_formatiert}"),
                    ("Geburtsland",                    "{nationalitaet}"),
                    ("Staatsangehörigkeit",            "{nationalitaet}"),
                    ("Telefon / Mobil",                "{telefon}"),
                    ("E-Mail-Adresse",                 "{email}"),
                ],
            },
            {
                "titel": "Abschnitt B: Aufenthaltsstatus",
                "felder": [
                    ("Art des Aufenthaltstitels",      "{aufenthaltstitel}"),
                    ("Aufenthaltstitel gültig bis",    "{aufenthaltstitel_ablauf}"),
                    ("Ausstellende Ausländerbehörde",  "→ Bitte bei der ABH nachfragen"),
                    ("Verpflichtet durch Ausländerbehörde", "{integrationskurs_verpflichtet}"),
                ],
            },
            {
                "titel": "Abschnitt C: Deutschkenntnisse",
                "felder": [
                    ("Vorhandene Deutschkenntnisse",   "{sprachniveau}"),
                    ("Alphabetisierungsbedarf",        "{alphabetisierungsbedarf_text}"),
                    ("Gewünschter Kurstyp",            "{integrationskurs_typ}"),
                ],
            },
            {
                "titel": "Abschnitt D: Besondere Kursform",
                "felder": [
                    ("Frauenkurs / Elternkurs",        "{frauen_kurs}"),
                    ("Jugendkurs (unter 27 J.)",       "{jugend_kurs}"),
                    ("Alphabetisierungskurs",          "{alpha_kurs}"),
                ],
            },
            {
                "titel": "Unterschriften",
                "felder": [
                    ("Datum",                          "→ Aktuelles Datum"),
                    ("Unterschrift Antragsteller/in",  "→ Kandidat unterschreibt"),
                ],
            },
        ],
    },
}


def _ermittle_formulare(r: dict) -> list[str]:
    """Welche Formulare braucht dieser Kandidat?"""
    formulare = []
    for prog in r["berechtigte_programme"]:
        if "BSK" in prog["name"]:
            modul = prog.get("empfohlenes_modul", "")
            if "Pflege" in modul or "Altenpflege" in modul:
                if "600-P" not in formulare:
                    formulare.append("600-P")
            elif "Medizin" in modul:
                if "600-M" not in formulare:
                    formulare.append("600-M")
            else:
                if "540" not in formulare:
                    formulare.append("540")
        if "Integrationskurs" in prog["name"] and "101" not in formulare:
            formulare.append("101")
    return formulare


def _baue_kontext(r: dict, zeile: pd.Series) -> dict:
    """Erstellt den Template-Kontext mit allen vorausgefüllten Werten."""
    # Geburtsdatum formatieren
    geb_raw = str(zeile.get("geburtsdatum", "")).strip()
    try:
        geb = datetime.strptime(geb_raw, "%Y-%m-%d")
        geb_fmt = geb.strftime("%d.%m.%Y")
    except ValueError:
        geb_fmt = geb_raw

    # BSK-Modul ermitteln
    berufsfeld = str(zeile.get("berufsfeld", "")).strip()
    niveau = str(zeile.get("sprachniveau_aktuell", "")).strip().upper()
    from check_foerderung import SPRACHNIVEAU_RANG
    niveau_rang = SPRACHNIVEAU_RANG.get(niveau, 0)
    from check_foerderung import _waehle_bsk_modul
    bsk_modulname, bsk_ue, bsk_zielniveau, bsk_formular = _waehle_bsk_modul(berufsfeld, niveau_rang)

    # Integrationskurs-Typ
    intk_typ = ""
    for prog in r["berechtigte_programme"]:
        if "Integrationskurs" in prog["name"]:
            intk_typ = prog["name"].replace("Integrationskurs – ", "")
            break

    # Alphabetisierung
    alpha = str(zeile.get("alphabetisierungsbedarf", "nein")).strip().lower() in ("ja", "yes", "1", "true")
    geschlecht = str(zeile.get("geschlecht", "")).strip().lower()
    geb_datum = zeile.get("geburtsdatum", "")
    alter = None
    try:
        geb_d = datetime.strptime(str(geb_datum), "%Y-%m-%d").date()
        alter = (datetime.now().date() - geb_d).days // 365
    except Exception:
        pass

    return {
        "nachname": zeile.get("nachname", ""),
        "vorname": zeile.get("vorname", ""),
        "geburtsdatum_formatiert": geb_fmt,
        "nationalitaet": zeile.get("nationalitaet", ""),
        "telefon": zeile.get("telefon", ""),
        "email": zeile.get("email", ""),
        "aufenthaltstitel": r["aufenthaltstitel"],
        "aufenthaltstitel_ablauf": r["aufenthaltstitel_ablauf"],
        "arbeitgeber": zeile.get("arbeitgeber", ""),
        "berufsfeld": berufsfeld,
        "sprachniveau": niveau,
        "bsk_modulname": bsk_modulname,
        "bsk_ue": bsk_ue,
        "bsk_zielniveau": bsk_zielniveau,
        "bsk_formular": bsk_formular,
        "anerkennungsstatus": str(zeile.get("anerkennungsverfahren", "")).strip().capitalize(),
        "anerkennungsstelle_typ": r["anerkennungsstelle"].get("stelle_typ", "–"),
        "integrationskurs_verpflichtet": (
            "Ja" if str(zeile.get("integrationskurs_verpflichtet", "nein")).strip().lower()
            in ("ja", "yes", "1", "true") else "Nein"
        ),
        "integrationskurs_typ": intk_typ,
        "alphabetisierungsbedarf_text": "Ja" if alpha else "Nein",
        "frauen_kurs": "Ja" if geschlecht in ("w", "weiblich", "f", "female") else "Nein",
        "jugend_kurs": "Ja" if alter is not None and alter < 27 else "Nein",
        "alpha_kurs": "Ja" if alpha else "Nein",
    }


def _fuelle_feld(wert_template: str, kontext: dict) -> str:
    """Ersetzt {platzhalter} mit echten Werten."""
    try:
        return wert_template.format(**kontext)
    except KeyError:
        return wert_template


def generiere_formulare(eingabe_pfad=None, ausgabe_ordner="output"):
    eingabe = Path(eingabe_pfad) if eingabe_pfad else Path(__file__).parent / "kandidaten_vorlage.csv"
    if not eingabe.exists():
        print(f"Fehler: Datei nicht gefunden: {eingabe}"); return

    df = pd.read_csv(eingabe) if eingabe.suffix == ".csv" else pd.read_excel(eingabe)
    ausgabe = Path(__file__).parent / ausgabe_ordner
    ausgabe.mkdir(exist_ok=True)

    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))
    template = env.get_template("formular_hilfe.html")
    datum = datetime.now().strftime("%d.%m.%Y")

    gesamt = 0
    for _, zeile in df.iterrows():
        r = pruefe_kandidat(zeile)
        formulare = _ermittle_formulare(r)
        kontext = _baue_kontext(r, zeile)

        for formular_nr in formulare:
            form_def = FORMULAR_FELDER[formular_nr]
            # Felder vorausfüllen
            abschnitte_gefuellt = []
            for abschnitt in form_def["abschnitte"]:
                felder_gefuellt = [
                    (label, _fuelle_feld(wert, kontext))
                    for label, wert in abschnitt["felder"]
                ]
                abschnitte_gefuellt.append({
                    "titel": abschnitt["titel"],
                    "felder": felder_gefuellt,
                })

            html = template.render(
                kandidat=r,
                formular_nr=formular_nr,
                formular_titel=form_def["titel"],
                abschnitte=abschnitte_gefuellt,
                datum=datum,
            )
            dateiname = (
                f"{zeile['nachname'].lower()}_{zeile['vorname'].split()[0].lower()}"
                f"_formular_{formular_nr}.html"
            )
            (ausgabe / dateiname).write_text(html, encoding="utf-8")
            print(f"  ✓ {dateiname}")
            gesamt += 1

    print(f"\n  {gesamt} Formular-Ausfüllhilfen erstellt in: {ausgabe.resolve()}")
    print("  Im Browser öffnen → Daten ins offizielle BAMF-Formular übertragen → unterschreiben\n")


if __name__ == "__main__":
    eingabe = sys.argv[1] if len(sys.argv) > 1 else None
    generiere_formulare(eingabe)
