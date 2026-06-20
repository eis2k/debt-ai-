DebtAI - Projektspezifikation

Ziel

Entwicklung einer vollständig lokal laufenden Anwendung zur Analyse von Schuldendokumenten.

Der Nutzer besitzt ca. 500-1000 Dokumente (PDFs und Scans), die in Paperless-ngx gespeichert werden.

Die Anwendung soll diese Dokumente analysieren und daraus automatisch ein Schuldenverzeichnis erzeugen.

Infrastruktur

* Paperless-ngx
* PostgreSQL
* pgvector
* Ollama
* Qwen 3
* Docker Compose

Funktionen

Dokumentenimport

Die Anwendung soll Dokumente aus Paperless über die API abrufen.

KI-Extraktion

Folgende Informationen sollen erkannt werden:

* Gläubiger
* Forderungsbetrag
* Aktenzeichen
* Vertragsnummer
* Dokumenttyp
* Datum
* Status

Datenbank

Tabellen:

* documents
* creditors
* creditor_aliases
* claims
* events

Dashboard

* Gesamtschulden
* Gläubigerliste
* Forderungsliste
* Dokumentensuche

Nichtziele

* Cloudbetrieb
* externe APIs
* automatische Kontaktaufnahme mit Gläubigern