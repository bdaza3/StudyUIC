from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/issues", tags=["issues"])

@router.get("/")
async def get_issues():
    return []

