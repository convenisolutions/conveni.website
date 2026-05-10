"""
Tägliche E-Mail-Zusammenfassung via Gmail.
Einrichtung: python email_notifier.py --setup
Täglich:     python email_notifier.py kandidaten.csv
"""
import smtplib
import json
import sys
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
from pathlib import Path

KONFIG_DATEI = Path(__file__).parent / "email_config.json"


def konfig_laden():
    if not KONFIG_DATEI.exists():
        print("❌ Keine Konfiguration gefunden. Bitte zuerst: python email_notifier.py --setup")
        sys.exit(1)
    with open(KONFIG_DATEI) as f:
        return json.load(f)


def konfig_einrichten():
    print("=== Gmail-Konfiguration einrichten ===\n")
    print("Du brauchst ein Gmail App-Passwort (nicht dein normales Passwort).")
    print("So erstellt du eines:")
    print("  1. Gehe zu: myaccount.google.com/security")
    print("  2. Klick auf '2-Schritt-Verifizierung' → aktivieren falls nötig")
    print("  3. Gehe zu: myaccount.google.com/apppasswords")
    print("  4. App: 'Mail', Gerät: 'Anderes (Conveni Workflow)'")
    print("  5. 16-stelliges Passwort kopieren\n")

    gmail = input("Deine Gmail-Adresse: ").strip()
    app_pw = input("App-Passwort (16 Zeichen, ohne Leerzeichen): ").strip().replace(" ", "")
    empfaenger = input(f"Empfänger-E-Mail [{gmail}]: ").strip() or gmail

    konfig = {
        "gmail": gmail,
        "app_passwort": app_pw,
        "empfaenger": empfaenger,
    }
    with open(KONFIG_DATEI, "w") as f:
        json.dump(konfig, f, indent=2)

    print("\n✓ Konfiguration gespeichert.")
    print("Test: python email_notifier.py --test")


def test_senden():
    konfig = konfig_laden()
    sende_email(
        konfig,
        betreff="✓ Conveni Workflow – Verbindungstest",
        html="<h2>Verbindung erfolgreich!</h2><p>Dein Conveni Workflow ist korrekt eingerichtet.</p>",
    )
    print("✓ Test-E-Mail gesendet an", konfig["empfaenger"])


def sende_email(konfig, betreff, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = betreff
    msg["From"] = konfig["gmail"]
    msg["To"] = konfig["empfaenger"]
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(konfig["gmail"], konfig["app_passwort"])
        server.sendmail(konfig["gmail"], konfig["empfaenger"], msg.as_string())


def tages_digest(csv_pfad):
    from fristenwächter import pruefe_fristen
    from status_manager import status_initialisieren, alle_status_holen, STATUSWERTE

    konfig = konfig_laden()
    fristen = pruefe_fristen(csv_pfad)
    status_initialisieren(csv_pfad)
    alle = alle_status_holen()
    heute = date.today().strftime("%d.%m.%Y")

    rot = fristen.get("rot", [])
    gelb = fristen.get("gelb", [])

    # Status-Zusammenfassung
    status_zaehler = {}
    for name, eintrag in alle.items():
        key = eintrag.get("aktuell", "neu")
        label = STATUSWERTE.get(key, {}).get("label", key)
        status_zaehler[label] = status_zaehler.get(label, 0) + 1

    # HTML aufbauen
    farbe_rot = "#dc3545"
    farbe_gelb = "#ffc107"
    farbe_gruen = "#28a745"
    farbe_blau = "#0d3b66"

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
      <div style="background:{farbe_blau};color:#fff;padding:20px 24px;border-radius:10px 10px 0 0;">
        <h1 style="margin:0;font-size:20px;">Conveni Workflow – {heute}</h1>
        <p style="margin:4px 0 0;opacity:0.8;font-size:13px;">Dein täglicher Überblick</p>
      </div>

      <div style="background:#f8f9fa;padding:16px 24px;">

        <!-- Alarme -->
        <h2 style="font-size:15px;color:{farbe_blau};margin-top:16px;">🔔 Fristenwächter</h2>
    """

    if not rot and not gelb:
        html += f'<p style="color:{farbe_gruen};font-weight:700;">✅ Keine dringenden Fristen heute.</p>'
    else:
        if rot:
            html += f'<div style="background:#fff3f3;border-left:4px solid {farbe_rot};padding:12px 16px;border-radius:4px;margin-bottom:8px;">'
            html += f'<strong style="color:{farbe_rot};">🔴 Dringend ({len(rot)})</strong><ul style="margin:8px 0 0;padding-left:18px;">'
            for a in rot:
                html += f'<li><strong>{a["kandidat"]}</strong> – {a["beschreibung"]}'
                if a.get("aktion"):
                    html += f'<br><span style="color:#555;font-size:12px;">→ {a["aktion"]}</span>'
                html += "</li>"
            html += "</ul></div>"

        if gelb:
            html += f'<div style="background:#fffbf0;border-left:4px solid {farbe_gelb};padding:12px 16px;border-radius:4px;margin-bottom:8px;">'
            html += f'<strong style="color:#856404;">🟡 Prüfen ({len(gelb)})</strong><ul style="margin:8px 0 0;padding-left:18px;">'
            for a in gelb[:5]:
                html += f'<li><strong>{a["kandidat"]}</strong> – {a["beschreibung"]}</li>'
            if len(gelb) > 5:
                html += f'<li style="color:#888;">+ {len(gelb)-5} weitere</li>'
            html += "</ul></div>"

    # Status-Übersicht
    html += f'<h2 style="font-size:15px;color:{farbe_blau};margin-top:20px;">👥 Kandidaten-Status</h2>'
    html += '<table style="width:100%;border-collapse:collapse;background:#fff;border-radius:6px;overflow:hidden;">'
    for label, anzahl in sorted(status_zaehler.items(), key=lambda x: -x[1]):
        html += f"""<tr style="border-bottom:1px solid #f0f0f0;">
          <td style="padding:8px 12px;font-size:13px;">{label}</td>
          <td style="padding:8px 12px;text-align:right;font-weight:700;color:{farbe_blau};">{anzahl}</td>
        </tr>"""
    html += "</table>"

    html += f"""
      </div>
      <div style="background:#dee2e6;padding:10px 24px;border-radius:0 0 10px 10px;font-size:11px;color:#666;text-align:center;">
        Conveni Personalvermittlung · Automatisch generiert · {heute}
      </div>
    </div>
    """

    betreff = f"Conveni Workflow {heute}"
    if rot:
        betreff = f"🔴 {len(rot)} dringende Alarme – {betreff}"
    elif gelb:
        betreff = f"🟡 {len(gelb)} Hinweise – {betreff}"
    else:
        betreff = f"✅ Alles OK – {betreff}"

    sende_email(konfig, betreff, html)
    print(f"✓ Tages-Digest gesendet an {konfig['empfaenger']}")
    if rot:
        print(f"  🔴 {len(rot)} dringende Alarme")
    if gelb:
        print(f"  🟡 {len(gelb)} Hinweise")


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--setup" in args:
        konfig_einrichten()
    elif "--test" in args:
        test_senden()
    elif args:
        tages_digest(args[0])
    else:
        print("Verwendung:")
        print("  python email_notifier.py --setup              # Einmalig einrichten")
        print("  python email_notifier.py --test               # Verbindung testen")
        print("  python email_notifier.py kandidaten.csv       # Digest senden")
