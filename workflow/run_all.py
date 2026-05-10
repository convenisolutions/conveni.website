"""
Führt alle Workflow-Scripts in der richtigen Reihenfolge aus.
Verwendung: python run_all.py [kandidaten_vorlage.csv]
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).parent
CSV  = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "kandidaten_vorlage.csv"

SCRIPTS = [
    ("Status initialisieren",      ["status_manager.py",              "--liste", str(CSV)]),
    ("Dokumenten-Tracking",        ["dokumente_manager.py",           "--init-alle", str(CSV)]),
    ("Kandidaten-Dashboard",       ["generate_uebersicht.py",         str(CSV)]),
    ("Checklisten",                ["generate_checklisten.py",        str(CSV)]),
    ("Formular-Guides",            ["generate_formulare.py",          str(CSV)]),
    ("Kalender-Export",            ["generate_kalender.py",           str(CSV)]),
    ("Arbeitgeber-Mappen",         ["generate_arbeitgeber_mappe.py",  str(CSV)]),
    ("Partnerschulen-Bericht",     ["generate_partnerschulen_bericht.py", str(CSV)]),
    ("Qualitätsbericht",           ["generate_qualitaet_bericht.py",  str(CSV)]),
    ("Dokumenten-Bericht",         ["generate_dokumente_bericht.py",  str(CSV)]),
    ("Monatsbericht",              ["generate_monatsbericht.py",      str(CSV)]),
    ("Fristenwächter",             ["fristenwächter.py",              str(CSV), "--html"]),
]

def main():
    start = datetime.now()
    print(f"\n  Conveni Workflow – Vollständiger Durchlauf")
    print(f"  Kandidaten-CSV: {CSV}")
    print(f"  {'─'*50}")

    ok = fehler = 0
    for label, args in SCRIPTS:
        result = subprocess.run(
            [sys.executable] + [str(HERE / args[0])] + args[1:],
            capture_output=True, text=True, cwd=str(HERE)
        )
        status = "✓" if result.returncode == 0 else "✗"
        if result.returncode == 0:
            ok += 1
        else:
            fehler += 1
            print(f"  {status} {label}")
            if result.stderr.strip():
                print(f"    {result.stderr.strip()[:120]}")
            continue
        # Erste Ausgabezeile als Kurzinfo
        erste_zeile = next((l.strip() for l in result.stdout.splitlines() if l.strip()), "")
        print(f"  {status} {label:<35} {erste_zeile[:60]}")

    dauer = (datetime.now() - start).seconds
    print(f"\n  {'─'*50}")
    print(f"  {ok} OK | {fehler} Fehler | {dauer}s")
    print(f"  Output: {HERE / 'output'}\n")

if __name__ == "__main__":
    main()
