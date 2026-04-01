# DevOps AI Knowledge Base

Aplikacja webowa typu **RAG (Retrieval-Augmented Generation)**, ktora pozwala budowac wlasna baze wiedzy z plikow PDF i zadawac do niej pytania w jezyku naturalnym. Odpowiedzi generowane sa przez model OpenAI GPT-4o-mini na podstawie kontekstu wyszukanego semantycznie z bazy wektorowej ChromaDB.

Projekt zbudowany w podejsciu **DevOps-ready** -- konteneryzacja Docker, NGINX reverse proxy, healthcheck, CI/CD z GitHub Actions, deploy na GCP przez Terraform.

---

## Spis tresci

- [Funkcje aplikacji](#funkcje-aplikacji)
- [Architektura](#architektura)
- [Technologie](#technologie)
- [Struktura projektu](#struktura-projektu)
- [Wymagania](#wymagania)
- [Konfiguracja](#konfiguracja)
- [Uruchomienie](#uruchomienie)
- [Deploy na GCP (Terraform)](#deploy-na-gcp-terraform)
- [CI/CD](#cicd)
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
- Podzial tekstu na fragmenty (chunki) po 200 slow z 50-slowowym overlapem dla zachowania kontekstu na granicach
- Zapis chunkow do bazy wektorowej ChromaDB z metadanymi (nazwa pliku, hash zrodla)

### Deduplikacja dokumentow
- Kazdy wgrany dokument otrzymuje unikalny identyfikator (SHA-256 hash tresci, pierwsze 16 znakow)
- Przy ponownym wgraniu tego samego pliku system rozpoznaje duplikat i pomija go
- Zapobiega zasmiecaniu bazy wektorowej powtorzonymi danymi

### Zadawanie pytan (Q&A)
- Uzytkownik wpisuje pytanie w jezyku naturalnym (polski, angielski lub inny)
- System wyszukuje 5 najbardziej pasujacych fragmentow z bazy wektorowej
- Kontekst (do 8000 znakow) przekazywany jest do modelu GPT-4o-mini
- Model generuje odpowiedz na podstawie znalezionego kontekstu
- Odpowiedz zwracana jest w tym samym jezyku co pytanie

### OpenAI Embeddings
- Embeddingi generowane przez model `text-embedding-3-small` (OpenAI)
- Znacznie lepsza jakosc wyszukiwania dla tekstow w jezyku polskim niz domyslne embeddingi ChromaDB
- Ten sam klucz API sluzy do embeddingów i generowania odpowiedzi

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

### NGINX Reverse Proxy
- Jeden punkt wejscia na porcie 80
- Routing: `/` -> frontend, `/api/*` -> backend
- Limit uploadu: 50MB, timeout proxy: 300s
- Eliminuje problemy z CORS

### Frontend (chat UI)
- Interfejs czatowy w przegladarce -- ciemny motyw
- Upload plikow PDF z loaderem
- Pole do wpisywania pytan + przycisk "Ask"
- Historia rozmowy: pytania uzytkownika (zielone, po prawej) i odpowiedzi AI (niebieskie, po lewej)
- Dynamiczny `API_URL` -- automatycznie wykrywa srodowisko (dev vs Docker)

---

## Architektura

```
Uzytkownik (przegladarka)
        |
        | HTTP (port 80)
        v
NGINX (reverse proxy)
        |
        |--- /           -> frontend (HTML/CSS/JS)
        |--- /api/*      -> backend (FastAPI :8000)
                |
                |--- ChromaDB (baza wektorowa, dane na dysku ./chroma)
                |
                |--- OpenAI API
                        |--- text-embedding-3-small (embeddingi)
                        |--- GPT-4o-mini (generowanie odpowiedzi)
```

**Przeplyw danych przy uploazie PDF:**
```
PDF -> pypdf (ekstrakcja tekstu) -> chunk_text (200 slow, 50 overlap)
    -> OpenAI Embeddings (text-embedding-3-small)
    -> ChromaDB (zapis z metadanymi: source, source_id)
```

**Przeplyw danych przy pytaniu:**
```
Pytanie -> OpenAI Embeddings -> ChromaDB (wyszukiwanie semantyczne, top 5)
        -> kontekst (max 8000 znakow) -> GPT-4o-mini -> odpowiedz
```

---

## Technologie

| Komponent | Technologia | Opis |
|-----------|-------------|------|
| Backend | Python 3.14 + FastAPI | REST API z walidacja Pydantic |
| Serwer ASGI | Uvicorn | Serwer HTTP z hot-reload |
| Baza wektorowa | ChromaDB (PersistentClient) | Przechowywanie i wyszukiwanie embeddingów |
| Embeddingi | OpenAI text-embedding-3-small | Wektorowe reprezentacje tekstu |
| Model AI | OpenAI GPT-4o-mini | Generowanie odpowiedzi na podstawie kontekstu |
| Ekstrakcja PDF | pypdf | Wyciaganie tekstu z plikow PDF |
| Env config | python-dotenv | Ladowanie zmiennych z pliku .env |
| Frontend | HTML + CSS + JavaScript | Interfejs czatowy (vanilla JS, fetch API) |
| Reverse proxy | NGINX | Routing /api -> backend, / -> frontend |
| Konteneryzacja | Docker + Docker Compose | Budowanie i uruchamianie aplikacji |
| IaC | Terraform | Infrastruktura na GCP jako kod |
| CI/CD | GitHub Actions | Automatyczny opis PR generowany przez AI |
| Chmura | GCP Compute Engine | VM z Docker w europe-central2 |

---

## Struktura projektu

```
devops-ai-knowledge-base/
|-- app/
|   |-- main.py              # Endpointy FastAPI (upload, ask, health, documents)
|   |-- rag.py               # Logika RAG (chunking, embeddingi, ChromaDB, OpenAI)
|   |-- nginx/
|       |-- default.conf     # Konfiguracja NGINX (reverse proxy, timeouty)
|-- frontend/
|   |-- index.html           # Interfejs czatowy (upload PDF + Q&A)
|   |-- style.css            # Style CSS (ciemny motyw)
|-- terraform/
|   |-- main.tf              # VM, firewall rules (GCP)
|   |-- variables.tf         # Zmienne (project_id, region, klucz API)
|   |-- outputs.tf           # Output: IP i URL aplikacji
|   |-- startup.sh           # Skrypt startowy VM (Docker + clone + run)
|   |-- cloud-init.yaml      # Alternatywny cloud-init config
|-- .github/
|   |-- workflows/
|       |-- pr-description.yml  # AI-powered PR description
|-- data/
|   |-- uploads/             # Wgrane pliki PDF (gitignore)
|-- chroma/                  # Baza wektorowa ChromaDB (gitignore)
|-- Dockerfile               # Obraz Python 3.14-slim + curl
|-- docker-compose.yml       # Backend + NGINX + healthcheck
|-- requirements.txt         # Zaleznosci Python
|-- .env.example             # Szablon zmiennych srodowiskowych
|-- .env                     # Klucz API (gitignore, nie w repo)
|-- .gitignore               # Wykluczenia z repo
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

### Do deployu na GCP
- Konto GCP z wlaczonym billing
- Terraform CLI (v1.0+)
- gcloud CLI (zalogowany)
- Wlaczone Compute Engine API

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

Aplikacja dostepna na: `http://localhost` (port 80, przez NGINX)

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

## Deploy na GCP (Terraform)

### Krok 1 -- Wlacz Compute Engine API

```bash
gcloud services enable compute.googleapis.com --project=TWOJE_PROJECT_ID
```

### Krok 2 -- Skonfiguruj zmienne

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edytuj `terraform.tfvars`:
```hcl
project_id = "twoje-project-id"
region     = "europe-central2"
zone       = "europe-central2-a"
```

### Krok 3 -- Deploy

```bash
terraform init
terraform plan -var="openai_api_key=sk-proj-twoj-klucz"
terraform apply -var="openai_api_key=sk-proj-twoj-klucz"
```

Terraform utworzy:
- Reguly firewall (HTTP port 80, SSH port 22)
- VM `e2-small` z Ubuntu 22.04
- Startup script ktory instaluje Docker, klonuje repo i uruchamia `docker-compose`

Po ~5 minutach aplikacja bedzie dostepna pod adresem IP wyswietlonym w output.

### Krok 4 -- Usuwanie infrastruktury

```bash
terraform destroy -var="openai_api_key=dummy"
```

---

## CI/CD

### AI PR Description (GitHub Actions)

Workflow `.github/workflows/pr-description.yml` automatycznie generuje opis PR:

1. Trigger: otwarcie nowego PR
2. Pobiera diff zmian
3. Wysyla diff do OpenAI GPT-4o-mini
4. Aktualizuje body PR z wygenerowanym opisem po polsku

**Wymagany secret:** `OPENAI_API_KEY` w Settings -> Secrets and variables -> Actions

---

## API -- endpointy

### GET /health

Sprawdzenie stanu aplikacji.

```bash
curl http://localhost/api/health
```

Odpowiedz:
```json
{"status": "ok"}
```

---

### POST /upload_pdfs

Upload jednego lub wielu plikow PDF do bazy wiedzy.

```bash
curl -X POST http://localhost/api/upload_pdfs \
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
curl -X POST http://localhost/api/ask \
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
curl http://localhost/api/documents
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
5. **Embeddingi** -- OpenAI `text-embedding-3-small` tworzy wektorowe reprezentacje kazdego chunku. Model ten dobrze obsluguje teksty polskie
6. **Zapis** -- chunki + embeddingi + metadane (nazwa pliku, source_id) zapisywane sa w bazie wektorowej na dysku (`./chroma`)
7. **Pytanie** -- uzytkownik zadaje pytanie w jezyku naturalnym
8. **Wyszukiwanie semantyczne** -- ChromaDB porownuje embedding pytania z embeddingami chunkow i zwraca 5 najbardziej pasujacych
9. **Generowanie odpowiedzi** -- kontekst (max 8000 znakow) + pytanie wysylane sa do GPT-4o-mini, ktory generuje odpowiedz

---

## Kluczowe elementy kodu

### app/rag.py -- logika RAG

```python
# OpenAI Embeddings -- lepsza jakosc wyszukiwania niz domyslne ChromaDB
class OpenAIEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=input
        )
        return [item.embedding for item in response.data]

# PersistentClient zapisuje dane na dysku -- przetrwaja restart kontenera
chroma_client = chromadb.PersistentClient(path="./chroma")
collection = chroma_client.get_or_create_collection(
    name="knowledge_openai",
    embedding_function=OpenAIEmbeddingFunction()
)
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
    # ChromaDB zwraca 5 najbardziej pasujacych fragmentow
    results = collection.query(query_texts=[question], n_results=5)
    context = "\n\n---\n\n".join(documents[0])[:8000]

    # GPT-4o-mini generuje odpowiedz na podstawie kontekstu
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a knowledge base assistant..."},
            {"role": "user", "content": f"Context:\n\n{context}\n\nQuestion: {question}"}
        ]
    )
```

### app/main.py -- endpointy FastAPI

```python
# Metadane API widoczne w Swagger UI (/docs)
app = FastAPI(
    title="DevOps AI Knowledge Base",
    description="RAG-based knowledge base API with PDF support",
    version="1.0.0"
)

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

### app/nginx/default.conf -- reverse proxy

```nginx
server {
    listen 80;
    client_max_body_size 50M;          # limit uploadu PDF

    location / {
        root /usr/share/nginx/html;     # serwuje frontend
    }

    location /api/ {
        proxy_pass http://backend:8000/; # proxy do FastAPI
        proxy_read_timeout 300s;         # timeout na odpowiedz (embeddingi duzych PDF)
        proxy_send_timeout 300s;
    }
}
```

### terraform/main.tf -- infrastruktura GCP

```hcl
# VM z Ubuntu 22.04 i publicznym IP
resource "google_compute_instance" "ai_kb" {
    name         = "ai-kb-server"
    machine_type = "e2-small"            # 2 vCPU, 2GB RAM
    zone         = "europe-central2-a"   # Warszawa

    boot_disk {
        initialize_params {
            image = "ubuntu-2204-lts"
            size  = 30                   # 30 GB na Docker, ChromaDB, PDF
        }
    }

    # Startup script instaluje Docker, klonuje repo, uruchamia docker-compose
    metadata_startup_script = templatefile("startup.sh", {
        openai_api_key = var.openai_api_key
    })
}
```

### docker-compose.yml

```yaml
services:
  backend:
    build: .
    expose: ["8000"]                     # tylko wewnetrznie (NGINX proxy)
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      start_period: 10s                  # daj backendowi czas na start

  nginx:
    image: nginx:alpine
    ports: ["80:80"]                     # jedyny publiczny port
    volumes:
      - ./app/nginx/default.conf:/etc/nginx/conf.d/default.conf
      - ./frontend:/usr/share/nginx/html
    depends_on: [backend]
```

---

## Ograniczenia

- Brak autoryzacji uzytkownikow -- kazdy moze wgrac PDF i zadawac pytania
- Prosty frontend (vanilla HTML/JS) bez frameworka
- Dane przechowywane lokalnie (ChromaDB na dysku VM)
- Brak HTTPS (wymaga certyfikatu SSL/TLS)
- VM na GCP nie ma auto-scalingu

---

## Roadmap

- [x] NGINX jako reverse proxy
- [x] OpenAI Embeddings (`text-embedding-3-small`)
- [x] CI/CD -- AI-powered PR description (GitHub Actions)
- [x] Deploy do chmury (GCP Compute Engine + Terraform)
- [ ] HTTPS (Let's Encrypt / Cloud Load Balancer)
- [ ] CI pipeline (lint, testy, build Docker image)
- [ ] Multi-stage Dockerfile (mniejszy obraz produkcyjny)
- [ ] Lepszy frontend (React / Next.js)
- [ ] Usuwanie dokumentow z bazy
- [ ] Podglad chunkow w bazie wektorowej
- [ ] Streaming odpowiedzi (SSE/WebSocket)
- [ ] Testy jednostkowe (pytest)
- [ ] Logowanie (logging zamiast print)
- [ ] Auto-deploy z GitHub Actions na GCP
