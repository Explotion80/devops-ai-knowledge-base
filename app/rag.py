import hashlib

import chromadb
from openai import OpenAI, APIConnectionError, RateLimitError, APIStatusError
from pypdf import PdfReader

import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

chroma_client = chromadb.PersistentClient(path="./chroma")
collection = chroma_client.get_or_create_collection(name="knowledge")

def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


# 🔹 dodanie tekstu do bazy
def add_to_knowledge(text: str, source: str = "manual"):
    source_id = _text_hash(text)
    existing = collection.get(where={"source_id": source_id})
    if existing and existing["ids"]:
        print(f"SKIP duplicate (source_id={source_id})")
        return False

    chunks = chunk_text(text)
    print("ADDING TO DB:", len(chunks))
    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk],
            ids=[f"{source_id}_{i}"],
            metadatas=[{"source": source, "source_id": source_id}]
        )
    return True

# 🔹 pytanie do bazy + LLM
def ask_knowledge(question: str):
    results = collection.query(
        query_texts=[question],
        n_results=3
    )

    documents = results.get("documents", [])
    # distances = results.get("distances", [])

    if not documents or not documents[0]:
        return "Brak danych w bazie"

    context = " ".join(documents[0])

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Odpowiadaj WYŁĄCZNIE na podstawie kontekstu. "
                        "Jeśli nie jesteś pewien, napisz: 'Nie ma tego w bazie wiedzy'."
                    )
                },
                {
                    "role": "user",
                    "content": f"Kontekst:\n{context}\n\nPytanie:\n{question}"
                }
            ]
        )
    except APIConnectionError:
        raise RuntimeError("Cannot connect to OpenAI API")
    except RateLimitError:
        raise RuntimeError("OpenAI API rate limit exceeded, try again later")
    except APIStatusError as e:
        raise RuntimeError(f"OpenAI API error: {e.status_code} {e.message}")

    return response.choices[0].message.content

# 🔹 dzielenie tekstu na chunki
def chunk_text(text: str, chunk_size=200, overlap=50):
    words = text.split()
    chunks = []
    step = max(chunk_size - overlap, 1)
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        if i + chunk_size >= len(words):
            break
    return chunks

# 🔹 wczytywanie PDF
def load_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text