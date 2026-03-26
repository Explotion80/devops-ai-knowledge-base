# DevOps AI Knowledge Base

Aplikacja webowa typu **RAG (Retrieval-Augmented Generation)**, ktora pozwala budowac wlasna baze wiedzy z plikow PDF i zadawac do niej pytania w jezyku naturalnym. Odpowiedzi generowane sa przez model OpenAI GPT-4o-mini na podstawie kontekstu wyszukanego semantycznie z bazy wektorowej ChromaDB.

Projekt zbudowany w podejsciu **DevOps-ready** -- konteneryzacja Docker, healthcheck, konfiguracja przez zmienne srodowiskowe, przygotowany pod CI/CD i reverse proxy.

---

## Spis tresci

- [Funkcje aplikacji](#funkcje-aplikacji)
- [Architektura](#architektura)
- [Technologie](#technologie)
- [Struktura projektu](#struktura-projektu)
- [Wymagania](#wymagania)
- [Konfiguracja](#konfiguracja)
- [Uruchomienie](#uruchomienie)
- [API -- endpointy](#api----endpointy)
- [Jak dziala RAG](#jak-dziala-rag)
- [Kluczowe elementy kodu](#kluczowe-elementy-kodu)
- [Ograniczenia](#ograniczenia)
- [Roadmap](#roadmap)

---

## Funkcje aplikacji

### Upload i przetwarzanie PDF
- Upload jednego lub wielu plikow PDF jednoczesnie przez frontend lub API
- Automatyczna ekstrakcja tekstu z kazdej strony PDF (biblioteka `pypdf`)
- Podział tekstu na fragmenty (chunki) po 200 slow z 50-slowowym overlapem dla zachowania kontekstu na granicach
- Zapis chunkow do bazy wektorowej ChromaDB z metadanymi (nazwa pliku, hash zrodla)

### Deduplikacja dokumentow
- Kazdy wgrany dokument otrzymuje unikalny identyfikator (SHA-256 hash tresci, pierwsze 16 znakow)
- Przy ponownym wgraniu tego samego pliku system rozpoznaje duplikat i pomija go
- Zapobiega zasmiecaniu bazy wektorowej powtorzonymi danymi

### Zadawanie pytan (Q&A)
- Uzytkownik wpisuje pytanie w jezyku naturalnym (polski, angielski lub inny)
- System wyszukuje 3 najbardziej pasujace fragmenty z bazy wektorowej
- Kontekst (do 4000 znakow) przekazywany jest do modelu GPT-4o-mini
- Model generuje odpowiedz wylacznie na podstawie znalezionego kontekstu
- Odpowiedz zwracana jest w tym samym jezyku co pytanie

### Walidacja danych wejsciowych
- Model Pydantic `AskRequest` z walidatorem -- pytanie nie moze byc puste
- Przy pustym lub brakujacym pytaniu zwracany jest blad HTTP 422 z czytelnym komunikatem

### Obsluga bledow OpenAI API
- `APIConnectionError` -- brak polaczenia z API
- `RateLimitError` -- przekroczony limit requestow
- `APIStatusError` -- nieprawidlowy klucz, blad serwera itp.
- Kazdy blad zwraca HTTP 502 z opisem problemu

### Healthcheck
- Endpoint `GET /health` zwraca `{"status": "ok"}`
- Docker healthcheck odpytuje ten endpoint co 30 sekund
- Pozwala monitorowac stan aplikacji w docker-compose (`docker-compose ps`)

### Lista dokumentow
- Endpoint `GET /documents` zwraca liste wszystkich wgranych plikow PDF

### Frontend (chat UI)
- Interfejs czatowy w przegladarce -- ciemny motyw
- Upload plikow PDF z loaderem
- Pole do wpisywania pytan + przycisk "Ask"
- Historia rozmowy: pytania uzytkownika (zielone, po prawej) i odpowiedzi AI (niebieskie, po lewej)

---

## Architektura

```
Frontend (HTML + JS + CSS)        port 3000
        |
        | fetch (HTTP)
        v
Backend (FastAPI + Uvicorn)       port 8000
        |
        |--- ChromaDB (baza wektorowa, dane na dysku ./chroma)
        |
        |--- OpenAI API (GPT-4o-mini -- generowanie odpowiedzi)
```

**Przeplyw danych przy uploazie PDF:**
```
PDF --> pypdf (ekstrakcja tekstu) --> chunk_text (podzial na fragmenty)
    --> ChromaDB (embeddingi + zapis) --> metadane (source, source_id)
```

**Przeplyw danych przy pytaniu:**
```
Pytanie --> ChromaDB (wyszukiwanie semantyczne, top 3 wyniki)
        --> kontekst (max 4000 znakow) --> GPT-4o-mini --> odpowiedz
```

---

## Technologie

| Komponent | Technologia | Opis |
|-----------|-------------|------|
| Backend | Python 3.14 + FastAPI | REST API z walidacja Pydantic |
| Serwer ASGI | Uvicorn | Serwer HTTP z hot-reload |
| Baza wektorowa | ChromaDB (PersistentClient) | Przechowywanie i wyszukiwanie embeddingów |
| Model AI | OpenAI GPT-4o-mini | Generowanie odpowiedzi na podstawie kontekstu |
| Ekstrakcja PDF | pypdf | Wyciaganie tekstu z plikow PDF |
| Env config | python-dotenv | Ladowanie zmiennych z pliku .env |
| Frontend | HTML + CSS + JavaScript | Interfejs czatowy (vanilla JS, fetch API) |
| Konteneryzacja | Docker + Docker Compose | Budowanie i uruchamianie aplikacji |
| Reverse proxy | NGINX (przygotowana konfiguracja) | Routing /api -> backend, / -> frontend |

---

## Struktura projektu

```
devops-ai-knowledge-base/
|-- app/
|   |-- main.py              # Endpointy FastAPI (upload, ask, health, documents)
|   |-- rag.py               # Logika RAG (chunking, ChromaDB, OpenAI)
|   |-- nginx/
|       |-- default.conf     # Konfiguracja NGINX (reverse proxy)
|-- frontend/
|   |-- index.html           # Interfejs czatowy (upload PDF + Q&A)
|   |-- style.css            # Style CSS (ciemny motyw)
|-- data/
|   |-- uploads/             # Wgrane pliki PDF (gitignore)
|-- chroma/                  # Baza wektorowa ChromaDB (gitignore)
|-- Dockerfile               # Obraz Python 3.14-slim + curl
|-- docker-compose.yml       # Serwis backend + healthcheck
|-- requirements.txt         # Zaleznosci Python
|-- .env.example             # Szablon zmiennych srodowiskowych
|-- .env                     # Klucz API (gitignore, nie w repo)
|-- .gitignore               # Wykluczenia z repo
|-- knowledge.txt            # Przykladowe dane tekstowe
|-- README.md                # Ten plik
```

---

## Wymagania

### Do uruchomienia z Docker (zalecane)
- Docker Desktop (Windows/Mac) lub Docker Engine (Linux)
- Docker Compose v2+
- Klucz API OpenAI (https://platform.openai.com/api-keys)

### Do uruchomienia lokalnie (bez Dockera)
- Python 3.10+
- pip
- Klucz API OpenAI

---

## Konfiguracja

### 1. Sklonuj repozytorium

```bash
git clone https://github.com/Explotion80/devops-ai-knowledge-base.git
cd devops-ai-knowledge-base
```

### 2. Utworz plik .env

```bash
cp .env.example .env
```

Edytuj `.env` i wklej swoj klucz OpenAI:

```env
OPENAI_API_KEY=sk-proj-twoj-klucz-api
```

Klucz mozesz wygenerowac na: https://platform.openai.com/api-keys

---

## Uruchomienie

### Opcja A: Docker Compose (zalecane)

```bash
docker-compose up --build
```

Backend dostepny na: `http://localhost:8000`

Sprawdzenie statusu:

```bash
docker-compose ps
# backend powinien miec status "healthy"
```

### Opcja B: Lokalnie (bez Dockera)

```bash
# Zainstaluj zaleznosci
pip install -r requirements.txt

# Uruchom backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# W osobnym terminalu -- uruchom frontend
cd frontend
python -m http.server 3000
```

Backend: `http://localhost:8000`
Frontend: `http://localhost:3000`
Dokumentacja API (Swagger): `http://localhost:8000/docs`

---

## API -- endpointy

### GET /health

Sprawdzenie stanu aplikacji.

```bash
curl http://localhost:8000/health
```

Odpowiedz:
```json
{"status": "ok"}
```

---

### POST /upload_pdfs

Upload jednego lub wielu plikow PDF do bazy wiedzy.

```bash
curl -X POST http://localhost:8000/upload_pdfs \
  -F "files=@dokument.pdf" \
  -F "files=@drugi_dokument.pdf"
```

Odpowiedz (sukces):
```json
{
  "added": ["dokument.pdf", "drugi_dokument.pdf"],
  "count": 2
}
```

Odpowiedz (duplikat -- plik juz w bazie):
```json
{
  "added": [],
  "count": 0
}
```

---

### POST /ask

Zadanie pytania do bazy wiedzy. Wymaga JSON body z polem `question`.

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Co to jest Kubernetes?"}'
```

Odpowiedz (sukces):
```json
{
  "answer": "Kubernetes to platforma do orkiestracji kontenerow..."
}
```

Odpowiedz (puste pytanie -- HTTP 422):
```json
{
  "detail": [
    {
      "msg": "Value error, question must not be empty",
      "type": "value_error"
    }
  ]
}
```

Odpowiedz (blad OpenAI -- HTTP 502):
```json
{
  "detail": "AI service error: Cannot connect to OpenAI API"
}
```

---

### GET /documents

Lista wgranych plikow PDF.

```bash
curl http://localhost:8000/documents
```

Odpowiedz:
```json
{
  "files": ["dokument.pdf", "raport.pdf"]
}
```

---

## Jak dziala RAG

**RAG (Retrieval-Augmented Generation)** to technika laczaca wyszukiwanie informacji z generowaniem tekstu przez model AI.

### Krok po kroku:

1. **Upload PDF** -- uzytkownik wgrywa plik PDF
2. **Ekstrakcja tekstu** -- `pypdf` wyciaga tekst z kazdej strony
3. **Chunking** -- tekst dzielony jest na fragmenty po 200 slow z 50-slowowym overlapem (nakladaniem sie). Overlap zapewnia, ze kontekst na granicach chunkow nie jest tracony
4. **Deduplikacja** -- hash SHA-256 tresci sluzy jako identyfikator. Jesli taki sam dokument juz istnieje w bazie, upload jest pomijany
5. **Embeddingi** -- ChromaDB tworzy wektorowe reprezentacje kazdego chunku (domyslny model sentence-transformers)
6. **Zapis** -- chunki + embeddingi + metadane (nazwa pliku, source_id) zapisywane sa w bazie wektorowej na dysku (`./chroma`)
7. **Pytanie** -- uzytkownik zadaje pytanie w jezyku naturalnym
8. **Wyszukiwanie semantyczne** -- ChromaDB porownuje embedding pytania z embeddingami chunkow i zwraca 3 najbardziej pasujace
9. **Generowanie odpowiedzi** -- kontekst (max 4000 znakow) + pytanie wysylane sa do GPT-4o-mini, ktory generuje odpowiedz

---

## Kluczowe elementy kodu

### app/rag.py -- logika RAG

```python
# Ladowanie klucza API z pliku .env (override=True nadpisuje zmienne srodowiskowe)
load_dotenv(override=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# PersistentClient zapisuje dane na dysku -- przetrwaja restart kontenera
chroma_client = chromadb.PersistentClient(path="./chroma")
collection = chroma_client.get_or_create_collection(name="knowledge")
```

**Deduplikacja dokumentow:**
```python
def add_to_knowledge(text, source="manual"):
    source_id = _text_hash(text)  # SHA-256, pierwsze 16 znakow
    existing = collection.get(where={"source_id": source_id})
    if existing and existing["ids"]:
        return False  # dokument juz istnieje
    # ... dodaj chunki do bazy
```

**Chunking z overlapem:**
```python
def chunk_text(text, chunk_size=200, overlap=50):
    # step = 150 (200 - 50), wiec kazdy chunk zaczyna sie 150 slow po poprzednim
    # ale zawiera 50 slow z konca poprzedniego chunku
    step = max(chunk_size - overlap, 1)
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size])
```

**Wyszukiwanie + generowanie odpowiedzi:**
```python
def ask_knowledge(question):
    # ChromaDB zwraca 3 najbardziej pasujace fragmenty
    results = collection.query(query_texts=[question], n_results=3)
    context = "\n\n---\n\n".join(documents[0])[:4000]

    # GPT-4o-mini generuje odpowiedz na podstawie kontekstu
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful knowledge base assistant..."},
            {"role": "user", "content": f"Context:\n\n{context}\n\nQuestion: {question}"}
        ]
    )
```

### app/main.py -- endpointy FastAPI

```python
# Walidacja danych wejsciowych -- Pydantic model
class AskRequest(BaseModel):
    question: str

    @field_validator("question")
    def question_not_empty(cls, v):
        if not v.strip():
            raise ValueError("question must not be empty")
        return v.strip()

# Obsluga bledow OpenAI -- HTTP 502 zamiast 500
@app.post("/ask")
def ask_question(data: AskRequest):
    try:
        answer = ask_knowledge(data.question)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")
```

### Dockerfile

```dockerfile
FROM python:3.14-slim
# curl potrzebny do healthchecka w docker-compose
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
```

### docker-compose.yml

```yaml
# Healthcheck -- Docker sprawdza czy backend zyje co 30 sekund
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 10s  # daj backendowi 10s na start zanim zaczniesz sprawdzac
```

---

## Ograniczenia

- Brak autoryzacji uzytkownikow -- kazdy moze wgrac PDF i zadawac pytania
- Prosty frontend (vanilla HTML/JS) bez frameworka
- NGINX reverse proxy przygotowany, ale nie podlaczony w docker-compose
- Brak deploymentu do chmury
- Dane przechowywane lokalnie (ChromaDB na dysku)
- Embeddingi ChromaDB (sentence-transformers) -- ograniczona jakosc dla tekstow polskich
- Frontend `API_URL` ustawiony na `localhost:8000` -- wymaga zmiany przy deploymencie

---

## Roadmap

- [ ] NGINX jako reverse proxy + routing `/api` -> backend, `/` -> frontend
- [ ] CI/CD pipeline (GitHub Actions -- lint, testy, budowanie obrazu)
- [ ] Multi-stage Dockerfile (mniejszy obraz produkcyjny)
- [ ] Deployment do chmury (GCP / Azure + Terraform)
- [ ] Lepszy frontend (React / Next.js)
- [ ] OpenAI Embeddings (`text-embedding-3-small`) zamiast domyslnych ChromaDB
- [ ] Usuwanie dokumentow z bazy
- [ ] Podglad chunkow w bazie wektorowej
- [ ] Streaming odpowiedzi (SSE/WebSocket)
- [ ] Testy jednostkowe (pytest)
- [ ] Logowanie (logging zamiast print)
