# Sprachförderungs-Workflow – Conveni Personalvermittlung

Automatisierte Prüfung der Förderberechtigung und Dokumenten-Checklisten für Fachkräfte aus Drittstaaten (Philippinen, Vietnam).

## Was dieser Workflow macht

1. **Kandidatendaten einlesen** – aus Google Sheets (CSV-Export) oder Excel
2. **Förderberechtigung prüfen** – für BSK, FbD, Integrationskurs, § 421 SGB III
3. **Checklisten generieren** – druckfertige HTML-Dokumente pro Kandidat

## Rechtliche Grundlagen

| Programm | Grundlage | Förderer |
|---|---|---|
| Berufssprachkurs (BSK) | § 45a AufenthG, DeuFöV | BAMF |
| FbD | ESF-Bundesprogramm | BAMF / ESF |
| Integrationskurs | § 43 AufenthG, IntV | BAMF |
| Sprachkurs Arbeitssuchende | § 421 SGB III | Agentur für Arbeit |

## Schnellstart

```bash
# 1. Abhängigkeiten installieren
pip install -r requirements.txt

# 2. Kandidatendaten prüfen (Konsolenausgabe)
python check_foerderung.py kandidaten.csv

# 3. PDF-Checklisten generieren (öffnet Ordner "output/")
python generate_checklisten.py kandidaten.csv
```

## Google Sheets einrichten

1. In Google Sheets: **Datei → Herunterladen → CSV** (oder `.xlsx`)
2. Das Script per CSV-Export aufrufen

**Benötigte Spalten** (Spaltenreihenfolge ist egal):

| Spalte | Beispiel |
|---|---|
| `nachname` | Nguyen |
| `vorname` | Thi Lan |
| `geburtsdatum` | 1990-05-15 |
| `nationalitaet` | Vietnam |
| `aufenthaltstitel` | Aufenthaltserlaubnis § 18a |
| `aufenthaltstitel_gueltig_bis` | 2026-12-31 |
| `einreisedatum` | 2024-03-01 |
| `sprachniveau_aktuell` | A2 |
| `beschaeftigt` | ja |
| `arbeitgeber` | Pflegeheim GmbH |
| `berufsfeld` | Pflege |
| `anerkennungsverfahren` | abgeschlossen / laufend / nicht beantragt |
| `email` | kandidat@example.com |
| `telefon` | +49 151 ... |

Die Datei `kandidaten_vorlage.csv` dient als Vorlage – einfach kopieren und mit echten Daten befüllen.

## Ausgabe-Beispiel

```
=================================================================
  FÖRDERBERECHTIGUNGS-PRÜFUNG – 10.05.2026
  Kandidaten gesamt: 5
=================================================================

Kandidat: Thi Lan Nguyen (Vietnam)
  Sprachniveau: A2 | Beschäftigt: Ja | Berufsfeld: Pflege
  Förderprogramme (3):
    ✓ Berufssprachkurs (BSK)
      → BSK-Modul Pflege (900 UE)
      → Förderung durch: BAMF
    ✓ FbD – Förderung berufsbez. Deutschkenntnisse
      → Standardkurs
      → Förderung durch: BAMF / ESF
    ✓ Integrationskurs
      → Integrationskurs (660 UE + 100 UE Orientierung)
      → Förderung durch: BAMF
```

## Checklisten-PDF erstellen

Nach `generate_checklisten.py` liegt im Ordner `output/` eine HTML-Datei pro Kandidat:

1. HTML-Datei im Browser öffnen (Chrome/Edge empfohlen)
2. **Strg+P** → Als PDF speichern

## Nächste Ausbaustufe (optional)

- **Google Sheets API**: Direkte Anbindung ohne CSV-Export
- **E-Mail-Versand**: Automatisch Checkliste an Kandidaten und Arbeitgeber senden
- **Wiedervorlage**: Automatische Erinnerung wenn Aufenthaltstitel bald abläuft
- **BAMF-Formulare**: Automatisch vorausgefüllte Antragsformulare als PDF
