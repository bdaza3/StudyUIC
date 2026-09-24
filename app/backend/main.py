import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.backend.routes.concierge import router as concierge_router
from app.backend.routes.issues import router as issues_router
from app.backend.routes.rag import router as rag_router

load_dotenv()

app = FastAPI()

# Configure the deployed frontend explicitly in CORS_ALLOWED_ORIGINS; do not use
# a wildcard because this API uses privileged server-side credentials.
allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(issues_router)
app.include_router(concierge_router)
app.include_router(rag_router)

#testing
@app.get("/health")

def health_check():
    return {"status": "ok", "service": "study-uic-api"}
