# DebtAI

DebtAI ist eine lokal betriebene Anwendung zur Analyse und Konsolidierung von Schuldendokumenten. Version 1.0 verbindet Paperless-Import, KI-Extraktion, Forderungskonsolidierung, Dashboard, Quellen-Chat und CSV-Export.

## Funktionen in Version 1.0

- Docker-Compose-Setup fuer PostgreSQL, Backend, Frontend und optional Ollama
- PostgreSQL-17-Schema inklusive `documents`, `creditors`, `claims`, `claim_events` und `embeddings`
- pgvector-Aktivierung fuer spaetere semantische Suche
- Paperless-ngx-Import ueber die Paperless API
- vorbereiteter KI-Anschluss fuer OpenAI, Gemini und Claude
- KI-Extraktion fuer Forderungsdaten aus OCR-Texten
- Speicherung erkannter Glaeubiger, Forderungen und Forderungsereignisse
- Glaeubigeruebersicht und konsolidierte Forderungsbetraege
- Dashboard mit Kennzahlen und Statusverteilung
- Quellen-Chat ueber importierte Dokumente
- CSV-Export der Forderungen
- Dokumentenliste mit Suche und OCR-Detailansicht
- README mit lokaler Installation

## Voraussetzungen

- Docker Desktop oder Docker Engine mit Docker Compose
- Paperless API-Token oder Paperless Benutzername/Passwort

## Paperless-ngx installieren

Eine lokale Paperless-ngx-Installation mit Redis und PostgreSQL ist im Ordner
`paperless` vorbereitet. Paperless verwendet Port `8001`, weil das DebtAI-Backend
bereits Port `8000` belegt.

Paperless starten:

```powershell
cd paperless
docker compose up -d
```

Beim ersten Start einen Administrator anlegen:

```powershell
docker compose exec webserver createsuperuser
```

Danach Paperless unter http://localhost:8001 oeffnen. Dokumente koennen in den
Ordner `paperless/consume` kopiert werden; Paperless importiert sie automatisch.

Die Daten liegen in Docker-Volumes. Ein Export kann in Paperless erstellt und
im Ordner `paperless/export` abgelegt werden.

Paperless stoppen:

```powershell
docker compose down
```

Die Daten bleiben dabei erhalten. `docker compose down -v` loescht dagegen auch
die Paperless-Datenbank und Dokumente und sollte nur fuer einen bewussten
Komplettreset verwendet werden.

## Installation

1. Umgebungsdatei erstellen:

```bash
cp .env.example .env
```

2. `.env` anpassen:

```env
PAPERLESS_API_URL=http://dein-paperless-host:8000
PAPERLESS_API_TOKEN=dein_api_token
```

Fuer die mitgelieferte lokale Paperless-Installation lautet die Adresse aus
dem DebtAI-Container:

```env
PAPERLESS_API_URL=http://host.docker.internal:8001
PAPERLESS_API_TOKEN=dein_api_token
```

Alternativ kann statt `PAPERLESS_API_TOKEN` auch Benutzername und Passwort gesetzt werden:

```env
PAPERLESS_USERNAME=dein_benutzer
PAPERLESS_PASSWORD=dein_passwort
```

3. Anwendung starten:

```bash
docker compose up --build
```

4. DebtAI im Browser oeffnen:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs

## Arbeitsbereiche

Die Oberflaeche ist in vier Tabs aufgeteilt:

- `Dokumente`: Paperless-Import, Suche, OCR-Detailansicht und Forderungserkennung
- `Glaeubiger`: konsolidierte Glaeubiger mit Anzahl und Summe der Forderungen
- `Dashboard`: Kennzahlen, offene Betraege, betitelte Forderungen und Statusgruppen
- `Chat`: Fragen an die importierten Dokumente mit Quellenanzeige

Oben rechts kann ueber das Download-Symbol ein CSV-Export der Forderungen
geladen werden.

## Einstellungen in der Oberflaeche

In der DebtAI-Oberflaeche befindet sich oben rechts ein Zahnrad-Symbol. Darueber
oeffnet sich das Einstellungsmenue.

Das Menue zeigt:

- welcher KI-Anbieter aktiv ist
- ob OpenAI, Gemini oder Claude technisch verbunden sind
- wie viele Anbieter einsatzbereit sind

API-Schluessel werden aus Sicherheitsgruenden nicht im Browser angezeigt. Sie
liegen in der lokalen `.env`-Datei und werden vom Backend geladen.

## Paperless importieren

Im Frontend auf `Paperless importieren` klicken.

Alternativ per API:

```bash
curl -X POST http://localhost:8000/api/import/paperless \
  -H "Content-Type: application/json" \
  -d "{}"
```

Optional kann die Anzahl fuer einen Testlauf begrenzt werden:

```bash
curl -X POST http://localhost:8000/api/import/paperless \
  -H "Content-Type: application/json" \
  -d "{\"limit\": 25}"
```

## Forderung erkennen

Ein importiertes Dokument in der Dokumentenliste anklicken und im Detailfenster
`Forderung erkennen` auswaehlen. DebtAI sendet den OCR-Text an den konfigurierten
KI-Anbieter und speichert die erkannten Daten in den Tabellen `creditors`,
`claims` und `claim_events`.

Erkannt werden unter anderem:

- Glaeubiger
- Forderungsbetrag und Waehrung
- Aktenzeichen oder Vertragsreferenz
- Titelstatus
- Dokument- oder Ereignistyp
- relevantes Datum

Die KI-Extraktion benoetigt einen konfigurierten Anbieter in `.env`. Ohne
API-Schluessel bleibt DebtAI normal nutzbar, die Forderungserkennung meldet dann
aber, dass kein KI-Anbieter eingerichtet ist.

Alternativ per API:

```bash
curl -X POST http://localhost:8000/api/extractions/documents/1/claim \
  -H "Content-Type: application/json" \
  -d "{}"
```

## Quellen-Chat

Im Tab `Chat` kann eine Frage zu den importierten Dokumenten gestellt werden.
DebtAI sucht passende OCR-Texte, uebergibt kurze Quellen-Auschnitte an den
konfigurierten KI-Anbieter und zeigt Antwort plus Quellen an.

Der Chat benoetigt wie die Forderungserkennung einen konfigurierten KI-Anbieter.

Alternativ per API:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"Welche Forderungen sind offen?\"}"
```

## Export

Forderungen koennen als CSV exportiert werden:

```bash
curl http://localhost:8000/api/exports/claims.csv
```

## KI-Anbieter anschliessen

DebtAI kann technisch fuer OpenAI, Gemini oder Claude vorbereitet werden. Ohne
API-Schluessel startet die Anwendung weiterhin normal.

In `.env` einen Anbieter auswaehlen und den passenden Schluessel setzen:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=dein_openai_schluessel
OPENAI_MODEL=gpt-4.1-mini
```

Alternativ Gemini:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=dein_gemini_schluessel
GEMINI_MODEL=gemini-2.5-flash
```

Oder Claude:

```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=dein_anthropic_schluessel
ANTHROPIC_MODEL=claude-3-5-haiku-latest
```

Nach einer Aenderung der `.env` das Backend neu starten:

```bash
docker compose up -d --force-recreate backend
```

Status pruefen:

```bash
curl http://localhost:8000/api/ai/status
```

Technischer Test:

```bash
curl -X POST http://localhost:8000/api/ai/complete \
  -H "Content-Type: application/json" \
  -d "{\"messages\":[{\"role\":\"user\",\"content\":\"Antworte nur mit OK.\"}]}"
```

## Datenbank

Die Datenbank wird beim Start automatisch vorbereitet. Alembic legt das Schema an, `db/init.sql` aktiviert zusaetzlich die pgvector-Erweiterung.

Wichtige Tabellen:

- `documents`: importierte Paperless-Dokumente mit OCR-Text
- `creditors`: eindeutige Glaeubiger
- `creditor_aliases`: alternative Schreibweisen
- `claims`: Forderungen
- `claim_events`: Forderungshistorie
- `embeddings`: Textabschnitte und spaetere Vektor-Embeddings

## Ollama

Ollama ist fuer Version 0.1 noch nicht aktiv noetig. Der Container ist vorbereitet und kann bei Bedarf gestartet werden:

```bash
docker compose --profile ai up ollama
```

Das Standardmodell fuer spaetere Versionen ist Qwen3 14B.

## Entwicklung

Backend lokal starten:

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend lokal starten:

```bash
cd frontend
npm install
npm run dev
```

## Roadmap-Status

- Version 0.2: KI-Extraktion und Forderungserkennung umgesetzt
- Version 0.3: Konsolidierung und Glaeubigeruebersicht umgesetzt
- Version 0.4: Dashboard umgesetzt
- Version 0.5: KI-Chat mit Quellen umgesetzt
- Version 1.0: Exportfunktionen umgesetzt
