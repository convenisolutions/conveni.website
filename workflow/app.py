"""
Conveni Web-Interface – lokale Web-App für den Sprachförderungs-Workflow.

Starten:  python app.py
Browser:  http://localhost:5001
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file, abort

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from check_foerderung import pruefe_kandidat
from status_manager import (
    _lade_status, status_setzen, status_initialisieren,
    get_fortschritt, STATUSWERTE,
)
from dokumente_manager import (
    _lade_dokumente, setze_dokument_status, initialisiere_alle,
    berechne_vollstaendigkeit, DOKUMENT_TYPEN,
)
from fristenwächter import pruefe_fristen
from kommunikation_vorlagen import generiere_vorlage, VORLAGEN

app = Flask(__name__, template_folder="templates/web")

CSV_PFAD   = HERE / "kandidaten_vorlage.csv"
OUTPUT_DIR = HERE / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

BERICHTE = {
    "uebersicht":      {"label": "Kandidaten-Dashboard",    "script": "generate_uebersicht.py",         "datei": "uebersicht.html"},
    "monatsbericht":   {"label": "Monatsbericht",           "script": "generate_monatsbericht.py",      "datei": None},
    "fristenwaechter": {"label": "Fristenwächter",          "script": "fristenwächter.py --html",       "datei": None},
    "checklisten":     {"label": "Kandidaten-Checklisten",  "script": "generate_checklisten.py",        "datei": None},
    "formulare":       {"label": "Formular-Guides",         "script": "generate_formulare.py",          "datei": None},
    "arbeitgeber":     {"label": "Arbeitgeber-Mappen",      "script": "generate_arbeitgeber_mappe.py",  "datei": None},
    "partnerschulen":  {"label": "Partnerschulen-Bericht",  "script": "generate_partnerschulen_bericht.py", "datei": "partnerschulen_bericht.html"},
    "qualitaet":       {"label": "Qualitätsbericht",        "script": "generate_qualitaet_bericht.py",  "datei": "qualitaet_bericht.html"},
    "dokumente":       {"label": "Dokumenten-Bericht",      "script": "generate_dokumente_bericht.py",  "datei": "dokumente_bericht.html"},
    "kalender":        {"label": "Kalender-Export (.ics)",  "script": "generate_kalender.py",           "datei": "wiedervorlage_kalender.ics"},
}


def _kandidaten_mit_status() -> list[dict]:
    if not CSV_PFAD.exists():
        return []
    df = pd.read_csv(CSV_PFAD) if CSV_PFAD.suffix == ".csv" else pd.read_excel(CSV_PFAD)
    status_daten = _lade_status()
    result = []
    for _, zeile in df.iterrows():
        k = pruefe_kandidat(zeile)
        key = k["name"].strip().lower().replace(" ", "_")
        s = status_daten.get(key, {})
        sk = s.get("aktuell", "neu")
        k["workflow_status"] = {
            "key":        sk,
            "label":      s.get("aktuell_label", "Neu aufgenommen"),
            "farbe":      STATUSWERTE.get(sk, {}).get("farbe", "grau"),
            "fortschritt": get_fortschritt(sk),
            "notiz":      s.get("notiz", ""),
        }
        result.append(k)
    return result


# ── Seiten ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    kandidaten = _kandidaten_mit_status()
    fristen    = pruefe_fristen()
    dok_daten  = _lade_dokumente()
    vollst_avg = round(
        sum(berechne_vollstaendigkeit(e) for e in dok_daten.values()) / len(dok_daten)
    ) if dok_daten else 0
    aktiv = sum(
        1 for k in kandidaten
        if k["workflow_status"]["key"] not in ("neu", "abgebrochen", "pausiert")
    )
    return render_template("index.html",
        kandidaten=kandidaten, fristen=fristen,
        vollst_avg=vollst_avg, aktiv_in_workflow=aktiv,
    )


@app.route("/kandidaten")
def kandidaten_view():
    status_initialisieren(str(CSV_PFAD))
    kandidaten = _kandidaten_mit_status()
    return render_template("kandidaten.html",
        kandidaten=kandidaten, statuswerte=STATUSWERTE,
    )


@app.route("/dokumente")
def dokumente_view():
    initialisiere_alle(str(CSV_PFAD))
    daten = _lade_dokumente()
    kandidaten = [
        {**e, "vollstaendigkeit": berechne_vollstaendigkeit(e)}
        for e in sorted(daten.values(), key=lambda x: x["name"])
    ]
    return render_template("dokumente.html",
        kandidaten=kandidaten, dokument_typen=DOKUMENT_TYPEN,
    )


@app.route("/vorlagen")
def vorlagen_view():
    kandidaten = _kandidaten_mit_status()
    return render_template("vorlagen.html",
        kandidaten=kandidaten, vorlagen=VORLAGEN,
    )


@app.route("/berichte")
def berichte_view():
    bericht_status = {}
    for key, meta in BERICHTE.items():
        datei = meta.get("datei")
        pfad  = OUTPUT_DIR / datei if datei else None
        bericht_status[key] = {
            **meta,
            "existiert": pfad.exists() if pfad else False,
            "datum": datetime.fromtimestamp(pfad.stat().st_mtime).strftime("%d.%m.%Y %H:%M")
                     if pfad and pfad.exists() else None,
        }
    return render_template("berichte.html", berichte=bericht_status)


# ── API ───────────────────────────────────────────────────────────────────────

@app.route("/api/status", methods=["POST"])
def api_status():
    data   = request.get_json()
    name   = (data.get("name") or "").strip()
    status = (data.get("status") or "").strip()
    notiz  = (data.get("notiz") or "").strip()
    if not name or status not in STATUSWERTE:
        return jsonify({"error": "Ungültige Parameter"}), 400
    eintrag = status_setzen(name, status, notiz)
    return jsonify({
        "ok": True,
        "label":       eintrag["aktuell_label"],
        "farbe":       STATUSWERTE[status]["farbe"],
        "fortschritt": get_fortschritt(status),
    })


@app.route("/api/dokument", methods=["POST"])
def api_dokument():
    data   = request.get_json()
    name   = (data.get("name") or "").strip()
    typ    = (data.get("typ") or "").strip()
    status = (data.get("status") or "vorhanden").strip()
    notiz  = (data.get("notiz") or "").strip()
    if not name or typ not in DOKUMENT_TYPEN:
        return jsonify({"error": "Ungültige Parameter"}), 400
    setze_dokument_status(name, typ, status, notiz)
    daten = _lade_dokumente()
    key   = name.strip().lower().replace(" ", "_")
    pct   = berechne_vollstaendigkeit(daten.get(key, {}))
    return jsonify({"ok": True, "vollstaendigkeit": pct})


@app.route("/api/vorlage", methods=["POST"])
def api_vorlage():
    data   = request.get_json()
    key    = data.get("vorlage", "")
    kname  = data.get("kandidat", "[Name]")
    berufsfeld = sprachniveau = ""
    for k in _kandidaten_mit_status():
        if kname.lower() in k["name"].lower():
            berufsfeld   = k.get("berufsfeld", "")
            sprachniveau = k.get("sprachniveau", "")
            break
    text = generiere_vorlage(
        vorlage_key=key,
        kandidat_name=kname,
        berufsfeld=berufsfeld,
        sprachniveau=sprachniveau,
        kursträger=data.get("kursträger", "[Kursträger]"),
        kurs_datum=data.get("datum", "[Datum]"),
        tage_at=int(data["tage"]) if data.get("tage") else None,
        fehlende_docs=data.get("docs") or None,
    )
    return jsonify({"text": text})


@app.route("/api/bericht/<name>", methods=["POST"])
def api_bericht(name):
    if name not in BERICHTE:
        return jsonify({"error": "Unbekannt"}), 404
    script_parts = BERICHTE[name]["script"].split()
    script_file  = HERE / script_parts[0]
    extra_args   = script_parts[1:]
    result = subprocess.run(
        [sys.executable, str(script_file), str(CSV_PFAD)] + extra_args,
        capture_output=True, text=True, cwd=str(HERE),
    )
    return jsonify({"ok": result.returncode == 0, "output": result.stdout + result.stderr})


@app.route("/output/<path:filename>")
def output_datei(filename):
    pfad = OUTPUT_DIR / filename
    if not pfad.exists():
        abort(404)
    return send_file(str(pfad))


if __name__ == "__main__":
    print("\n  Conveni Web-Interface")
    print("  ────────────────────────────────────")
    print("  → http://localhost:5001\n")
    app.run(debug=True, port=5001, host="0.0.0.0")
