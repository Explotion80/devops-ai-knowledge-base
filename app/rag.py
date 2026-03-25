import chromadb
from openai import OpenAI
from pypdf import PdfReader

import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

chroma_client = chromadb.Client(
    settings=chromadb.config.Settings(
        persist_directory="./chroma"
    )
)
collection = chroma_client.get_or_create_collection(name="knowledge")

# 🔹 dodanie tekstu do bazy
def add_to_knowledge(text: str):
    chunks = chunk_text(text)
    print("ADDING TO DB:", len(chunks))
    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk],
            ids=[f"{hash(chunk)}_{i}"]
        )

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

    return response.choices[0].message.content

# 🔹 dzielenie tekstu na chunki
def chunk_text(text: str, chunk_size=200):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

# 🔹 wczytywanie PDF
def load_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text