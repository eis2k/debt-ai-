DebtAI - Projektspezifikation

Projektziel

DebtAI ist eine vollständig lokal betriebene Anwendung zur Analyse und Konsolidierung von Schuldendokumenten.

Die Anwendung soll aus ca. 500–1000 eingescannten und in Paperless-ngx archivierten Dokumenten automatisch ein belastbares Schuldenverzeichnis erzeugen.

Ziel ist die Vorbereitung von:

* außergerichtlichen Vergleichen
* Schuldnerberatung
* Verbraucherinsolvenz
* Gläubigerverzeichnis
* Forderungsübersichten

Alle Daten verbleiben ausschließlich auf lokalen Systemen.

⸻

Ausgangssituation

Der Nutzer besitzt:

* NAS-System
* Paperless-ngx
* Windows-PC
* AMD Radeon RX 7800 XT mit 16 GB VRAM

Dokumente werden:

Drucker → NAS → Paperless-ngx

übertragen.

Paperless führt OCR durch und speichert die Dokumente.

⸻

Grundprinzip

Paperless bleibt das führende Dokumentenarchiv.

DebtAI liest Dokumente ausschließlich über die Paperless API aus.

Dokumente werden niemals verändert.

DebtAI erstellt ausschließlich strukturierte Metadaten und Analysen.

⸻

Technologiestack

Infrastruktur

* Docker Compose
* PostgreSQL 17
* pgvector
* Ollama
* Qwen3 14B (Standardmodell)

Backend

* Python 3.12
* FastAPI
* SQLAlchemy
* Alembic

Frontend

* React
* TypeScript
* Material UI

Authentifizierung

Lokale Benutzerverwaltung.

Kein Cloud Login.

Keine Drittanbieter.

⸻

Architektur

Container

postgres
backend
frontend
ollama

später optional:

worker
scheduler

⸻

Datenbankmodell

documents

Speichert alle aus Paperless importierten Dokumente.

Felder:

* id
* paperless_id
* filename
* created_at
* document_date
* document_type
* ocr_text
* checksum
* confidence_score

⸻

creditors

Eindeutige Gläubiger.

Felder:

* id
* canonical_name
* active
* notes

Beispiele:

Klarna
Telekom
EOS
Riverty

⸻

creditor_aliases

Alternative Schreibweisen.

Beispiele:

Klarna GmbH
Klarna Bank AB
Klarna Forderungsmanagement

zeigen auf:

Klarna

⸻

claims

Forderungen.

Felder:

* id
* creditor_id
* amount
* currency
* claim_reference
* contract_reference
* title_exists
* title_type
* status
* first_seen
* last_seen

⸻

claim_events

Historie.

Mögliche Typen:

* Rechnung
* Mahnung
* Inkasso
* Anwaltsschreiben
* Mahnbescheid
* Vollstreckungsbescheid
* Gerichtsvollzieher
* Kontopfändung
* Lohnpfändung
* Vergleich
* Zahlung

⸻

embeddings

Semantische Suche.

Felder:

* id
* document_id
* chunk_text
* embedding

pgvector verwenden.

⸻

Dokumentklassifikation

Die KI muss Dokumente klassifizieren.

Mögliche Klassen:

* Rechnung
* Zahlungserinnerung
* Mahnung
* Inkasso
* Anwalt
* Mahnbescheid
* Vollstreckungsbescheid
* Gericht
* Gerichtsvollzieher
* Pfändung
* Vergleich
* Sonstiges

⸻

Extraktion

Für jedes Dokument sollen folgende Daten extrahiert werden:

* Dokumenttyp
* Gläubiger
* Betrag
* Aktenzeichen
* Vertragsnummer
* Kundennummer
* Datum
* Forderungsstatus
* Titel vorhanden

Antwortformat ausschließlich JSON.

⸻

Konsolidierung

Das System soll Forderungen automatisch zusammenführen.

Kriterien:

* Aktenzeichen
* Vertragsnummer
* Kundennummer
* Gläubiger
* semantische Ähnlichkeit

Beispiel:

Klarna → Inkasso → Anwalt

soll als ein Fall erkannt werden.

⸻

Dashboard

Startseite

Anzeigen:

* Anzahl Dokumente
* Anzahl Gläubiger
* Anzahl Forderungen
* Gesamtschulden

⸻

Gläubigeransicht

Anzeigen:

* Gläubigername
* Gesamtsumme
* Anzahl Forderungen
* letzter Kontakt

⸻

Forderungsansicht

Anzeigen:

* Forderungshöhe
* Status
* Titel vorhanden
* Historie

⸻

Dokumentansicht

Anzeigen:

* PDF
* OCR Text
* Extrahierte Daten
* KI Bewertung

⸻

Suche

Normale Volltextsuche.

Zusätzlich semantische Suche mit pgvector.

Beispiele:

“Alle Kontopfändungen”

“Alle Schreiben von Klarna”

“Alle titulierten Forderungen”

⸻

KI Chat

Benutzer kann Fragen stellen:

* Welche Forderungen sind tituliert?
* Welche Gläubiger existieren?
* Welche Forderungen sind älter als fünf Jahre?
* Welche Forderungen wurden verkauft?

Antworten müssen Quellen angeben.

⸻

Vergleichsmodul

Benutzer gibt ein:

* verfügbares Monatsbudget
* Laufzeit

Beispiel:

250 Euro
36 Monate

System berechnet:

Gesamtbudget 9000 Euro

und erstellt:

* Vergleichsübersicht
* Gläubigerliste
* Quotenberechnung

Keine automatische Kontaktaufnahme.

⸻

Sicherheit

Keine Cloud.

Keine Datenübertragung.

Keine externen APIs.

Lokale Verarbeitung ausschließlich über Ollama.

⸻

Roadmap

Version 0.1

* Docker Setup
* PostgreSQL
* Paperless Import
* Dokumentenliste

Version 0.2

* KI Extraktion
* Forderungserkennung

Version 0.3

* Konsolidierung
* Gläubigerübersicht

Version 0.4

* Dashboard

Version 0.5

* KI Chat

Version 1.0

* Vergleichsmodul
* Exportfunktionen