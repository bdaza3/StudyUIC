from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/issues", tags=["issues"])
issues: dict[UUID, dict] = {}


class IssueCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=2000)
    category: str = Field(min_length=1, max_length=80)


class IssueUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    status: str | None = Field(default=None, pattern="^(open|in_review|resolved)$")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_issue(issue: IssueCreate):
    issue_id = uuid4()
    record = {"id": str(issue_id), **issue.model_dump(), "status": "open"}
    issues[issue_id] = record
    return record


@router.get("/")
async def get_issues():
    return list(issues.values())


@router.get("/{issue_id}")
async def get_issue(issue_id: UUID):
    issue = issues.get(issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.patch("/{issue_id}")
async def update_issue(issue_id: UUID, update: IssueUpdate):
    issue = issues.get(issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    issue.update(update.model_dump(exclude_none=True))
    return issue

