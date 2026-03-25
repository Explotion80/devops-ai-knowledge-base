# DevOps AI Knowledge Base

Prosta, ale rozwojowa aplikacja typu **RAG (Retrieval-Augmented Generation)**, która pozwala tworzyć własną bazę wiedzy i zadawać do niej pytania przy użyciu AI.

Projekt został zbudowany jako **praktyczny projekt DevOps + AI** — działa w Dockerze i jest gotowy do dalszego rozwoju (CI/CD, cloud, reverse proxy).

---

# 🚀 Co potrafi aplikacja?
✅ Wrzucanie plików **PDF** i analiza ich zawartości
✅ Zadawanie pytań do zapisanych danych
✅ Odpowiedzi generowane przez AI na podstawie kontekstu
✅ Wyszukiwanie semantyczne (embeddingi)

---

#  Jak to działa?
1. Dodajesz plik PDF
2. Dane są dzielone na fragmenty
3. Tworzone są embeddingi (OpenAI)
4. Dane trafiają do bazy wektorowej (ChromaDB)
5. Przy pytaniu:

   * wyszukiwany jest najbardziej pasujący kontekst
   * AI generuje odpowiedź

To podejście to RAG (Retrieval-Augmented Generation)

---

# 🧱 Architektura

```text
Frontend (HTML + JS)
        ↓
Backend (FastAPI)
        ↓
ChromaDB (vector database)
        ↓
OpenAI API (LLM + embeddings)
```

---

# Technologie

* Python + FastAPI – backend API
* HTML + JS (fetch) – frontend
* OpenAI API – model językowy + embeddingi
* ChromaDB – baza wektorowa
* Docker / Docker Compose – uruchamianie aplikacji

---

# Konfiguracja

## 1. Utwórz plik `.env`

```env
OPENAI_API_KEY=twój_klucz_api
```

---

## 2. Dodaj `.gitignore`

```text
.env
__pycache__/
*.pyc
```

---

# Uruchomienie

## 1. Zbuduj i uruchom aplikację

```bash
docker-compose up --build
```

---

## 2. Otwórz aplikację

Frontend:

```
http://localhost:3000
```

Backend:

```
http://localhost:8000
```

---

# 🔌 API

## ➕ Dodanie danych

POST /ingest

```json
{
  "content": "Twój tekst"
}
```

---

## Zadanie pytania

**POST /ask

```json
{
  "question": "Twoje pytanie"
}
```

---

# Obsługa PDF

Możesz wrzucić własny plik PDF, a aplikacja:

* wyciąga z niego tekst
* dzieli go na fragmenty
* tworzy embeddingi
* zapisuje w bazie

Następnie możesz zadawać pytania dotyczące zawartości PDF

---

#  Ograniczenia (na teraz)

* brak autoryzacji użytkowników
* prosty frontend (bez frameworka)
* brak NGINX (reverse proxy)
* brak deploymentu do chmury
* dane przechowywane lokalnie

---

#  Roadmap (co dalej?)

* [ ] NGINX + routing `/api`
* [ ] deployment (GCP / Azure + Terraform)
* [ ] CI/CD (GitHub Actions)
* [ ] lepszy frontend (React / Next.js)
* [ ] baza PostgreSQL

---

# 💡 Cel projektu

Projekt pokazuje w praktyce:

* integrację AI z aplikacją webową
* wykorzystanie RAG
* podstawy architektury backend + AI
* podejście DevOps (Docker, struktura projektu)
