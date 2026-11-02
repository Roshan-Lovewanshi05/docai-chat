from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth,document,chat


from .rag.clients import ensure_collection


from contextlib import asynccontextmanager

@asynccontextmanager
async def create_vectordb(app: FastAPI):
    try:
        await ensure_collection()
        print("SUCCESS: Qdrant collection and user_id index are ready.")

    except Exception as error:
        print("ERROR: Qdrant initialization failed:", repr(error))
        raise

    yield 



app = FastAPI(lifespan=create_vectordb)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","doc-ai-frontend-gj6j.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth.router)
app.include_router(document.router)
app.include_router(chat.router)

@app.get("/health")
def health():
    return {"status":"okk"}