# Sprachförderungs-Workflow – Conveni Personalvermittlung

Automatisierter Workflow zur Förderberechtigung, Aufenthaltsweg-Analyse, Anerkennungsberatung und Dokumenten-Checklisten für Fachkräfte aus Drittstaaten (Philippinen, Vietnam).

## Was dieser Workflow leistet

| Funktion | Script | Output |
|---|---|---|
| Förderberechtigung prüfen | `check_foerderung.py` | Konsolenausgabe |
| Checkliste pro Kandidat | `generate_checklisten.py` | HTML/PDF je Kandidat |
| Gesamtübersicht / Dashboard | `generate_uebersicht.py` | HTML-Dashboard |

## Schnellstart

```bash
pip install -r requirements.txt

# Prüfung (Konsole)
python check_foerderung.py kandidaten_vorlage.csv

# Individuelle Checklisten (HTML → PDF)
python generate_checklisten.py kandidaten_vorlage.csv

# Gesamt-Dashboard (HTML → PDF)
python generate_uebersicht.py kandidaten_vorlage.csv
```

Alle Ausgaben landen im Ordner `output/`. Im Browser öffnen → Drucken → Als PDF speichern.

---

## Was automatisch analysiert wird

### Förderprogramme (9 Programme geprüft)

| Programm | Förderer | Kosten Kandidat |
|---|---|---|
| Berufssprachkurs (BSK) | BAMF | ca. 2,07 €/UE Eigenanteil |
| Integrationskurs (5 Varianten) | BAMF | ca. 1,95 €/UE (Erlass möglich) |
| FbD – berufsbez. Deutsch | BAMF / ESF | kostenfrei |
| § 421 SGB III – Bildungsgutschein | Agentur für Arbeit | kostenfrei |
| IQ Netzwerk – Anerkennungsberatung | BMAS / ESF | kostenfrei |
| Nachqualifizierung / AVGS | AA / ESF | kostenfrei |
| Qualifizierungschancengesetz | Agentur für Arbeit | Rest nach Förderung |
| Eingliederungszuschuss | Agentur für Arbeit | Rest nach Förderung |
| Bildungsprämie | BMBF | 50% Eigenanteil (max. 500 € Zuschuss) |

### Integrationskurs – automatisch gewählte Variante

| Kurstyp | Umfang | Wann gewählt |
|---|---|---|
| Alphabetisierungskurs | 900 + 100 UE | `alphabetisierungsbedarf = ja` |
| Jugend-Integrationskurs | 900 + 100 UE | Alter unter 27 Jahre |
| Frauen-/Elternkurs | 660 + 100 UE | Geschlecht = weiblich |
| Intensiv-Integrationskurs | 430 + 30 UE | Niveau A2 |
| Allgemeiner Integrationskurs | 660 + 100 UE | Standard (A1, männlich, ≥27) |

### BSK-Modul – automatisch nach Berufsfeld

| Modul | Umfang | Berufsfelder |
|---|---|---|
| BSK-Spezialkurs Pflege | **900 UE** | Pflege, Altenpflege, Krankenpflege |
| BSK-Spezialkurs Medizin | **900 UE** | Medizin, Arztpraxis, Zahnmedizin |
| BSK-Spezialkurs Pädagogik | **900 UE** | Erziehung, Sozialpädagogik |
| BSK-Fachkurs | 400 UE | IT, Ingenieur, Kaufmännisch, Finanz |
| BSK-Standardkurs | 510 UE | Handwerk, Bau, Gastronomie, Logistik, … |

### Aufenthaltsweg-Analyse

Das Script erkennt automatisch den § AufenthG und zeigt:
- Bezeichnung und Beschreibung des Aufenthaltstitels
- Wann die **Niederlassungserlaubnis** möglich ist
- Welches **Sprachziel** dafür nötig ist (meist B1)
- Strategische Empfehlung (z.B. B1-Kurs für Blaue Karte: spart 12 Monate!)

| Aufenthaltstitel | NE möglich nach |
|---|---|
| § 18a (Berufsausbildung) | 4 Jahre – oder 2 Jahre mit B1! |
| § 18b (Hochschulabschluss) | 4 Jahre – oder 2 Jahre mit B1 |
| Blaue Karte EU (§ 18c) | **21 Monate** mit B1 (sonst 33 Monate) |
| § 16d (Anerkennungsaufenthalt) | Nach Anerkennung: → § 18a/18b |
| Niederlassungserlaubnis | Bereits vorhanden → Einbürgerung prüfen |

### Anerkennungsstelle

Pro Berufsfeld wird automatisch die zuständige Stelle ausgegeben:
- Pflege/Krankenpflege: Landesamt für Gesundheit (ZBFS Bayern, BezReg NRW, …)
- Medizin: Landesärztekammer
- Handwerk: Handwerkskammer (HWK)
- IT: Keine Anerkennung nötig (nicht reglementiert)
- Ingenieur: KMK/NARIC + Ingenieurkammer

### Ampelstatus (für Dashboard)

| Farbe | Bedeutung |
|---|---|
| Rot | Aufenthaltstitel läuft ab / Anerkennung fehlt bei reglementierten Berufen |
| Gelb | Handlungsbedarf: Schritte anstehend, Hinweise vorhanden |
| Grün | Alles im Plan |

### Nächste Schritte (priorisiert)

Für jeden Kandidaten generiert das Script einen priorisierten Aktionsplan:

1. **SOFORT** – Aufenthaltstitel verlängern, Anerkennung einleiten
2. **DIESE WOCHE** – Einstufungstest, IQ-Beratung, AA-Anmeldung
3. **DIESEN MONAT** – BSK/Integrationskurs anmelden, FbD beantragen
4. **LANGFRISTIG** – B1-Zertifikat, Anerkennungsverfahren abschließen

### Arbeitgeberförderung

Das Script prüft auch Förderungen für den Arbeitgeber:

**Qualifizierungschancengesetz (§ 82 SGB III)**
| Betriebsgröße | Lehrgangskosten | Lohnkostenzuschuss |
|---|---|---|
| Klein (<10 MA) | 100% | 75% |
| Mittel (10–249 MA) | 50% | 50% |
| Groß (≥250 MA) | 25% | 25% |

**Eingliederungszuschuss (§ 88 SGB III):** Bis 50% des Lohns für 12 Monate bei Neueinstellung – Antrag muss VOR Arbeitsaufnahme gestellt werden!

---

## Google Sheets einrichten

1. In Google Sheets: **Datei → Herunterladen → CSV** (oder `.xlsx`)
2. Script aufrufen: `python check_foerderung.py meine_kandidaten.csv`

### Benötigte Spalten

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

Die Datei `kandidaten_vorlage.csv` als Kopiervorlage nutzen.

---

## Unterstützte Berufsfelder

`Pflege` · `Altenpflege` · `Krankenpflege` · `Medizin` · `Arztpraxis` · `Zahnmedizin` · `Erziehung` · `Sozialpädagogik` · `Sozialarbeit` · `Handwerk` · `Bau` · `Elektro` · `Metall` · `Logistik` · `Gastronomie` · `Einzelhandel` · `Transport` · `Reinigung` · `IT` · `Ingenieur` · `Kaufmännisch` · `Finanz` · `Verwaltung`

---

## Nächste Ausbaustufen (optional)

- **Google Sheets API** – Direktanbindung ohne CSV-Export nötig
- **E-Mail-Versand** – Automatisch Checkliste an Kandidaten und Arbeitgeber schicken
- **Erinnerungs-Mails** – Automatische Mail 90 Tage vor Ablauf des Aufenthaltstitels
- **BAMF-Formular-Prefill** – Vorausgefüllte PDF-Antragsformulare generieren
- **Webhook / Zapier-Integration** – Neue Kandidaten aus Formular direkt verarbeiten
