import os
import re

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client


load_dotenv()


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

UIC_URL = "https://catalog.uic.edu/ucat/course-descriptions/cs/"

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
)


# ---------------------------------------------------------
# HTTP
# ---------------------------------------------------------

def get_page() -> BeautifulSoup:
    response = requests.get(
        UIC_URL,
        timeout=30,
        headers={
            "User-Agent": "StudyUIC Course Importer/1.0"
        },
    )

    response.raise_for_status()

    return BeautifulSoup(
        response.text,
        "html.parser",
    )


# ---------------------------------------------------------
# Text helpers
# ---------------------------------------------------------

def clean_text(value: str) -> str:
    """
    Normalize whitespace, including non-breaking spaces
    used by the UIC catalog.
    """

    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)

    return value.strip()


# ---------------------------------------------------------
# Credits
# ---------------------------------------------------------

def parse_credits(
    credits_text: str,
    full_text: str,
) -> int | None:
    """
    Determine the undergraduate credit value from a UIC
    course entry.

    Examples:

        "3 hours"       -> 3
        "1-3 hours"     -> 1
        "3 or 4 hours"  -> 3
        "0-4 hours"     -> 3 if the course later says
                           "3 undergraduate hours"
        "0 hours"       -> 0

    UIC often lists variable undergraduate/graduate
    credits like:

        3 or 4 hours.
        ...
        3 undergraduate hours. 4 graduate hours.

    In those cases, prefer the explicit undergraduate value.
    """

    normalized_text = clean_text(full_text)

    # Prefer explicit undergraduate credit information.
    undergraduate_match = re.search(
        r"(\d+)\s+undergraduate\s+hours?",
        normalized_text,
        flags=re.IGNORECASE,
    )

    if undergraduate_match:
        return int(
            undergraduate_match.group(1)
        )

    # Otherwise use the first number in the course header.
    numbers = re.findall(
        r"\d+",
        credits_text,
    )

    if not numbers:
        return None

    return int(numbers[0])


# ---------------------------------------------------------
# Description
# ---------------------------------------------------------

def extract_description(
    full_text: str,
) -> str | None:
    """
    Extract the main course description.

    Stops before catalog metadata such as:
        Course Information:
        Prerequisite(s):
        Class Schedule Information:
    """

    description = re.split(
        r"Course Information:"
        r"|Prerequisite\s*\(s\):"
        r"|Class Schedule Information:"
        r"|Course Schedule Information:"
        r"|Recommended [Bb]ackground:",
        full_text,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    description = clean_text(description)

    return description or None


# ---------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------

def extract_prerequisites(
    text: str,
) -> str | None:
    """
    Extract the prerequisite section from a course entry.
    """

    match = re.search(
        r"Prerequisite\s*\(s\):\s*(.*?)(?="
        r"Class Schedule Information:"
        r"|Course Schedule Information:"
        r"|Recommended [Bb]ackground:"
        r"|$)",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    value = clean_text(
        match.group(1)
    )

    return value or None


# ---------------------------------------------------------
# Corequisites
# ---------------------------------------------------------

def extract_corequisites(
    text: str,
) -> str | None:
    """
    Extract explicit concurrent-registration requirements.

    Example:

        Credit or concurrent registration in CS 211
    """

    matches = re.findall(
        r"(?:Credit or )?concurrent registration in "
        r"([A-Z]{2,5}\s+\d{3})",
        text,
        flags=re.IGNORECASE,
    )

    if not matches:
        return None

    unique = []

    for course in matches:
        course = course.upper()

        if course not in unique:
            unique.append(course)

    return ", ".join(unique)


# ---------------------------------------------------------
# Course extraction
# ---------------------------------------------------------

def extract_courses(
    soup: BeautifulSoup,
) -> list[dict]:
    """
    Extract all CS courses from the UIC catalog.

    The UIC page separates course headers from the rest
    of the course information, so we treat a matching
    CS XXX header as the beginning of a course and collect
    subsequent paragraphs until the next course header.
    """

    courses = []

    paragraphs = soup.find_all("p")

    current_course = None
    current_parts = []

    # Examples this pattern handles:

    # CS 111. Program Design I. 3 hours.
    # CS 401. Computer Algorithms I. 3 or 4 hours.
    # CS 425. Computer Graphics I. 0-4 hours.
    # CS 194. Special Topics in Computer Science. 1-3 hours.

    course_header_pattern = re.compile(
        r"^CS\s+(\d{3})\.\s+"
        r"(.+?)\.\s+"
        r"(\d+\s*(?:-\s*|\bor\b)?\s*\d*)"
        r"\s+hours?\.",
        flags=re.IGNORECASE,
    )

    def save_current_course():
        """
        Convert the currently accumulated course information
        into a database row.
        """

        if current_course is None:
            return

        full_text = clean_text(
            " ".join(current_parts)
        )

        course_number = current_course[
            "course_number"
        ]

        credits = parse_credits(
            current_course["credits_text"],
            full_text,
        )

        courses.append({
            "department": "CS",
            "course_number": course_number,
            "title": current_course["title"],
            "description": extract_description(
                full_text
            ),
            "credits": credits,
            "course_level": int(
                course_number[0]
            ) * 100,
            "prerequisites": extract_prerequisites(
                full_text
            ),
            "corequisites": extract_corequisites(
                full_text
            ),
            "long_description": full_text,
            "active": True,
        })

    for paragraph in paragraphs:
        text = paragraph.get_text(
            " ",
            strip=True,
        )

        text = clean_text(text)

        if not text:
            continue

        match = course_header_pattern.match(
            text
        )

        if match:
            # Save the previous course before starting
            # the next one.
            save_current_course()

            current_course = {
                "course_number": match.group(1),
                "title": match.group(2).strip(),
                "credits_text": match.group(3).strip(),
            }

            current_parts = []

            # Sometimes additional information is located
            # in the same paragraph as the header.
            remaining = text[
                match.end():
            ].strip()

            if remaining:
                current_parts.append(
                    remaining
                )

        elif current_course is not None:
            # This paragraph belongs to the current course.
            current_parts.append(text)

    # Save the final course.
    save_current_course()

    return courses


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

def validate_courses(
    courses: list[dict],
) -> None:
    """
    Validate all parsed courses before uploading them.
    """

    if not courses:
        raise ValueError(
            "No courses were found. "
            "Aborting upload."
        )

    seen = set()

    for course in courses:

        key = (
            course["department"],
            course["course_number"],
        )

        # Check duplicates.
        if key in seen:
            raise ValueError(
                f"Duplicate course found: {key}"
            )

        seen.add(key)

        # Course title.
        if not course["title"]:
            raise ValueError(
                f"Missing title for {key}"
            )

        # Credits.
        #
        # 0 is allowed because UIC has legitimate
        # zero-credit courses such as CS 499.
        if course["credits"] is not None:
            if not 0 <= course["credits"] <= 12:
                raise ValueError(
                    f"Invalid credits for {key}: "
                    f"{course['credits']}"
                )

        # Course level.
        if not (
            100
            <= course["course_level"]
            <= 599
        ):
            raise ValueError(
                f"Invalid course level for {key}: "
                f"{course['course_level']}"
            )


# ---------------------------------------------------------
# Supabase
# ---------------------------------------------------------

def upload_courses(
    courses: list[dict],
) -> None:
    """
    Upsert all courses into Supabase.

    Your database has:

        UNIQUE (department, course_number)

    so this operation is safe to rerun.
    """

    response = (
        supabase
        .table("courses")
        .upsert(
            courses,
            on_conflict=(
                "department,course_number"
            ),
        )
        .execute()
    )

    print(
        "Supabase upload successful."
    )

    print(
        f"Returned rows: "
        f"{len(response.data or [])}"
    )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print(
        "Fetching UIC CS catalog..."
    )

    soup = get_page()

    print(
        "Parsing courses..."
    )

    courses = extract_courses(
        soup
    )

    # Validate BEFORE uploading.
    validate_courses(
        courses
    )

    print()
    print(
        f"Found {len(courses)} CS courses."
    )

    print()

    for course in courses:
        print(
            f"  {course['department']} "
            f"{course['course_number']} - "
            f"{course['title']} "
            f"({course['credits']} credits)"
        )

    print()

    print(
        "Uploading to Supabase..."
    )

    upload_courses(
        courses
    )

    print()

    print(
        "Import complete."
    )


if __name__ == "__main__":
    main()