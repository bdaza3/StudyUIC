"""RAG search and grounded course-answer endpoints."""

import re
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.backend.services.llm import OpenRouterClient
from app.backend.services.rag_retrieval import RagRetriever, RetrievalQuery, RetrievalResult


router = APIRouter(prefix="/api/v1/rag", tags=["rag"])
logger = logging.getLogger(__name__)


class RagSearchRequest(RetrievalQuery):
    """HTTP representation of a course retrieval query."""


class RagSearchResponse(BaseModel):
    results: list[RetrievalResult]


class RagAnswerResponse(BaseModel):
    answer: str
    citations: list[str]
    results: list[RetrievalResult]


def _course_context(results: list[RetrievalResult]) -> list[dict[str, str]]:
    return [
        {
            "course_code": str(result.metadata.get("course_code", "")),
            "document_text": result.document_text,
        }
        for result in results
    ]


async def _retrieve(request: RagSearchRequest) -> list[RetrievalResult]:
    try:
        return await RagRetriever().retrieve(RetrievalQuery(**request.model_dump()))
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Course retrieval failed") from exc


@router.post("/search", response_model=RagSearchResponse)
async def search(request: RagSearchRequest) -> RagSearchResponse:
    """Embed a question and return the closest course documents from Supabase."""
    return RagSearchResponse(results=await _retrieve(request))


@router.post("/answer", response_model=RagAnswerResponse)
async def answer(request: RagSearchRequest) -> RagAnswerResponse:
    """Generate an answer constrained to the courses returned by semantic retrieval."""
    results = await _retrieve(request)
    if not results:
        return RagAnswerResponse(
            answer="I could not find course records that answer this question.",
            citations=[],
            results=[],
        )
    try:
        grounded_answer = await OpenRouterClient().answer_from_courses(
            request.question, _course_context(results)
        )
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Grounded answer generation failed")
        raise HTTPException(status_code=502, detail="Grounded answer generation failed") from exc
    retrieved_codes = [course["course_code"] for course in _course_context(results) if course["course_code"]]
    cited_codes = set(re.findall(r"\b[A-Z]{2,5}\s\d{3}\b", grounded_answer))
    citations = list(dict.fromkeys(code for code in retrieved_codes if code in cited_codes))
    return RagAnswerResponse(answer=grounded_answer, citations=citations, results=results)
