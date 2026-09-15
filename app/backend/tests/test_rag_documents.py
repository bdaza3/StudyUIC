"""Unit tests for RAG document construction, determinism, and ingestion logic."""

import pytest

from app.backend.services.rag_documents import (
    CourseRecord,
    RagDocumentMetadata,
    construct_course_document,
    documents_equal_ignoring_id,
)


class TestRagDocumentConstruction:
    """Test deterministic document construction."""

    def test_construct_course_document_minimal(self) -> None:
        """Test document construction with minimal course data."""
        course = CourseRecord(
            id="test-course-1",
            course_code="CS 150",
            title="Introduction to CS",
            department="CS",
            credits=None,
            course_level=None,
            description=None,
            prerequisites=None,
            corequisites=None,
            long_description=None,
        )

        doc = construct_course_document(course)

        assert doc.source_type == "course"
        assert doc.source_id == "test-course-1"
        assert doc.source_table == "courses"
        assert "CS 150" in doc.document_text
        assert "Introduction to CS" in doc.document_text
        assert "CS" in doc.document_text
        assert doc.metadata.course_code == "CS 150"
        assert doc.content_hash is not None

    def test_construct_course_document_full(self) -> None:
        """Test document construction with complete course metadata."""
        course = CourseRecord(
            id="test-course-2",
            course_code="CS 251",
            title="Data Structures",
            department="CS",
            credits=3,
            course_level=200,
            description="Study of fundamental data structures.",
            prerequisites="CS 150",
            corequisites=None,
            long_description="In-depth study of arrays, lists, stacks, queues, trees, and graphs. "
            "Analysis of algorithms for searching and sorting.",
        )

        doc = construct_course_document(course)

        assert doc.source_type == "course"
        assert "CS 251" in doc.document_text
        assert "Data Structures" in doc.document_text
        assert "Credits: 3" in doc.document_text
        assert "Course Level: 200" in doc.document_text
        assert "Prerequisites: CS 150" in doc.document_text
        assert "In-depth study of arrays" in doc.document_text
        assert doc.metadata.credits == 3
        assert doc.metadata.course_level == 200

    def test_construct_course_document_determinism(self) -> None:
        """Test that identical course records produce identical documents."""
        course1 = CourseRecord(
            id="test-course-3",
            course_code="CS 361",
            title="Machine Organization",
            department="CS",
            credits=3,
            course_level=300,
            description="Computer architecture and organization.",
            prerequisites="CS 251",
            corequisites=None,
            long_description=None,
        )

        course2 = CourseRecord(
            id="test-course-3",
            course_code="CS 361",
            title="Machine Organization",
            department="CS",
            credits=3,
            course_level=300,
            description="Computer architecture and organization.",
            prerequisites="CS 251",
            corequisites=None,
            long_description=None,
        )

        doc1 = construct_course_document(course1)
        doc2 = construct_course_document(course2)

        assert doc1.document_text == doc2.document_text
        assert doc1.content_hash == doc2.content_hash

    def test_construct_course_document_content_hash_changes(self) -> None:
        """Test that different content produces different content hashes."""
        course1 = CourseRecord(
            id="test-course-4",
            course_code="CS 401",
            title="Computer Algorithms I",
            department="CS",
            credits=3,
            course_level=400,
            description="Study of algorithms.",
            prerequisites="CS 251",
            corequisites=None,
            long_description=None,
        )

        course2 = CourseRecord(
            id="test-course-4",
            course_code="CS 401",
            title="Computer Algorithms I - Updated",  # Different title
            department="CS",
            credits=3,
            course_level=400,
            description="Study of algorithms.",
            prerequisites="CS 251",
            corequisites=None,
            long_description=None,
        )

        doc1 = construct_course_document(course1)
        doc2 = construct_course_document(course2)

        assert doc1.content_hash != doc2.content_hash

    def test_construct_course_document_metadata_fields(self) -> None:
        """Test that metadata is correctly extracted and stored."""
        course = CourseRecord(
            id="test-course-5",
            course_code="MATH 310",
            title="Applied Linear Algebra",
            department="MATH",
            credits=4,
            course_level=300,
            description="Applications of linear algebra.",
            prerequisites="MATH 210, MATH 220",
            corequisites=None,
            long_description=None,
        )

        doc = construct_course_document(course)
        metadata = doc.metadata

        assert metadata.department == "MATH"
        assert metadata.course_code == "MATH 310"
        assert metadata.course_level == 300
        assert metadata.credits == 4
        assert metadata.course_title == "Applied Linear Algebra"
        assert metadata.source_type == "course"

    def test_documents_equal_ignoring_id(self) -> None:
        """Test document equality check."""
        course1 = CourseRecord(
            id="id-1",
            course_code="ECE 266",
            title="Embedded Systems Design",
            department="ECE",
            credits=3,
            course_level=200,
            description="Embedded systems design principles.",
            prerequisites=None,
            corequisites=None,
            long_description=None,
        )

        course2 = CourseRecord(
            id="id-2",  # Different ID
            course_code="ECE 266",
            title="Embedded Systems Design",
            department="ECE",
            credits=3,
            course_level=200,
            description="Embedded systems design principles.",
            prerequisites=None,
            corequisites=None,
            long_description=None,
        )

        doc1 = construct_course_document(course1)
        doc2 = construct_course_document(course2)

        # Content is the same, but source_id is different
        assert doc1.source_id != doc2.source_id
        assert documents_equal_ignoring_id(doc1, doc2)

    def test_construct_course_document_with_corequisites(self) -> None:
        """Test handling of corequisites."""
        course = CourseRecord(
            id="test-course-6",
            course_code="CS 401",
            title="Computer Algorithms I",
            department="CS",
            credits=3,
            course_level=400,
            description="Advanced algorithms.",
            prerequisites="CS 251",
            corequisites="CS 461",
            long_description=None,
        )

        doc = construct_course_document(course)

        assert "Corequisites: CS 461" in doc.document_text

    def test_construct_course_document_long_description_preferred(self) -> None:
        """Test that long_description is preferred over description."""
        course = CourseRecord(
            id="test-course-7",
            course_code="IDS 270",
            title="Data Science",
            department="IDS",
            credits=3,
            course_level=200,
            description="Short description.",
            prerequisites=None,
            corequisites=None,
            long_description="Long detailed description of data science principles and applications.",
        )

        doc = construct_course_document(course)

        # Should include the long description, not the short one
        assert "Long detailed description" in doc.document_text
        assert "Short description." not in doc.document_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
