import hashlib
import os

import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from dotenv import load_dotenv
from openai import OpenAI, APIConnectionError, RateLimitError, APIStatusError
from pypdf import PdfReader

load_dotenv(override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class OpenAIEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=input
        )
        return [item.embedding for item in response.data]


chroma_client = chromadb.PersistentClient(path="./chroma")
embedding_fn = OpenAIEmbeddingFunction()
collection = chroma_client.get_or_create_collection(
    name="knowledge_openai",
    embedding_function=embedding_fn
)


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


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


def ask_knowledge(question: str):
    results = collection.query(
        query_texts=[question],
        n_results=5
    )

    documents = results.get("documents", [])

    if not documents or not documents[0]:
        return "Brak danych w bazie"

    context = "\n\n---\n\n".join(documents[0])
    context = context[:8000]
    print(f"QUERY: {question} | CONTEXT LENGTH: {len(context)} chars")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a knowledge base assistant. Answer the user's question using the provided context. The context comes from documents uploaded by the user. Synthesize information from the context to give a useful answer, even if the context only partially covers the topic. Only reply 'Nie znaleziono informacji w bazie wiedzy.' if the context has absolutely nothing to do with the question. Answer in the same language as the question."
                },
                {
                    "role": "user",
                    "content": f"Context:\n\n{context}\n\nQuestion: {question}"
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


def load_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text
