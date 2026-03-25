from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import shutil
from app.rag import add_to_knowledge, ask_knowledge, load_pdf

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# UPLOAD PDF
@app.post("/upload_pdfs")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    added_files = []

    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Wczytanie PDF
            text = load_pdf(file_path)
            print(f"PDF {file.filename} length:", len(text))

            if text.strip():  # jeśli jest tekst
                add_to_knowledge(text)
                added_files.append(file.filename)
            else:
                print(f"PDF {file.filename} zawiera pusty tekst!")

        except Exception as e:
            return {"error": str(e)}

    return {
        "added": added_files,
        "count": len(added_files)
    }

# 🔹 LISTA PLIKÓW
@app.get("/documents")
def list_documents():
    try:
        files = os.listdir(UPLOAD_DIR)
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}

# 🔹 ASK
@app.post("/ask")
def ask_question(data: dict):
    question = data.get("question")
    answer = ask_knowledge(question)
    return {"answer": answer}