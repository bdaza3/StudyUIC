import hashlib
import json
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field


class RagDocumentMetadata(BaseModel):
    """Structured metadata for a RAG document."""

    department: str | None = None
    course_code: str | None = None
    course_level: int | None = None
    credits: int | None = None
    course_title: str | None = None
    source_type: str = "course"


class RagDocument(BaseModel):
    """A retrievable document with embedding and metadata."""

    source_type: str = Field(pattern="^(course|program|policy|resource)$")
    source_id: str
    source_table: str
    document_text: str
    metadata: RagDocumentMetadata
    content_hash: str


@dataclass(frozen=True)
class CourseRecord:
    """Raw course data from Supabase."""

    id: str
    course_code: str
    title: str
    department: str
    credits: int | None
    course_level: int | None
    description: str | None
    prerequisites: str | None
    corequisites: str | None
    long_description: str | None


def construct_course_document(course: CourseRecord) -> RagDocument:
    """
    Deterministically construct a RAG document from a course record.

    Same course record always produces identical document_text and metadata
    unless the underlying data changes.
    """
    lines = [
        f"Course: {course.course_code}",
        f"Title: {course.title}",
        f"Department: {course.department}",
    ]

    if course.credits:
        lines.append(f"Credits: {course.credits}")
    if course.course_level:
        lines.append(f"Course Level: {course.course_level}")
    if course.prerequisites:
        lines.append(f"Prerequisites: {course.prerequisites}")
    if course.corequisites:
        lines.append(f"Corequisites: {course.corequisites}")

    if course.long_description:
        lines.append(f"Description: {course.long_description}")
    elif course.description:
        lines.append(f"Description: {course.description}")

    document_text = "\n".join(lines)
    content_hash = _compute_content_hash(document_text)

    metadata = RagDocumentMetadata(
        department=course.department,
        course_code=course.course_code,
        course_level=course.course_level,
        credits=course.credits,
        course_title=course.title,
        source_type="course",
    )

    return RagDocument(
        source_type="course",
        source_id=course.id,
        source_table="courses",
        document_text=document_text,
        metadata=metadata,
        content_hash=content_hash,
    )


def _compute_content_hash(text: str) -> str:
    """Compute a deterministic hash of document content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def documents_equal_ignoring_id(doc1: RagDocument, doc2: RagDocument) -> bool:
    """Check if two documents have identical content (ignoring source_id if same table)."""
    return (
        doc1.source_type == doc2.source_type
        and doc1.document_text == doc2.document_text
        and doc1.content_hash == doc2.content_hash
    )
