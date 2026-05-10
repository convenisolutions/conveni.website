# Sprachförderungs-Workflow – Conveni Personalvermittlung

Automatisierter Workflow zur Förderberechtigung, Aufenthaltsweg-Analyse, Anerkennungsberatung, Dokumenten-Tracking und Kandidaten-Management für Fachkräfte aus Drittstaaten (Philippinen, Vietnam).

---

## Schnellstart

```bash
pip install -r requirements.txt

# Alles auf einmal (alle Berichte regenerieren)
python run_all.py kandidaten_vorlage.csv

# Web-Interface starten (empfohlen)
python app.py
# → Browser: http://localhost:5001
```

---

## Web-Interface (Flask)

Das Web-Interface bietet eine browserbasierte Oberfläche für alle Funktionen:

```bash
python app.py
```

| Seite | URL | Funktion |
|---|---|---|
| Dashboard | `/` | KPI-Karten, Fristenwächter, Kandidaten-Übersicht |
| Kandidaten | `/kandidaten` | Workflow-Status + Notiz inline speichern |
| Dokumente | `/dokumente` | Checkbox-Tracking je Kandidat |
| Vorlagen | `/vorlagen` | E-Mail / WhatsApp Texte generieren & kopieren |
| Berichte | `/berichte` | Alle Berichte per Klick generieren |

---

## Skripte im Überblick

### Alles auf einmal

| Script | Beschreibung |
|---|---|
| `run_all.py [CSV]` | Führt alle 12 Skripte sequenziell aus, zeigt ✓/✗ je Schritt |
| `app.py` | Flask-Webserver auf Port 5001 |

### Analyse & Prüfung

| Script | Beschreibung | Output |
|---|---|---|
| `check_foerderung.py [CSV]` | Förderberechtigung aller Kandidaten prüfen | Konsolenausgabe |
| `status_manager.py --liste` | Aktuellen Workflow-Status aller Kandidaten anzeigen | Konsole |

### Berichte generieren

| Script | Beschreibung | Datei in `output/` |
|---|---|---|
| `generate_uebersicht.py [CSV]` | Kandidaten-Dashboard mit Status & Fortschritt | `uebersicht.html` |
| `generate_checklisten.py [CSV]` | Individuelle Checkliste pro Kandidat | `checkliste_<name>.html` |
| `generate_formulare.py [CSV]` | BAMF-Formular-Hinweise je Kandidat | `formulare_<name>.html` |
| `generate_kalender.py [CSV]` | Fristen-Kalender (ICS für Outlook/Google) | `fristen.ics` |
| `generate_arbeitgeber_mappe.py [CSV]` | Arbeitgeber-Förderungsmappe | `arbeitgeber_<name>.html` |
| `generate_partnerschulen_bericht.py [CSV]` | Kursträger-Pipeline & Kandidaten-Matching | `partnerschulen_bericht.html` |
| `generate_qualitaet_bericht.py [CSV]` | Kursqualität, KPIs, Rangliste | `qualitaet_bericht.html` |
| `generate_monatsbericht.py [CSV]` | Monatsbericht mit Fördervolumen | `monatsbericht_<JJJJ-MM>.html` |
| `generate_dokumente_bericht.py [CSV]` | Dokumenten-Vollständigkeit je Kandidat | `dokumente_bericht.html` |
| `fristenwächter.py [CSV] [--html]` | Täglicher Fristenalarm (cron-fähig) | `alarm_report.html` (bei Alarmen) |

### Daten-Manager (CLI + Python-API)

| Modul | CLI-Beispiel | Beschreibung |
|---|---|---|
| `status_manager.py` | `--setze "Max M." kurs_laeuft` | Workflow-Status pro Kandidat verwalten |
| `dokumente_manager.py` | `--setze "Max M." reisepass vorhanden` | Dokumenten-Status (12 Typen) tracken |
| `partnerschulen_manager.py` | `--match kandidaten.csv` | Schulen-Datenbank + Kandidaten-Matching |
| `qualitaet_manager.py` | `--kpis` | Kursqualität erfassen und KPIs berechnen |
| `kommunikation_vorlagen.py` | `--vorlage einladung_einstufungstest --kandidat "M."` | 16 E-Mail/WhatsApp-Vorlagen |
| `google_sheets_sync.py` | `--sheets-id SHEET_ID --csv out.csv` | Google Sheets → CSV Export + alle Berichte |

---

## Workflow-Status (15 Stufen)

| Schlüssel | Label | Farbe | Fortschritt |
|---|---|---|---|
| `neu` | Neu erfasst | grau | 0% |
| `erstgespraech` | Erstgespräch | blau | 7% |
| `dokumente_pruefen` | Dokumente prüfen | blau | 14% |
| `foerderung_pruefen` | Förderung prüfen | blau | 21% |
| `antrag_stellen` | Antrag stellen | orange | 28% |
| `antrag_eingereicht` | Antrag eingereicht | orange | 36% |
| `warteliste` | Auf Warteliste | orange | 43% |
| `kursplatz_zugewiesen` | Kursplatz zugewiesen | orange | 50% |
| `kurs_laeuft` | Kurs läuft | blau | 60% |
| `pruefung_angemeldet` | Prüfung angemeldet | blau | 70% |
| `pruefung_bestanden` | Prüfung bestanden | gruen | 80% |
| `pruefung_nicht_bestanden` | Prüfung nicht bestanden | rot | 75% |
| `wiederholt_kurs` | Wiederholt Kurs | orange | 65% |
| `vermittelt` | Vermittelt / beschäftigt | gruen | 95% |
| `abgeschlossen` | Abgeschlossen | gruen | 100% |

Statuswechsel: `python status_manager.py --setze "Name" <schlüssel>`

---

## Dokument-Typen (12 Typen)

| Typ-ID | Bezeichnung | Pflicht |
|---|---|---|
| `reisepass` | Reisepass / Nationalpass | ✓ |
| `aufenthaltstitel` | Aufenthaltstitel | ✓ |
| `meldebescheinigung` | Meldebescheinigung | ✓ |
| `lichtbild` | Lichtbild (biometrisch) | ✓ |
| `lebenslauf` | Lebenslauf | ✓ |
| `qualifikationsnachweis` | Qualifikationsnachweis | ✓ |
| `krankenversicherung` | Krankenversicherungsnachweis | |
| `ab_bestaetigung` | Anerkennungsberatung-Bestätigung | |
| `bamf_antrag` | BAMF-Antrag (Formular) | |
| `einstufungstest` | Einstufungstest-Ergebnis | |
| `anerkennung_antrag` | Anerkennungsantrag | |
| `arbeitsvertrag` | Arbeitsvertrag | |

Status-Werte: `vorhanden` · `fehlend` · `angefordert` · `nicht_relevant`

---

## Kommunikationsvorlagen (16 Vorlagen)

```bash
python kommunikation_vorlagen.py --liste
python kommunikation_vorlagen.py --vorlage einladung_einstufungstest --kandidat "Anna M." --datum "15.06.2026"
```

| Schlüssel | Kanal | Empfänger |
|---|---|---|
| `einladung_einstufungstest` | E-Mail | Kandidat |
| `kursbestaetigung` | E-Mail | Kandidat |
| `kursstart_erinnerung` | E-Mail | Kandidat |
| `dokumente_anfordern` | E-Mail | Kandidat |
| `foerderantrag_info` | E-Mail | Kandidat |
| `pruefung_vorbereitung` | E-Mail | Kandidat |
| `glueckwunsch_bestanden` | E-Mail | Kandidat |
| `vermittlung_erfolg` | E-Mail | Kandidat |
| `wa_kursstart` | WhatsApp | Kandidat |
| `wa_dokumente` | WhatsApp | Kandidat |
| `wa_pruefung_erinnerung` | WhatsApp | Kandidat |
| `at_ablauf_erinnerung` | E-Mail | Kandidat |
| `ag_foerderung_info` | E-Mail | Arbeitgeber |
| `ag_eg_zuschuss` | E-Mail | Arbeitgeber |
| `kursträger_anfrage` | E-Mail | Kursträger |
| `kursträger_feedback` | E-Mail | Kursträger |

---

## Fristenwächter (täglicher Cron)

```bash
# Manuell ausführen
python fristenwächter.py kandidaten_vorlage.csv

# Mit HTML-Bericht
python fristenwächter.py kandidaten_vorlage.csv --html

# Als täglichen Cron einrichten (08:00 Uhr)
0 8 * * * cd /pfad/zum/workflow && python fristenwächter.py kandidaten.csv --html
```

Überwacht:
- Aufenthaltstitel-Ablauf: **rot** < 30 Tage, **gelb** < 90 Tage
- Wiedervorlagen: **rot** wenn hoch-prioritär & < 14 Tage (oder überfällig)
- Inaktive Kandidaten: **gelb** wenn Status > 45 Tage unverändert

---

## Partnerschulen-Akquise

```bash
# Alle Schulen anzeigen
python partnerschulen_manager.py --liste

# Nur aktive Partner
python partnerschulen_manager.py --liste aktiv

# Kandidaten mit passenden Schulen matchen
python partnerschulen_manager.py --match kandidaten_vorlage.csv

# Akquise-E-Mail für Schule generieren
python partnerschulen_manager.py --akquise-email S001

# Kontaktstatus aktualisieren
python partnerschulen_manager.py --status S001 angebot_erhalten
```

Pipeline-Stufen: `noch_nicht` → `angefragt` → `angebot_erhalten` → `vertrag` → `aktiv` → `inaktiv`

---

## Qualitätsmanagement

```bash
# KPIs berechnen
python qualitaet_manager.py --kpis

# Kursträger-Rangliste
python qualitaet_manager.py --kurstraeger

# Kursergebnis erfassen
python qualitaet_manager.py --erfasse "Max M." --kurs S001 --modul BSK-900 \
  --ergebnis bestanden --niveau B2 --bewertung 5
```

---

## Förderprogramme (9 Programme)

| Programm | Förderer | Kosten Kandidat |
|---|---|---|
| Berufssprachkurs BSK (§45a AufenthG) | BAMF | ca. 2,07 €/UE Eigenanteil |
| Integrationskurs §43 AufenthG (5 Varianten) | BAMF | ca. 1,95 €/UE (Erlass möglich) |
| FbD – berufsbezogenes Deutsch | BAMF / ESF | kostenfrei |
| § 421 SGB III – Bildungsgutschein | Agentur für Arbeit | kostenfrei |
| IQ Netzwerk – Anerkennungsberatung | BMAS / ESF | kostenfrei |
| Nachqualifizierung / AVGS | AA / ESF | kostenfrei |
| Qualifizierungschancengesetz §82 SGB III | Agentur für Arbeit | Rest nach Förderung |
| Eingliederungszuschuss §88 SGB III | Agentur für Arbeit | – (für Arbeitgeber) |
| Bildungsprämie | BMBF | 50% Eigenanteil (max. 500 €) |

**Eingliederungszuschuss:** Bis 50% des Lohns für 12 Monate – Antrag **vor** Arbeitsaufnahme!

---

## Benötigte CSV-Spalten

| Spalte | Beispiel | Pflicht |
|---|---|---|
| `nachname` | Nguyen | ✓ |
| `vorname` | Thi Lan | ✓ |
| `geburtsdatum` | 1990-05-15 | ✓ |
| `geschlecht` | weiblich / männlich | ✓ |
| `nationalitaet` | Vietnam | ✓ |
| `aufenthaltstitel` | Aufenthaltserlaubnis § 18a | ✓ |
| `aufenthaltstitel_gueltig_bis` | 2026-12-31 | ✓ |
| `einreisedatum` | 2024-03-01 | |
| `sprachniveau_aktuell` | A2 | ✓ |
| `alphabetisierungsbedarf` | ja / nein | ✓ |
| `beschaeftigt` | ja / nein | ✓ |
| `arbeitgeber` | Pflegeheim GmbH | |
| `arbeitgeber_groesse` | klein / mittel / groß | ✓ |
| `berufsfeld` | Pflege | ✓ |
| `qualifikation_abschluss` | Berufsausbildung / Bachelor / Master | |
| `qualifikation_fach` | Krankenpflege | |
| `anerkennungsverfahren` | abgeschlossen / laufend / nicht beantragt | ✓ |
| `integrationskurs_verpflichtet` | ja / nein | |
| `email` | kandidat@example.com | |
| `telefon` | +49 151 … | |

Vorlage: `kandidaten_vorlage.csv`

---

## Datendateien

| Datei | Inhalt |
|---|---|
| `status.json` | Workflow-Status + Verlauf je Kandidat |
| `dokumente.json` | Dokumenten-Status (12 Typen) je Kandidat |
| `schulen.json` | Partnerschulen-Datenbank mit Kontakt-Pipeline |
| `qualitaet.json` | Kursqualität-Einträge je Kandidat |

---

## Google Sheets einbinden

```bash
# Service-Account-Schlüssel in credentials.json ablegen, dann:
python google_sheets_sync.py --sheets-id <SHEET_ID> --csv kandidaten.csv
```

Das Script exportiert die Tabelle als CSV und regeneriert alle Berichte.

---

## Unterstützte Berufsfelder

`Pflege` · `Altenpflege` · `Krankenpflege` · `Medizin` · `Arztpraxis` · `Zahnmedizin` · `Erziehung` · `Sozialpädagogik` · `Sozialarbeit` · `Handwerk` · `Bau` · `Elektro` · `Metall` · `Logistik` · `Gastronomie` · `Einzelhandel` · `Transport` · `Reinigung` · `IT` · `Ingenieur` · `Kaufmännisch` · `Finanz` · `Verwaltung`
