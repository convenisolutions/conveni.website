"""
Wiedervorlage-Kalender: Exportiert alle Termine als .ics-Datei.
Import in Outlook: Datei → Öffnen → Importieren → iCalendar
Import in Google Kalender: Einstellungen → Kalender importieren
Import in Apple Kalender: Ablage → Importieren
"""

import sys
import uuid
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

from check_foerderung import pruefe_kandidat


def _ics_escape(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")


def _ics_fold(line: str) -> str:
    """ICS-Zeilenumbruch bei 75 Zeichen (RFC 5545)."""
    if len(line.encode("utf-8")) <= 75:
        return line
    result, current = [], ""
    for char in line:
        if len((current + char).encode("utf-8")) > 75:
            result.append(current)
            current = " " + char
        else:
            current += char
    result.append(current)
    return "\r\n".join(result)


def _erstelle_vevent(termin: dict, kandidat_name: str, kategorie: str) -> str:
    uid = f"{uuid.uuid4()}@conveni-workflow"
    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dtstart = termin["datum"].strftime("%Y%m%d")
    dtend = (termin["datum"] + timedelta(days=1)).strftime("%Y%m%d")
    alarm_tage = 14 if termin["prioritaet"] == "hoch" else 7

    summary = f"[{termin['prioritaet'].upper()}] {termin['beschreibung']} – {kandidat_name}"
    description = (
        f"Kandidat: {kandidat_name}\\n"
        f"Aktion: {termin['aktion']}\\n"
        f"Priorität: {termin['prioritaet'].upper()}\\n"
        f"Erinnerung ab: {termin['erinnerung_str']}\\n"
        f"Kategorie: {kategorie}"
    )

    prioritaet_nr = {"hoch": "1", "mittel": "5", "niedrig": "9"}.get(termin["prioritaet"], "5")

    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART;VALUE=DATE:{dtstart}",
        f"DTEND;VALUE=DATE:{dtend}",
        f"SUMMARY:{_ics_escape(summary)}",
        f"DESCRIPTION:{_ics_escape(description)}",
        f"PRIORITY:{prioritaet_nr}",
        f"CATEGORIES:{_ics_escape(kategorie)}",
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        f"DESCRIPTION:{_ics_escape('Erinnerung: ' + summary)}",
        f"TRIGGER:-P{alarm_tage}D",
        "END:VALARM",
        "END:VEVENT",
    ]
    return "\r\n".join(_ics_fold(l) for l in lines)


def generiere_kalender(eingabe_pfad=None, ausgabe_ordner="output"):
    eingabe = Path(eingabe_pfad) if eingabe_pfad else Path(__file__).parent / "kandidaten_vorlage.csv"
    if not eingabe.exists():
        print(f"Fehler: Datei nicht gefunden: {eingabe}"); return

    df = pd.read_csv(eingabe) if eingabe.suffix == ".csv" else pd.read_excel(eingabe)
    ausgabe = Path(__file__).parent / ausgabe_ordner
    ausgabe.mkdir(exist_ok=True)

    alle_events: list[tuple[str, dict, str]] = []
    for _, zeile in df.iterrows():
        r = pruefe_kandidat(zeile)
        for t in r["wiedervorlage"]:
            alle_events.append((r["name"], t, r["berufsfeld"]))

    alle_events.sort(key=lambda x: x[1]["datum"])

    header = "\r\n".join([
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Conveni Personalvermittlung//Foerder-Workflow//DE",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Conveni – Wiedervorlage Sprachförderung",
        "X-WR-CALDESC:Automatisch generierte Wiedervorlagetermine",
        "X-WR-TIMEZONE:Europe/Berlin",
    ])

    events_ics = "\r\n".join(
        _erstelle_vevent(t, name, beruf) for name, t, beruf in alle_events
    )

    ics = f"{header}\r\n{events_ics}\r\nEND:VCALENDAR"

    ausgabe_datei = ausgabe / "wiedervorlage_kalender.ics"
    ausgabe_datei.write_bytes(ics.encode("utf-8"))

    hoch = sum(1 for _, t, _ in alle_events if t["prioritaet"] == "hoch")
    mittel = sum(1 for _, t, _ in alle_events if t["prioritaet"] == "mittel")
    print(f"  ✓ Kalender erstellt: {ausgabe_datei.name}")
    print(f"    {len(alle_events)} Termine | Hoch: {hoch} | Mittel: {mittel}")
    print("    → Outlook:         Datei → Öffnen & Exportieren → Importieren → iCalendar")
    print("    → Google Kalender: Einstellungen (⚙) → Kalender importieren → .ics wählen")
    print("    → Apple Kalender:  Ablage → Importieren\n")
    return str(ausgabe_datei)


if __name__ == "__main__":
    eingabe = sys.argv[1] if len(sys.argv) > 1 else None
    generiere_kalender(eingabe)
