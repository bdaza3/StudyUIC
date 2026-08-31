from fastapi import FastAPI
from app.backend.routes.issues import router as issues_router

app = FastAPI()

app.include_router(issues_router)

#testing
@app.get("/health")

def health_check():
    return {"status": "ok"}
#testing
