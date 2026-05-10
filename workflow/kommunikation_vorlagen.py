"""
E-Mail & WhatsApp-Vorlagen: Generiert personalisierte Kommunikationstexte für
Kandidaten, Arbeitgeber und Kursträger – auf Knopfdruck aus den Kandidatendaten.

Verwendung:
  python kommunikation_vorlagen.py --liste                               # alle Vorlagen
  python kommunikation_vorlagen.py --vorlage erstanschreiben_kandidat \
      --kandidat "Nguyen Thi Lan" --csv kandidaten_vorlage.csv
  python kommunikation_vorlagen.py --vorlage whatsapp_kurserinnerung \
      --kandidat "Maria Santos" --kurs "VHS München" --datum "01.06.2026"
  python kommunikation_vorlagen.py --vorlage at_ablauf_warnung \
      --kandidat "Van Minh Tran" --tage 28
"""

import sys
import argparse
import pandas as pd
from pathlib import Path
from datetime import date

VORLAGEN: dict[str, dict] = {
    # ── Kandidaten ──────────────────────────────────────────────────────────
    "erstanschreiben_kandidat": {
        "label": "Erstanschreiben – Kandidat (DE)",
        "kanal": "E-Mail",
        "empfaenger": "Kandidat",
    },
    "erstanschreiben_kandidat_en": {
        "label": "First contact – Candidate (EN)",
        "kanal": "E-Mail",
        "empfaenger": "Kandidat",
    },
    "status_update_kandidat": {
        "label": "Status-Update – Kandidat",
        "kanal": "E-Mail",
        "empfaenger": "Kandidat",
    },
    "dokumente_anfordern": {
        "label": "Fehlende Unterlagen anfordern",
        "kanal": "E-Mail",
        "empfaenger": "Kandidat",
    },
    "kurs_erinnerung": {
        "label": "Kursbeginn-Erinnerung (1 Woche vorher)",
        "kanal": "E-Mail",
        "empfaenger": "Kandidat",
    },
    "at_ablauf_warnung": {
        "label": "Aufenthaltstitel-Ablauf-Warnung",
        "kanal": "E-Mail",
        "empfaenger": "Kandidat",
    },
    "kurs_abgeschlossen_glueckwunsch": {
        "label": "Glückwunsch Kursabschluss",
        "kanal": "E-Mail",
        "empfaenger": "Kandidat",
    },
    # ── WhatsApp (kurz) ──────────────────────────────────────────────────────
    "whatsapp_willkommen": {
        "label": "WhatsApp: Willkommen (DE/EN)",
        "kanal": "WhatsApp",
        "empfaenger": "Kandidat",
    },
    "whatsapp_kurserinnerung": {
        "label": "WhatsApp: Kurserinnerung",
        "kanal": "WhatsApp",
        "empfaenger": "Kandidat",
    },
    "whatsapp_dokument_fehlt": {
        "label": "WhatsApp: Dokument fehlt noch",
        "kanal": "WhatsApp",
        "empfaenger": "Kandidat",
    },
    "whatsapp_at_warnung": {
        "label": "WhatsApp: Aufenthaltstitel läuft ab",
        "kanal": "WhatsApp",
        "empfaenger": "Kandidat",
    },
    # ── Arbeitgeber ──────────────────────────────────────────────────────────
    "arbeitgeber_erstanschreiben": {
        "label": "Erstanschreiben – Arbeitgeber",
        "kanal": "E-Mail",
        "empfaenger": "Arbeitgeber",
    },
    "arbeitgeber_foerderantrag_erinnerung": {
        "label": "Arbeitgeber: Förderantrag noch offen",
        "kanal": "E-Mail",
        "empfaenger": "Arbeitgeber",
    },
    "arbeitgeber_ab_bestaetigung_anfordern": {
        "label": "Arbeitgeber: Arbeitgeberbestätigung anfordern",
        "kanal": "E-Mail",
        "empfaenger": "Arbeitgeber",
    },
    # ── Kursträger ───────────────────────────────────────────────────────────
    "kursträger_anmeldung": {
        "label": "Kursträger: Kursanmeldung",
        "kanal": "E-Mail",
        "empfaenger": "Kursträger",
    },
}


def _today_str() -> str:
    return date.today().strftime("%d.%m.%Y")


def generiere_vorlage(
    vorlage_key: str,
    kandidat_name: str = "[Vorname Nachname]",
    email: str = "",
    berufsfeld: str = "",
    sprachniveau: str = "",
    arbeitgeber: str = "[Arbeitgeber]",
    kursträger: str = "[Kursträger]",
    kurs_datum: str = "[Datum]",
    tage_at: int | None = None,
    fehlende_docs: list[str] | None = None,
    status_label: str = "",
    naechster_schritt: str = "",
) -> str:
    vorname = kandidat_name.split()[0] if kandidat_name else "Hallo"
    docs_str = "\n".join(f"  – {d}" for d in (fehlende_docs or ["[Dokumentenliste]"]))
    heute = _today_str()

    vorlagen_text = {

        "erstanschreiben_kandidat": f"""Betreff: Willkommen bei Conveni – Ihr persönlicher Förderungs-Workflow

Sehr geehrte/r {kandidat_name},

herzlich willkommen bei der Conveni Personalvermittlung! Wir freuen uns, Sie auf
Ihrem Weg in Deutschland begleiten zu dürfen.

Mein Name ist [Ihr Name], ich bin Ihr persönlicher Ansprechpartner für alle Fragen
rund um Sprachförderung, Aufenthaltstitel und berufliche Anerkennung.

In einem ersten Schritt werde ich für Sie prüfen, welche Förderungen für Sie in Frage
kommen – insbesondere Berufssprachkurse (BSK) und Integrationskurse des BAMF.

Was ich jetzt von Ihnen brauche:
  – Kopie Reisepass / Personalausweis
  – Kopie Aufenthaltstitel (§ ... AufenthG)
  – Meldebescheinigung
  – Lebenslauf auf Deutsch
  – Nachweise über Ihre Berufsausbildung / Qualifikation

Bitte senden Sie diese Unterlagen per E-Mail an [ihre-email@conveni.de] oder
bringen Sie sie direkt bei uns vorbei.

Bei Fragen können Sie mich jederzeit per E-Mail oder WhatsApp erreichen:
[Ihre Telefonnummer / WhatsApp]

Ich freue mich auf die Zusammenarbeit!

Mit freundlichen Grüßen
[Ihr Name]
Conveni Personalvermittlung | conveni.de""",

        "erstanschreiben_kandidat_en": f"""Subject: Welcome to Conveni – Your Personal Support Process

Dear {kandidat_name},

Welcome to Conveni! We are glad to support you on your journey in Germany.

My name is [Your Name] and I will be your personal contact person for all questions
about language funding, residence permits, and professional recognition.

As a first step, I will check which funding programs are available for you –
especially vocational language courses (BSK) and integration courses from BAMF.

What I need from you now:
  – Copy of passport / ID card
  – Copy of residence permit (§ ... AufenthG)
  – Registration certificate (Meldebescheinigung)
  – CV in German
  – Proof of your professional qualification / degree

Please send these documents by email to [your-email@conveni.de].

You can reach me at any time by email or WhatsApp:
[Your phone number / WhatsApp]

Looking forward to working with you!

Best regards,
[Your Name]
Conveni Personalvermittlung | conveni.de""",

        "status_update_kandidat": f"""Betreff: Ihr aktueller Bearbeitungsstand – {heute}

Liebe/r {vorname},

kurzes Update zu Ihrem Förderungs-Workflow:

Aktueller Status: {status_label or '[Status]'}
Nächster Schritt: {naechster_schritt or '[Nächster Schritt]'}

Bei Fragen stehe ich Ihnen jederzeit zur Verfügung.

Mit freundlichen Grüßen
[Ihr Name]
Conveni Personalvermittlung""",

        "dokumente_anfordern": f"""Betreff: Fehlende Unterlagen für Ihren Förderantrag

Liebe/r {vorname},

für die Beantragung Ihrer Sprachkursförderung fehlen noch folgende Unterlagen:

{docs_str}

Bitte senden Sie diese so bald wie möglich an [ihre-email@conveni.de].
Je schneller wir die Unterlagen haben, desto schneller können wir den Antrag stellen.

Bei Fragen melden Sie sich gerne!

Mit freundlichen Grüßen
[Ihr Name]
Conveni Personalvermittlung""",

        "kurs_erinnerung": f"""Betreff: Erinnerung – Ihr Kurs beginnt am {kurs_datum}!

Liebe/r {vorname},

nur zur Erinnerung: Ihr Sprachkurs bei {kursträger} beginnt am {kurs_datum}.

Bitte beachten Sie:
  ✓ Pünktlich vor Ort sein (ca. 15 Minuten vor Kursbeginn)
  ✓ Aufenthaltstitel mitbringen
  ✓ Arbeitgeber rechtzeitig über die Kurszeiten informieren (falls noch nicht geschehen)
  ✓ Bei Erkrankung: Kursträger UND uns sofort informieren

Adresse: [Kursträger-Adresse]
Ihr Kursmodul: [{berufsfeld or 'BSK'}]

Viel Erfolg!

Mit freundlichen Grüßen
[Ihr Name]
Conveni Personalvermittlung""",

        "at_ablauf_warnung": f"""Betreff: Wichtig – Ihr Aufenthaltstitel läuft {'in ' + str(tage_at) + ' Tagen' if tage_at else 'bald'} ab!

Liebe/r {vorname},

Ihr aktueller Aufenthaltstitel läuft {'in ' + str(tage_at) + ' Tagen' if tage_at else 'demnächst'} ab.
Bitte stellen Sie JETZT einen Verlängerungsantrag bei der Ausländerbehörde!

Was zu tun ist:
  1. Termin bei der Ausländerbehörde vereinbaren (möglichst diese Woche!)
  2. Arbeitgeber informieren – ggf. Arbeitgeberbescheinigung beantragen
  3. Uns Bescheid geben, sobald der neue Aufenthaltstitel vorliegt

Hinweis: Solange der Antrag auf Verlängerung gestellt und die Fiktionsbescheinigung
ausgestellt ist, dürfen Sie weiterhin arbeiten (§ 81 Abs. 4 AufenthG).

Bitte melden Sie sich umgehend bei uns, wenn Sie Hilfe benötigen!

Mit freundlichen Grüßen
[Ihr Name]
Conveni Personalvermittlung""",

        "kurs_abgeschlossen_glueckwunsch": f"""Betreff: Herzlichen Glückwunsch zum Kursabschluss! 🎉

Liebe/r {vorname},

herzlichen Glückwunsch zum erfolgreichen Abschluss Ihres Sprachkurses!

Das ist ein wichtiger Schritt für Ihre berufliche Zukunft in Deutschland.
Wir sind sehr stolz auf Ihren Einsatz.

Was als nächstes kommt:
{naechster_schritt or '  – Bitte kommen Sie mit Ihrem Zertifikat zu uns in die Beratung.'}

Mit freundlichen Grüßen
[Ihr Name]
Conveni Personalvermittlung""",

        # ── WhatsApp ──────────────────────────────────────────────────────────

        "whatsapp_willkommen": f"""🇩🇪 Hallo {vorname}! Willkommen bei Conveni Personalvermittlung.
Ich bin [Ihr Name], Ihr Ansprechpartner für Sprachkurse und Förderung.
Bei Fragen jederzeit schreiben! 😊

🇬🇧 Hello {vorname}! Welcome to Conveni.
I'm [Your Name], your contact for language courses and funding.
Feel free to message anytime! 😊""",

        "whatsapp_kurserinnerung": f"""Hallo {vorname} 👋
Nur kurze Erinnerung: Ihr Kurs bei {kursträger} startet am {kurs_datum}!
Bitte rechtzeitig da sein. Bei Fragen: einfach schreiben. Viel Erfolg! 💪""",

        "whatsapp_dokument_fehlt": f"""Hallo {vorname} 👋
Für Ihren Förderantrag fehlt noch:
{docs_str}
Bitte so bald wie möglich schicken. Danke! 🙏""",

        "whatsapp_at_warnung": f"""⚠️ Wichtig {vorname}!
Ihr Aufenthaltstitel läuft {'in ' + str(tage_at) + ' Tagen' if tage_at else 'bald'} ab.
Bitte JETZT Termin bei der Ausländerbehörde holen!
Bei Fragen helfen wir gerne. 📞""",

        # ── Arbeitgeber ───────────────────────────────────────────────────────

        "arbeitgeber_erstanschreiben": f"""Betreff: Sprachförderung für Ihre internationalen Mitarbeiter – Conveni

Sehr geehrte Damen und Herren,

{kandidat_name} ist über uns in Ihrem Unternehmen tätig. Im Rahmen unserer
Begleitung prüfen wir für alle vermittelten Mitarbeiter die Möglichkeiten
zur Sprachförderung.

Wir möchten Sie darüber informieren, dass für {vorname} folgende Förderungen
möglich sind:
  – Berufssprachkurs (BSK): Sie erhalten als Arbeitgeber Lohnkostenzuschuss
    während der Kurszeit über das Qualifizierungschancengesetz (§ 82 SGB III)
  – BAMF übernimmt die Kurskosten

Als nächsten Schritt würden wir gerne einen kurzen Abstimmungstermin vereinbaren.

Mit freundlichen Grüßen
[Ihr Name]
Conveni Personalvermittlung""",

        "arbeitgeber_foerderantrag_erinnerung": f"""Betreff: Erinnerung – Förderantrag für {kandidat_name} noch offen

Sehr geehrte Damen und Herren,

der Antrag auf Lohnkostenzuschuss nach dem Qualifizierungschancengesetz
(§ 82 SGB III) für {kandidat_name} ist noch nicht bei der Agentur für Arbeit
eingereicht worden.

WICHTIG: Der Antrag muss VOR Kursbeginn gestellt werden!

Bitte wenden Sie sich an:
  Agentur für Arbeit → Arbeitgeber-Service
  Kostenloser Rückruf: arbeitsagentur.de

Bei Fragen helfen wir Ihnen gerne weiter.

Mit freundlichen Grüßen
[Ihr Name]
Conveni Personalvermittlung""",

        "arbeitgeber_ab_bestaetigung_anfordern": f"""Betreff: Bitte um Arbeitgeberbestätigung für {kandidat_name}

Sehr geehrte Damen und Herren,

für den BSK-Antrag (Berufssprachkurs) von {kandidat_name} benötigen wir eine
Arbeitgeberbestätigung mit:
  ✓ Firmenname und -stempel
  ✓ Unterschrift der Geschäftsführung
  ✓ Bestätigung des Beschäftigungsverhältnisses
  ✓ Bestätigung der Freistellung für Kurszeiten

Ein Formular finden Sie im Anhang. Bitte zurücksenden an:
[ihre-email@conveni.de]

Vielen Dank!

Mit freundlichen Grüßen
[Ihr Name]
Conveni Personalvermittlung""",

        "kursträger_anmeldung": f"""Betreff: Kursanmeldung – {kandidat_name}

Sehr geehrte Damen und Herren,

ich möchte folgenden Kandidaten für einen Kurs bei Ihnen anmelden:

Name:            {kandidat_name}
Berufsfeld:      {berufsfeld or '[Berufsfeld]'}
Aktuelles Niveau:{sprachniveau or '[Niveau]'}
Gewünschtes Modul: [BSK-Modul]
Gewünschter Kursbeginn: {kurs_datum}

Bitte teilen Sie mir mit, ob ein Platz verfügbar ist und wann der
nächste Einstufungstest stattfindet.

Wir sind BAMF-anerkannte Personalvermittlung und koordinieren die
Förderanträge vorab.

Mit freundlichen Grüßen
[Ihr Name]
Conveni Personalvermittlung""",
    }

    text = vorlagen_text.get(vorlage_key)
    if not text:
        return f"Vorlage '{vorlage_key}' nicht gefunden. Verfügbare Vorlagen: --liste"
    return text


def _lade_kandidat_aus_csv(name: str, csv_pfad: str | None = None) -> dict:
    eingabe = Path(csv_pfad) if csv_pfad else Path(__file__).parent / "kandidaten_vorlage.csv"
    if not eingabe.exists():
        return {}
    df = pd.read_csv(eingabe) if eingabe.suffix == ".csv" else pd.read_excel(eingabe)
    from check_foerderung import pruefe_kandidat
    for _, zeile in df.iterrows():
        vname = f"{zeile.get('vorname', '')} {zeile.get('nachname', '')}".strip()
        if name.lower() in vname.lower():
            return pruefe_kandidat(zeile)
    return {}


def main():
    parser = argparse.ArgumentParser(description="Kommunikationsvorlagen – E-Mail & WhatsApp")
    parser.add_argument("--liste", action="store_true", help="Alle verfügbaren Vorlagen anzeigen")
    parser.add_argument("--vorlage", metavar="KEY", help="Vorlage generieren")
    parser.add_argument("--kandidat", metavar="NAME", help="Kandidatenname für Personalisierung")
    parser.add_argument("--csv", metavar="PFAD", help="Kandidaten-CSV für automatische Befüllung")
    parser.add_argument("--kurs", metavar="NAME", default="[Kursträger]", help="Kursträger-Name")
    parser.add_argument("--datum", metavar="DD.MM.YYYY", default="[Datum]", help="Kursdatum")
    parser.add_argument("--tage", type=int, help="Tage bis Aufenthaltstitel-Ablauf")
    parser.add_argument("--docs", nargs="+", metavar="DOK", help="Fehlende Dokumente (Leerzeichen-getrennt)")
    args = parser.parse_args()

    if args.liste:
        print("\nVerfügbare Kommunikationsvorlagen:")
        letzter_kanal = ""
        for key, meta in VORLAGEN.items():
            if meta["kanal"] != letzter_kanal:
                print(f"\n  [{meta['kanal']}]")
                letzter_kanal = meta["kanal"]
            print(f"  {key:<42} → {meta['label']}")
        print()
        return

    if not args.vorlage:
        parser.print_help()
        return

    # Kandidatendaten aus CSV laden
    k_daten: dict = {}
    if args.kandidat and args.csv:
        k_daten = _lade_kandidat_aus_csv(args.kandidat, args.csv)

    text = generiere_vorlage(
        vorlage_key=args.vorlage,
        kandidat_name=args.kandidat or k_daten.get("name", "[Name]"),
        email=k_daten.get("email", ""),
        berufsfeld=k_daten.get("berufsfeld", ""),
        sprachniveau=k_daten.get("sprachniveau", ""),
        arbeitgeber=k_daten.get("arbeitgeber", "[Arbeitgeber]"),
        kursträger=args.kurs,
        kurs_datum=args.datum,
        tage_at=args.tage,
        fehlende_docs=args.docs,
        status_label=k_daten.get("workflow_status", {}).get("label", ""),
        naechster_schritt=(k_daten.get("naechste_schritte") or [{}])[0].get("schritt", ""),
    )

    print("\n" + "=" * 62)
    print(text)
    print("=" * 62 + "\n")


if __name__ == "__main__":
    main()
