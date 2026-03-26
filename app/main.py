from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import List
import os
import shutil
from app.rag import add_to_knowledge, ask_knowledge, load_pdf


class AskRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("question must not be empty")
        return v.strip()

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}

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
                added = add_to_knowledge(text, source=file.filename)
                if added:
                    added_files.append(file.filename)
                else:
                    print(f"PDF {file.filename} already in knowledge base")
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

@app.post("/ask")
def ask_question(data: AskRequest):
    try:
        answer = ask_knowledge(data.question)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")
    return {"answer": answer}