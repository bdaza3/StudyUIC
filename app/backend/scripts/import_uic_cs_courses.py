import os
import re

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client


load_dotenv()

UIC_URL = "https://catalog.uic.edu/ucat/course-descriptions/cs/"

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
)


def get_page() -> BeautifulSoup:
    response = requests.get(
        UIC_URL,
        timeout=30,
        headers={
            "User-Agent": "StudyUIC Course Importer/1.0"
        },
    )

    response.raise_for_status()

    return BeautifulSoup(response.text, "html.parser")


def extract_courses(soup: BeautifulSoup) -> list[dict]:
    courses = []

    # UIC's catalog puts each course in a paragraph.
    for paragraph in soup.find_all("p"):
        text = paragraph.get_text(" ", strip=True)

        # Example:
        # CS 111. Program Design I. 3 hours.
        match = re.match(
            r"^CS\s+(\d{3})\.\s+(.+?)\.\s+"
            r"(\d+(?:-\d+)?)\s+hours\.",
            text,
        )

        if not match:
            continue

        course_number = match.group(1)
        title = match.group(2).strip()
        credits_text = match.group(3)

        # For courses such as "3-4 hours", use the undergraduate
        # credit value when possible. Otherwise use the first number.
        credits = int(credits_text.split("-")[0])

        # The catalog may have a lot of additional information
        # after the initial course description.
        remaining_text = text[match.end():].strip()

        # Try to isolate the actual description from Course Information.
        if "Course Information:" in remaining_text:
            description = remaining_text.split(
                "Course Information:", 1
            )[0].strip()
        else:
            description = remaining_text

        prerequisites = extract_prerequisites(text)
        corequisites = extract_corequisites(text)

        course_level = int(course_number[0]) * 100

        courses.append({
            "department": "CS",
            "course_number": course_number,
            "title": title,
            "description": description or None,
            "credits": credits,
            "course_level": course_level,
            "prerequisites": prerequisites,
            "corequisites": corequisites,
            "long_description": text,
            "active": True,
        })

    return courses


def extract_prerequisites(text: str) -> str | None:
    match = re.search(
        r"Prerequisite\(s\):\s*(.*?)(?="
        r"Class Schedule Information:|"
        r"Recommended [Bb]ackground:|"
        r"$)",
        text,
    )

    if not match:
        return None

    value = clean_text(match.group(1))

    return value or None


def extract_corequisites(text: str) -> str | None:
    # UIC sometimes expresses this inside the prerequisite text,
    # e.g. "Credit or concurrent registration in CS 211".
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


def clean_text(value: str) -> str:
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def validate_courses(courses: list[dict]) -> None:
    seen = set()

    for course in courses:
        key = (
            course["department"],
            course["course_number"],
        )

        if key in seen:
            raise ValueError(
                f"Duplicate course found: {key}"
            )

        seen.add(key)

        if not course["title"]:
            raise ValueError(
                f"Missing title for {key}"
            )

        if not 100 <= course["course_level"] <= 599:
            raise ValueError(
                f"Invalid course level: {course}"
            )


def upload_courses(courses: list[dict]) -> None:
    # Your table has a unique constraint on
    # (department, course_number), so this is safe to rerun.
    response = (
        supabase
        .table("courses")
        .upsert(
            courses,
            on_conflict="department,course_number",
        )
        .execute()
    )

    print(f"Supabase response: {response}")


def main():
    print("Fetching UIC CS catalog...")

    soup = get_page()

    print("Parsing courses...")

    courses = extract_courses(soup)

    validate_courses(courses)

    print(f"Found {len(courses)} CS courses.")

    for course in courses:
        print(
            f"  {course['department']} "
            f"{course['course_number']} - "
            f"{course['title']}"
        )

    print()
    print("Uploading to Supabase...")

    upload_courses(courses)

    print()
    print("Import complete.")


if __name__ == "__main__":
    main()