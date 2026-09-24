from fastapi import FastAPI
from app.backend.routes.concierge import router as concierge_router
from app.backend.routes.issues import router as issues_router
from app.backend.routes.rag import router as rag_router

app = FastAPI()

app.include_router(issues_router)
app.include_router(concierge_router)
app.include_router(rag_router)

#testing
@app.get("/health")

def health_check():
    return {"status": "ok", "service": "study-uic-api"}
