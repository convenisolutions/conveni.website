"""
Partnerschulen-Verwaltung: Trackt BAMF-Kursträger, VHS und private Partner.
Speichert in workflow/schulen.json. Unterstützt Kandidaten-Matching und
Akquise-E-Mail-Vorlagen.

Verwendung:
  python partnerschulen_manager.py --liste
  python partnerschulen_manager.py --suche BSK-900
  python partnerschulen_manager.py --match kandidaten_vorlage.csv
  python partnerschulen_manager.py --akquise-email S001
  python partnerschulen_manager.py --status S001 aktiv
  python partnerschulen_manager.py --init-beispieldaten
"""

import json
import sys
import argparse
from pathlib import Path

SCHULEN_DATEI = Path(__file__).parent / "schulen.json"

KONTAKT_STATUSWERTE = {
    "noch_nicht":       {"label": "Noch nicht kontaktiert", "farbe": "grau"},
    "angefragt":        {"label": "Angefragt",              "farbe": "blau"},
    "angebot_erhalten": {"label": "Angebot erhalten",       "farbe": "orange"},
    "vertrag":          {"label": "Vertrag geschlossen",     "farbe": "gruen"},
    "aktiv":            {"label": "Aktiver Partner",         "farbe": "gruen"},
    "inaktiv":          {"label": "Nicht mehr aktiv",        "farbe": "rot"},
}

# Kurs-Modul → kompatible Schul-Angebots-Typen
MODUL_ZU_ANGEBOT = {
    "BSK-510":                    ["BSK-510"],
    "BSK-900":                    ["BSK-900"],
    "BSK-400":                    ["BSK-400"],
    "BSK Fachkurs":               ["BSK-400", "FbD"],
    "Alphabetisierungskurs":      ["Alphabetisierungskurs"],
    "Jugendintegrationskurs":     ["Integrationskurs"],
    "Frauen-/Elternkurs":         ["Integrationskurs"],
    "Intensivintegrationskurs":   ["Integrationskurs"],
    "Allgemeiner Integrationskurs": ["Integrationskurs"],
    "FbD":                        ["FbD"],
    "§ 421 Bildungsgutschein":    ["Deutschkurs allgemein", "FbD", "BSK-510"],
}

BEISPIELDATEN = [
    {
        "id": "S001",
        "name": "VHS München",
        "traeger_typ": "VHS",
        "stadt": "München",
        "plz": "80331",
        "bundesland": "Bayern",
        "kontakt_person": "Frau Huber",
        "email": "sprachkurse@vhs.muenchen.de",
        "telefon": "089 480006-0",
        "bamf_zugelassen": True,
        "bamf_traeger_nr": "097801",
        "angebote": ["BSK-510", "BSK-900", "Integrationskurs", "Alphabetisierungskurs"],
        "kapazitaet_pro_kurs": 16,
        "naechster_kursbeginn": "2026-06-01",
        "preis_ue": 4.80,
        "kooperationsrabatt_pct": 0,
        "kontakt_status": "aktiv",
        "bewertung": 4.5,
        "notiz": "Langjähriger Partner, schnelle Einstufungstests möglich",
    },
    {
        "id": "S002",
        "name": "Sprachschule Alpha GmbH",
        "traeger_typ": "privat",
        "stadt": "München",
        "plz": "80336",
        "bundesland": "Bayern",
        "kontakt_person": "Herr Maier",
        "email": "info@alpha-sprachen.de",
        "telefon": "089 22334455",
        "bamf_zugelassen": True,
        "bamf_traeger_nr": "097845",
        "angebote": ["BSK-510", "BSK-900", "FbD", "BSK-400"],
        "kapazitaet_pro_kurs": 12,
        "naechster_kursbeginn": "2026-07-01",
        "preis_ue": 5.20,
        "kooperationsrabatt_pct": 5,
        "kontakt_status": "vertrag",
        "bewertung": 4.2,
        "notiz": "5 % Rabatt ab 3 gleichzeitigen Anmeldungen",
    },
    {
        "id": "S003",
        "name": "BFZ Bildungszentrum Bayern",
        "traeger_typ": "Bildungsträger",
        "stadt": "Nürnberg",
        "plz": "90403",
        "bundesland": "Bayern",
        "kontakt_person": "Frau Schmidt",
        "email": "info@bfz-nuernberg.de",
        "telefon": "0911 2000-0",
        "bamf_zugelassen": True,
        "bamf_traeger_nr": "091201",
        "angebote": ["BSK-510", "BSK-900", "Integrationskurs", "FbD", "Alphabetisierungskurs"],
        "kapazitaet_pro_kurs": 20,
        "naechster_kursbeginn": "2026-06-15",
        "preis_ue": 4.60,
        "kooperationsrabatt_pct": 0,
        "kontakt_status": "aktiv",
        "bewertung": 4.7,
        "notiz": "Sehr gute Prüfungsergebnisse, eigenes Prüfungszentrum",
    },
    {
        "id": "S004",
        "name": "Caritasverband München",
        "traeger_typ": "Wohlfahrtsverband",
        "stadt": "München",
        "plz": "80797",
        "bundesland": "Bayern",
        "kontakt_person": "Frau Weber",
        "email": "integration@caritas-muenchen.de",
        "telefon": "089 55169-0",
        "bamf_zugelassen": True,
        "bamf_traeger_nr": "097866",
        "angebote": ["Integrationskurs", "Alphabetisierungskurs", "BSK-510"],
        "kapazitaet_pro_kurs": 18,
        "naechster_kursbeginn": "2026-05-20",
        "preis_ue": 4.50,
        "kooperationsrabatt_pct": 0,
        "kontakt_status": "aktiv",
        "bewertung": 4.3,
        "notiz": "Spezialisiert auf Frauen-/Elternkurse und Alphabetisierung",
    },
    {
        "id": "S005",
        "name": "Inlingua München",
        "traeger_typ": "privat",
        "stadt": "München",
        "plz": "80539",
        "bundesland": "Bayern",
        "kontakt_person": "Herr Fischer",
        "email": "muenchen@inlingua.de",
        "telefon": "089 235051-0",
        "bamf_zugelassen": True,
        "bamf_traeger_nr": "097812",
        "angebote": ["BSK-900", "BSK-400", "FbD", "Deutschkurs allgemein"],
        "kapazitaet_pro_kurs": 10,
        "naechster_kursbeginn": "2026-06-01",
        "preis_ue": 6.00,
        "kooperationsrabatt_pct": 10,
        "kontakt_status": "angebot_erhalten",
        "bewertung": 4.0,
        "notiz": "Premium-Anbieter; 10 % Kooperationsrabatt angeboten, Vertrag noch offen",
    },
    {
        "id": "S006",
        "name": "DAA Deutsche Angestellten-Akademie Hamburg",
        "traeger_typ": "Bildungsträger",
        "stadt": "Hamburg",
        "plz": "20354",
        "bundesland": "Hamburg",
        "kontakt_person": "Frau Richter",
        "email": "hamburg@daa.de",
        "telefon": "040 350094-0",
        "bamf_zugelassen": True,
        "bamf_traeger_nr": "020301",
        "angebote": ["BSK-510", "BSK-900", "Integrationskurs", "FbD", "BSK-400"],
        "kapazitaet_pro_kurs": 20,
        "naechster_kursbeginn": "2026-07-15",
        "preis_ue": 5.00,
        "kooperationsrabatt_pct": 0,
        "kontakt_status": "noch_nicht",
        "bewertung": None,
        "notiz": "",
    },
    {
        "id": "S007",
        "name": "AWO Bildungswerk Bayern",
        "traeger_typ": "Wohlfahrtsverband",
        "stadt": "München",
        "plz": "80335",
        "bundesland": "Bayern",
        "kontakt_person": "Herr Zimmermann",
        "email": "bildung@awo-muenchen.de",
        "telefon": "089 458095-0",
        "bamf_zugelassen": True,
        "bamf_traeger_nr": "097870",
        "angebote": ["Integrationskurs", "BSK-510", "Alphabetisierungskurs"],
        "kapazitaet_pro_kurs": 18,
        "naechster_kursbeginn": "2026-06-10",
        "preis_ue": 4.70,
        "kooperationsrabatt_pct": 0,
        "kontakt_status": "noch_nicht",
        "bewertung": None,
        "notiz": "",
    },
]


def _lade_schulen() -> list:
    if SCHULEN_DATEI.exists():
        return json.loads(SCHULEN_DATEI.read_text(encoding="utf-8"))
    return []


def _speichere_schulen(schulen: list):
    SCHULEN_DATEI.write_text(
        json.dumps(schulen, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )


def _schule_nach_id(schul_id: str) -> dict | None:
    return next((s for s in _lade_schulen() if s["id"] == schul_id), None)


def initialisiere_beispieldaten():
    _speichere_schulen(BEISPIELDATEN)
    print(f"  {len(BEISPIELDATEN)} Beispiel-Schulen initialisiert in: {SCHULEN_DATEI}")


def status_setzen(schul_id: str, status: str):
    if status not in KONTAKT_STATUSWERTE:
        print(f"Fehler: Unbekannter Status '{status}'")
        print(f"Gültige Werte: {', '.join(KONTAKT_STATUSWERTE.keys())}")
        sys.exit(1)
    schulen = _lade_schulen()
    for s in schulen:
        if s["id"] == schul_id:
            s["kontakt_status"] = status
            _speichere_schulen(schulen)
            print(f"  ✓ {s['name']} → {KONTAKT_STATUSWERTE[status]['label']}")
            return
    print(f"Fehler: Schule '{schul_id}' nicht gefunden.")
    sys.exit(1)


def suche_schulen(angebot: str) -> list:
    angebot_u = angebot.upper()
    return [
        s for s in _lade_schulen()
        if any(angebot_u in a.upper() for a in s["angebote"])
    ]


def finde_schulen_fuer_kandidat(kandidat: dict) -> list[dict]:
    """Gibt bis zu 5 passende Partnerschulen zurück, sortiert nach Bewertung."""
    schulen = _lade_schulen()
    passend_ids: set[str] = set()
    passend: list[dict] = []

    for prog in kandidat.get("berechtigte_programme", []):
        pname = prog["name"]
        benoetigt: list[str] = []
        for schluessel, angebote in MODUL_ZU_ANGEBOT.items():
            if schluessel in pname:
                benoetigt = angebote
                break
        if not benoetigt:
            if "BSK" in pname:
                benoetigt = ["BSK-510"]
            elif "Integrations" in pname or "Alphabetisierung" in pname:
                benoetigt = ["Integrationskurs"]
            else:
                continue

        for schule in schulen:
            if schule["kontakt_status"] in ("inaktiv",):
                continue
            if schule["id"] in passend_ids:
                continue
            if any(a in schule["angebote"] for a in benoetigt):
                passend_ids.add(schule["id"])
                passend.append(schule)

    passend.sort(key=lambda s: (
        {"aktiv": 0, "vertrag": 1, "angebot_erhalten": 2, "angefragt": 3, "noch_nicht": 4}.get(
            s["kontakt_status"], 9
        ),
        -(s.get("bewertung") or 0),
    ))
    return passend[:5]


def generiere_akquise_email(schul_id: str) -> str:
    schule = _schule_nach_id(schul_id)
    if not schule:
        return f"Fehler: Schule '{schul_id}' nicht gefunden."

    angebote_str = ", ".join(schule.get("angebote", []))
    ansprechpartner = schule.get("kontakt_person", "Damen und Herren")
    rabatt_hinweis = (
        f"\nDa Sie einen Kooperationsrabatt von {schule['kooperationsrabatt_pct']} % angeboten haben, "
        "möchten wir diesen gerne zeitnah vertraglich festhalten."
        if schule.get("kooperationsrabatt_pct", 0) > 0 else ""
    )

    return f"""Betreff: Kooperationsanfrage – Sprachkurse für internationale Fachkräfte

Sehr geehrte/r {ansprechpartner},

mein Name ist [Ihr Name], ich leite die Personalvermittlung Conveni mit Sitz in [Ihr Standort].
Wir vermitteln qualifizierte Fachkräfte aus dem Ausland (Philippinen, Vietnam) an deutsche
Arbeitgeber und begleiten diese vollständig durch den Sprachförderungsprozess – von der
Förderprüfung über den BAMF-Antrag bis zum Kursabschluss.

Da {schule['name']} als BAMF-zugelassener Kursträger (Träger-Nr. {schule.get('bamf_traeger_nr', 'N/A')})
Angebote in folgenden Bereichen vorhält:
  {angebote_str}
– würde ich gerne eine dauerhafte Kooperationsvereinbarung besprechen.{rabatt_hinweis}

Was wir in die Partnerschaft einbringen:
  • Vollständig vorbereitete Kandidaten (Aufenthaltstitel geprüft, Förderantrag vorbereitet)
  • Koordinierte Freistellungen mit den Arbeitgebern
  • Gruppen von 3–8 Teilnehmenden pro Kursrunde möglich
  • Schnelle Rückmeldung bei kurzfristigen Änderungen (Ausfall, Kündigung)

Was wir uns von der Partnerschaft erhoffen:
  • Bevorzugte Platzierung unserer Kandidaten bei Kursstart
  • Direkte Ansprechperson für Einstufungstests und administrative Fragen
  • Ggf. Gruppenkonditionen bei mehreren gleichzeitigen Anmeldungen

Wäre ein kurzes Telefonat diese oder nächste Woche möglich?
Ich freue mich auf Ihre Rückmeldung.

Mit freundlichen Grüßen
[Ihr Name]
Conveni Personalvermittlung
[Telefonnummer] | info@conveni.de | conveni.de
"""


def _liste_anzeigen(filter_status: str | None = None):
    schulen = _lade_schulen()
    if filter_status:
        schulen = [s for s in schulen if s["kontakt_status"] == filter_status]
    if not schulen:
        print("Keine Schulen gefunden." + (f" (Filter: {filter_status})" if filter_status else ""))
        return

    print(f"\n{'ID':<6} {'Name':<32} {'Stadt':<12} {'Angebote':<38} {'Status':<22} {'★'}")
    print("-" * 116)
    for s in schulen:
        angebote = ", ".join(s["angebote"][:3]) + ("…" if len(s["angebote"]) > 3 else "")
        status_label = KONTAKT_STATUSWERTE.get(s["kontakt_status"], {}).get("label", s["kontakt_status"])
        bew = f"{s['bewertung']:.1f}" if s.get("bewertung") else "–"
        print(f"{s['id']:<6} {s['name']:<32} {s['stadt']:<12} {angebote:<38} {status_label:<22} {bew}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Partnerschulen-Verwaltung")
    parser.add_argument("--liste", nargs="?", const=True, metavar="STATUS",
                        help="Alle Schulen anzeigen (optional: Filter z.B. 'aktiv')")
    parser.add_argument("--suche", metavar="ANGEBOT",
                        help="Schulen nach Angebot suchen (z.B. BSK-900)")
    parser.add_argument("--match", metavar="CSV",
                        help="Kandidaten-CSV: Passende Schulen pro Kandidat ausgeben")
    parser.add_argument("--akquise-email", metavar="SCHUL_ID",
                        help="Akquise-E-Mail-Vorlage für eine Schule generieren")
    parser.add_argument("--status", nargs=2, metavar=("SCHUL_ID", "STATUS"),
                        help="Kontaktstatus setzen: --status S001 aktiv")
    parser.add_argument("--init-beispieldaten", action="store_true",
                        help="schulen.json mit Beispieldaten befüllen")
    args = parser.parse_args()

    if args.init_beispieldaten:
        initialisiere_beispieldaten()
        return

    if args.liste is not None:
        filter_s = args.liste if isinstance(args.liste, str) else None
        _liste_anzeigen(filter_s)
        return

    if args.suche:
        gefunden = suche_schulen(args.suche)
        if not gefunden:
            print(f"Keine Schulen mit Angebot '{args.suche}' gefunden.")
        else:
            print(f"\nSchulen mit Angebot '{args.suche}':")
            for s in gefunden:
                sl = KONTAKT_STATUSWERTE.get(s["kontakt_status"], {}).get("label", s["kontakt_status"])
                print(f"  {s['id']}  {s['name']} ({s['stadt']}) – {sl}")
        return

    if args.match:
        import pandas as pd
        from check_foerderung import pruefe_kandidat
        pfad = args.match
        df = pd.read_csv(pfad) if pfad.endswith(".csv") else pd.read_excel(pfad)
        for _, zeile in df.iterrows():
            k = pruefe_kandidat(zeile)
            schulen = finde_schulen_fuer_kandidat(k)
            namen = [f"{s['name']} ({s['stadt']})" for s in schulen]
            print(f"  {k['name']}: {', '.join(namen) if namen else 'Keine passenden Schulen'}")
        return

    if args.akquise_email:
        print(generiere_akquise_email(args.akquise_email))
        return

    if args.status:
        status_setzen(args.status[0], args.status[1])
        return

    parser.print_help()


if __name__ == "__main__":
    main()
