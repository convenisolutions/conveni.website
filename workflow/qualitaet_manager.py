"""
Qualitätsmanagement: Trackt Kursergebnisse, Kursträger-Bewertungen und KPIs.
Daten werden in workflow/qualitaet.json gespeichert.

Verwendung:
  python qualitaet_manager.py --kpis
  python qualitaet_manager.py --kurstraeger
  python qualitaet_manager.py --erfasse "Nguyen Thi Lan" --kurs S001 --modul BSK-900 \
      --ergebnis bestanden --niveau B2 --bewertung 5
  python qualitaet_manager.py --kandidat "Nguyen Thi Lan"
  python qualitaet_manager.py --init-beispieldaten
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import date

QUALITAET_DATEI = Path(__file__).parent / "qualitaet.json"
STATUS_DATEI = Path(__file__).parent / "status.json"


def _kandidat_key(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def _lade_qualitaet() -> dict:
    if QUALITAET_DATEI.exists():
        return json.loads(QUALITAET_DATEI.read_text(encoding="utf-8"))
    return {}


def _speichere_qualitaet(daten: dict):
    QUALITAET_DATEI.write_text(
        json.dumps(daten, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )


def _lade_status() -> dict:
    if STATUS_DATEI.exists():
        return json.loads(STATUS_DATEI.read_text(encoding="utf-8"))
    return {}


def erfasse_kursergebnis(
    name: str,
    kurstraeger_id: str,
    kurstraeger_name: str,
    modul: str,
    ergebnis: str,
    niveau: str,
    bewertung: int | None = None,
    notiz: str = "",
) -> dict:
    """Speichert ein Kursergebnis für einen Kandidaten in qualitaet.json."""
    if ergebnis not in ("bestanden", "nicht_bestanden", "abgebrochen"):
        print("Fehler: --ergebnis muss 'bestanden', 'nicht_bestanden' oder 'abgebrochen' sein.")
        sys.exit(1)

    daten = _lade_qualitaet()
    key = _kandidat_key(name)
    eintrag = daten.get(key, {"name": name, "kurseintraege": []})

    kurseintrag = {
        "kurstraeger_id": kurstraeger_id,
        "kurstraeger_name": kurstraeger_name,
        "modul": modul,
        "abschluss_datum": date.today().isoformat(),
        "pruefungsergebnis": ergebnis,
        "erreichtes_niveau": niveau,
        "bewertung_kurstraeger": bewertung,
        "notiz": notiz,
    }

    eintrag["kurseintraege"].append(kurseintrag)
    daten[key] = eintrag
    _speichere_qualitaet(daten)
    return eintrag


def berechne_kpis() -> dict:
    """Berechnet übergreifende Qualitäts-KPIs aus qualitaet.json und status.json."""
    qualitaet = _lade_qualitaet()
    status_daten = _lade_status()

    alle_eintraege = [
        e
        for kandidat in qualitaet.values()
        for e in kandidat.get("kurseintraege", [])
    ]

    gesamt = len(alle_eintraege)
    bestanden = sum(1 for e in alle_eintraege if e["pruefungsergebnis"] == "bestanden")
    nicht_bestanden = sum(1 for e in alle_eintraege if e["pruefungsergebnis"] == "nicht_bestanden")
    abgebrochen = sum(1 for e in alle_eintraege if e["pruefungsergebnis"] == "abgebrochen")

    bewertungen = [e["bewertung_kurstraeger"] for e in alle_eintraege if e.get("bewertung_kurstraeger")]
    durchschnitt_bewertung = round(sum(bewertungen) / len(bewertungen), 1) if bewertungen else None

    kandidaten_gesamt = len(status_daten)
    vermittelt = sum(1 for e in status_daten.values() if e.get("aktuell") == "vermittelt")
    aktiv_in_kurs = sum(
        1 for e in status_daten.values()
        if e.get("aktuell") in ("kurs_laeuft", "kurs_genehmigt", "einstufungstest")
    )
    abgebrochen_status = sum(1 for e in status_daten.values() if e.get("aktuell") == "abgebrochen")
    kurs_abgeschlossen = sum(1 for e in status_daten.values() if e.get("aktuell") == "kurs_abgeschlossen")

    return {
        "kurs_gesamt": gesamt,
        "bestanden": bestanden,
        "nicht_bestanden": nicht_bestanden,
        "abgebrochen_kurs": abgebrochen,
        "erfolgsquote_pct": round(bestanden / gesamt * 100, 1) if gesamt > 0 else None,
        "abbruchquote_pct": round(abgebrochen / gesamt * 100, 1) if gesamt > 0 else None,
        "durchschnitt_bewertung": durchschnitt_bewertung,
        "kandidaten_gesamt": kandidaten_gesamt,
        "vermittelt": vermittelt,
        "aktiv_in_kurs": aktiv_in_kurs,
        "kurs_abgeschlossen": kurs_abgeschlossen,
        "abgebrochen_status": abgebrochen_status,
        "vermittlungsquote_pct": round(vermittelt / kandidaten_gesamt * 100, 1) if kandidaten_gesamt > 0 else None,
    }


def bewerte_kursträger() -> list[dict]:
    """Aggregiert Bewertungen und Erfolgsquoten pro Kursträger, sortiert nach Bewertung."""
    qualitaet = _lade_qualitaet()
    alle_eintraege = [
        e
        for kandidat in qualitaet.values()
        for e in kandidat.get("kurseintraege", [])
    ]

    kt_stats: dict[str, dict] = {}
    for e in alle_eintraege:
        kid = e["kurstraeger_id"]
        if kid not in kt_stats:
            kt_stats[kid] = {"id": kid, "name": e["kurstraeger_name"], "eintraege": []}
        kt_stats[kid]["eintraege"].append(e)

    ergebnis = []
    for data in kt_stats.values():
        eintraege = data["eintraege"]
        gesamt = len(eintraege)
        bestanden = sum(1 for e in eintraege if e["pruefungsergebnis"] == "bestanden")
        bewertungen = [e["bewertung_kurstraeger"] for e in eintraege if e.get("bewertung_kurstraeger")]
        ergebnis.append({
            "id": data["id"],
            "name": data["name"],
            "kurs_gesamt": gesamt,
            "bestanden": bestanden,
            "erfolgsquote_pct": round(bestanden / gesamt * 100, 1) if gesamt > 0 else 0,
            "durchschnitt_bewertung": round(sum(bewertungen) / len(bewertungen), 1) if bewertungen else None,
            "module": sorted({e["modul"] for e in eintraege}),
            "letzte_bewertungen": [e.get("notiz", "") for e in eintraege if e.get("notiz")],
        })

    ergebnis.sort(key=lambda x: -(x.get("durchschnitt_bewertung") or 0))
    return ergebnis


def _zeige_kpis():
    kpis = berechne_kpis()
    print("\n  ── Qualitäts-KPIs ──────────────────────────────────────")
    print(f"  Kandidaten gesamt:       {kpis['kandidaten_gesamt']}")
    print(f"  Aktiv in Kurs:           {kpis['aktiv_in_kurs']}")
    print(f"  Kurs abgeschlossen:      {kpis['kurs_abgeschlossen']}")
    print(f"  Vermittelt:              {kpis['vermittelt']}")
    print(f"  Abgebrochen:             {kpis['abgebrochen_status']}")
    if kpis["vermittlungsquote_pct"] is not None:
        print(f"  Vermittlungsquote:       {kpis['vermittlungsquote_pct']} %")
    print()
    print(f"  Prüfungsabschlüsse:      {kpis['kurs_gesamt']}")
    if kpis["kurs_gesamt"] > 0:
        print(f"  Bestanden:               {kpis['bestanden']}")
        print(f"  Nicht bestanden:         {kpis['nicht_bestanden']}")
        print(f"  Abgebrochen:             {kpis['abgebrochen_kurs']}")
        print(f"  Erfolgsquote:            {kpis['erfolgsquote_pct']} %")
    if kpis["durchschnitt_bewertung"] is not None:
        print(f"  ⌀ Kursträger-Bewertung:  {kpis['durchschnitt_bewertung']} / 5")
    print()


def _zeige_kursträger():
    kts = bewerte_kursträger()
    if not kts:
        print("Noch keine Kursergebnisse erfasst. Bitte --init-beispieldaten ausführen.")
        return
    print(f"\n  {'Kursträger':<32} {'Kurse':<7} {'Erfolg':>8}   {'⌀ Bew.':<10} {'Module'}")
    print("  " + "-" * 84)
    for kt in kts:
        bew = f"{kt['durchschnitt_bewertung']:.1f} / 5" if kt.get("durchschnitt_bewertung") else "–"
        module = ", ".join(kt["module"])
        print(f"  {kt['name']:<32} {kt['kurs_gesamt']:<7} {kt['erfolgsquote_pct']:>6.1f} %   {bew:<10} {module}")
    print()


BEISPIEL_QUALITAETSDATEN = {
    "nguyen_thi_lan": {
        "name": "Nguyen Thi Lan",
        "kurseintraege": [
            {
                "kurstraeger_id": "S001",
                "kurstraeger_name": "VHS München",
                "modul": "BSK-900",
                "abschluss_datum": "2026-04-15",
                "pruefungsergebnis": "bestanden",
                "erreichtes_niveau": "B2",
                "bewertung_kurstraeger": 5,
                "notiz": "Sehr gute Betreuung, klare Kursstruktur",
            }
        ],
    },
    "maria_santos": {
        "name": "Maria Santos",
        "kurseintraege": [
            {
                "kurstraeger_id": "S001",
                "kurstraeger_name": "VHS München",
                "modul": "BSK-900",
                "abschluss_datum": "2026-03-20",
                "pruefungsergebnis": "bestanden",
                "erreichtes_niveau": "B2",
                "bewertung_kurstraeger": 4,
                "notiz": "Guter Kurs, Lehrmaterial könnte moderner sein",
            }
        ],
    },
    "jose_reyes": {
        "name": "Jose Reyes",
        "kurseintraege": [
            {
                "kurstraeger_id": "S002",
                "kurstraeger_name": "Sprachschule Alpha GmbH",
                "modul": "BSK-510",
                "abschluss_datum": "2026-02-28",
                "pruefungsergebnis": "bestanden",
                "erreichtes_niveau": "B1",
                "bewertung_kurstraeger": 4,
                "notiz": "Prüfung knapp bestanden, aber stabile Leistung im Kurs",
            }
        ],
    },
    "van_minh_tran": {
        "name": "Van Minh Tran",
        "kurseintraege": [
            {
                "kurstraeger_id": "S003",
                "kurstraeger_name": "BFZ Bildungszentrum Bayern",
                "modul": "BSK-510",
                "abschluss_datum": "2026-03-10",
                "pruefungsergebnis": "bestanden",
                "erreichtes_niveau": "B1",
                "bewertung_kurstraeger": 5,
                "notiz": "Top Kursträger, sehr strukturierter Unterricht",
            }
        ],
    },
}


def main():
    parser = argparse.ArgumentParser(description="Qualitätsmanagement – Kursergebnisse und KPIs")
    parser.add_argument("--kpis", action="store_true", help="Qualitäts-KPIs anzeigen")
    parser.add_argument("--kurstraeger", action="store_true", help="Kursträger-Rangliste anzeigen")
    parser.add_argument("--kandidat", metavar="NAME", help="Alle Kurseinträge eines Kandidaten anzeigen")
    parser.add_argument("--erfasse", metavar="NAME", help="Kursergebnis erfassen")
    parser.add_argument("--kurs", metavar="SCHUL_ID", help="Kursträger-ID (z.B. S001)")
    parser.add_argument("--kursname", metavar="NAME", default="", help="Kursträger-Name (wenn ID unbekannt)")
    parser.add_argument("--modul", metavar="MODUL", default="BSK-510",
                        help="Kursmodul (BSK-510, BSK-900, BSK-400, Integrationskurs, FbD)")
    parser.add_argument("--ergebnis", choices=["bestanden", "nicht_bestanden", "abgebrochen"],
                        help="Prüfungsergebnis")
    parser.add_argument("--niveau", metavar="NIVEAU", default="",
                        help="Erreichtes Sprachniveau (A2, B1, B2, C1)")
    parser.add_argument("--bewertung", type=int, choices=[1, 2, 3, 4, 5],
                        help="Kursträger-Bewertung (1–5 Sterne)")
    parser.add_argument("--notiz", default="", help="Freitext-Notiz zum Kursergebnis")
    parser.add_argument("--init-beispieldaten", action="store_true",
                        help="qualitaet.json mit Beispieldaten befüllen")
    args = parser.parse_args()

    if args.init_beispieldaten:
        _speichere_qualitaet(BEISPIEL_QUALITAETSDATEN)
        print(f"  {len(BEISPIEL_QUALITAETSDATEN)} Beispiel-Einträge in qualitaet.json geschrieben.")
        return

    if args.kpis:
        _zeige_kpis()
        return

    if args.kurstraeger:
        _zeige_kursträger()
        return

    if args.kandidat:
        daten = _lade_qualitaet()
        eintrag = daten.get(_kandidat_key(args.kandidat))
        if not eintrag:
            print(f"Keine Qualitätsdaten für: {args.kandidat}")
            return
        print(f"\nKurseinträge: {eintrag['name']}")
        print("-" * 60)
        for e in eintrag.get("kurseintraege", []):
            bew = f"★ {e['bewertung_kurstraeger']}/5" if e.get("bewertung_kurstraeger") else ""
            print(f"  {e['abschluss_datum']}  {e['kurstraeger_name']:<28} {e['modul']:<10} "
                  f"{e['pruefungsergebnis']:<16} {e.get('erreichtes_niveau',''):<5} {bew}")
            if e.get("notiz"):
                print(f"    Notiz: {e['notiz']}")
        print()
        return

    if args.erfasse:
        if not args.ergebnis:
            print("Fehler: --ergebnis ist erforderlich.")
            sys.exit(1)
        schul_id = args.kurs or "MANUELL"
        schul_name = args.kursname or schul_id
        if args.kurs and not args.kursname:
            try:
                from partnerschulen_manager import _schule_nach_id
                s = _schule_nach_id(args.kurs)
                if s:
                    schul_name = s["name"]
            except ImportError:
                pass
        erfasse_kursergebnis(
            name=args.erfasse,
            kurstraeger_id=schul_id,
            kurstraeger_name=schul_name,
            modul=args.modul,
            ergebnis=args.ergebnis,
            niveau=args.niveau,
            bewertung=args.bewertung,
            notiz=args.notiz,
        )
        print(f"  ✓ Kursergebnis gespeichert: {args.erfasse} → {args.ergebnis} ({args.niveau})")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
