DevOps AI Knowledge Base

Aplikacja webowa typu AI Knowledge Base (RAG – Retrieval-Augmented Generation), która pozwala:

dodawać własne dane (teksty, notatki, pliki PDF)
zadawać pytania do tych danych
otrzymywać odpowiedzi generowane przez model AI na podstawie zapisanej wiedzy

Projekt jest przygotowany w stylu DevOps-ready – działa w Dockerze i może być łatwo rozwijany o CI/CD, chmurę czy reverse proxy (np. NGINX w przyszłości).

Funkcjonalności:
Ingest danych – dodawanie tekstu do bazy wiedzy
Obsługa PDF – możliwość wrzucenia własnego pliku PDF, który:
- jest przetwarzany na tekst
- dzielony na fragmenty
- zamieniany na embeddingi
- zapisywany w bazie wektorowej
- Zadawanie pytań (Q&A) – AI odpowiada na podstawie zapisanych danych (również z PDF)
RAG (Retrieval-Augmented Generation):
- embeddingi
- wyszukiwanie kontekstowe
- odpowiedzi generowane przez model OpenAI
Dockerized – całość działa w kontenerach

 Jak to działa (RAG)
Dodajesz tekst lub plik PDF
Tekst jest dzielony na fragmenty
Tworzone są embeddingi (OpenAI)
Dane trafiają do ChromaDB
Przy pytaniu:
wyszukiwany jest najbardziej pasujący kontekst (również z PDF)
AI generuje odpowiedź na podstawie tych danych

 Przykład użycia
Wrzucasz PDF (np. dokumentację lub artykuł)
Zadajesz pytanie:
{
  "question": "O czym jest ten dokument?"
}
Odpowiedź:
AI analizuje treść PDF i zwraca odpowiedź na podstawie jego zawartości

Zastosowania
analiza dokumentów (PDF)
chatboty firmowe
baza wiedzy dla zespołu
automatyczne odpowiadanie na pytania z dokumentacji