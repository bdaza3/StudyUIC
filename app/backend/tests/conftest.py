"""Pytest configuration and shared fixtures for StudyUIC backend tests."""

import pytest


@pytest.fixture
def sample_course_record():
    """A sample CourseRecord for testing document construction."""
    from app.backend.services.rag_documents import CourseRecord

    return CourseRecord(
        id="test-cs-251",
        course_code="CS 251",
        title="Data Structures",
        department="CS",
        credits=3,
        course_level=200,
        description="Study of data structures.",
        prerequisites="CS 150",
        corequisites=None,
        long_description="Comprehensive study of arrays, lists, stacks, queues, trees, graphs, "
        "and algorithms for searching and sorting.",
    )


@pytest.fixture
def sample_course_record_minimal():
    """A minimal CourseRecord with only required fields."""
    from app.backend.services.rag_documents import CourseRecord

    return CourseRecord(
        id="test-math-310",
        course_code="MATH 310",
        title="Applied Linear Algebra",
        department="MATH",
        credits=None,
        course_level=None,
        description=None,
        prerequisites=None,
        corequisites=None,
        long_description=None,
    )


@pytest.fixture
def rag_document_metadata():
    """A sample RagDocumentMetadata object."""
    from app.backend.services.rag_documents import RagDocumentMetadata

    return RagDocumentMetadata(
        department="CS",
        course_code="CS 401",
        course_level=400,
        credits=3,
        course_title="Computer Algorithms I",
        source_type="course",
    )


def pytest_configure(config):
    """Register custom markers for RAG tests."""
    config.addinivalue_line(
        "markers", "rag_document: mark test as RAG document construction test"
    )
    config.addinivalue_line("markers", "rag_ingestion: mark test as RAG ingestion test")
    config.addinivalue_line("markers", "rag_retrieval: mark test as RAG retrieval test")
    config.addinivalue_line("markers", "embedding: mark test as embedding test")
