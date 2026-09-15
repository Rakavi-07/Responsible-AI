import json
import re
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_DIR = Path("json")
OUTPUT_DIR = Path("final_json")

OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# SKILL DICTIONARIES
# ============================================================

SKILL_CATEGORIES = {

    "programming_languages": [
        "Python",
        "Java",
        "JavaScript",
        "TypeScript",
        "C++",
        "C#",
        "C",
        "SQL",
        "Go",
        "Rust",
        "PHP",
        "Ruby",
        "Kotlin",
        "Swift",
        "R",
        "MATLAB"
    ],

    "frameworks": [
        "Next.js",
        "React",
        "React.js",
        "Angular",
        "Vue.js",
        "Vue",
        "Django",
        "Flask",
        "FastAPI",
        "Spring Boot",
        "Spring",
        "Express.js",
        "Express",
        "Node.js",
        "Tailwind CSS",
        "Bootstrap",
        "Flutter"
    ],

    "databases": [
        "MySQL",
        "PostgreSQL",
        "MongoDB",
        "SQLite",
        "Oracle",
        "Redis",
        "Firestore",
        "DynamoDB",
        "Cassandra",
        "MariaDB"
    ],

    "tools": [
        "Git",
        "GitHub",
        "GitLab",
        "VS Code",
        "Docker",
        "Postman",
        "Jira",
        "Figma",
        "Eclipse",
        "Visual Studio"
    ],

    "cloud": [
        "AWS",
        "Amazon Web Services",
        "Azure",
        "Microsoft Azure",
        "Google Cloud",
        "GCP",
        "Firebase",
        "Vercel",
        "Heroku"
    ],

    "soft_skills": [
        "Communication",
        "Leadership",
        "Teamwork",
        "Team Leadership",
        "Problem Solving",
        "Problem-Solving",
        "Time Management",
        "Negotiation",
        "Presentation",
        "Public Speaking",
        "Adaptability",
        "Creativity"
    ]
}


# ============================================================
# GENERAL CLEANING
# ============================================================

def clean_text(text):

    if text is None:
        return ""

    text = str(text)

    text = text.replace("\u200b", "")
    text = text.replace("\ufeff", "")

    # Preserve image marker
    if text.startswith("[IMAGE:"):
        return text.strip()

    text = re.sub(
        r"^[•●▪■□◆◇◦\-\*]+\s*",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# LIST CLEANING
# ============================================================

def clean_list(items):

    if not items:
        return []

    if not isinstance(items, list):
        items = [items]

    result = []

    for item in items:

        item = clean_text(item)

        if item and item not in result:

            result.append(item)

    return result


# ============================================================
# IMAGE EXTRACTION
# ============================================================

def find_image_path(value):

    if value is None:
        return None

    # Direct string
    if isinstance(value, str):

        match = re.search(
            r"\[IMAGE:\s*(.*?)\]",
            value,
            re.IGNORECASE
        )

        if match:
            return match.group(1).strip()

        # Already a path
        if (
            "images/" in value
            or "images\\" in value
        ):

            return value.strip()

        return None

    # Dictionary
    if isinstance(value, dict):

        possible_keys = [
            "photo",
            "image",
            "image_path",
            "photo_path",
            "path"
        ]

        for key in possible_keys:

            if key in value:

                result = find_image_path(
                    value[key]
                )

                if result:
                    return result

        for item in value.values():

            result = find_image_path(item)

            if result:
                return result

    # List
    if isinstance(value, list):

        for item in value:

            result = find_image_path(item)

            if result:
                return result

    return None


# ============================================================
# DATE EXTRACTION
# ============================================================

def extract_date_range(text):

    if not text:
        return None, None

    patterns = [

        r"([A-Za-z]+\s+\d{4})\s*[–—-]\s*"
        r"([A-Za-z]+\s+\d{4})",

        r"\b(\d{4})\s*[–—-]\s*(\d{4})\b",

        r"([A-Za-z]+\s+\d{4})\s*[–—-]\s*"
        r"(Present|Current)",

        r"\b(\d{4})\s*[–—-]\s*"
        r"(Present|Current)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            return (
                match.group(1),
                match.group(2)
            )

    return None, None


# ============================================================
# GPA / CGPA
# ============================================================

def extract_gpa(text):

    if not text:
        return None

    patterns = [
        r"CGPA\s*[:\-]?\s*(\d+(?:\.\d+)?)",
        r"GPA\s*[:\-]?\s*(\d+(?:\.\d+)?)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            try:
                return float(
                    match.group(1)
                )
            except ValueError:
                pass

    return None


# ============================================================
# SKILL DETECTION
# ============================================================

def contains_skill(text, skill):

    pattern = (
        r"(?<![A-Za-z0-9])"
        + re.escape(skill)
        + r"(?![A-Za-z0-9])"
    )

    return bool(
        re.search(
            pattern,
            text,
            re.IGNORECASE
        )
    )


# ============================================================
# SKILL CATEGORIZATION
# ============================================================

def categorize_skills(skill_data):

    result = {
        "programming_languages": [],
        "frameworks": [],
        "databases": [],
        "tools": [],
        "cloud": [],
        "soft_skills": []
    }

    raw_lines = []

    if isinstance(skill_data, dict):

        raw_lines.extend(
            skill_data.get(
                "technical",
                []
            )
        )

        for category in result:

            existing = skill_data.get(
                category,
                []
            )

            if isinstance(existing, list):

                result[category].extend(
                    existing
                )

    elif isinstance(skill_data, list):

        raw_lines = skill_data

    raw_text = " ".join(
        clean_text(x)
        for x in raw_lines
    )

    for category, skills in SKILL_CATEGORIES.items():

        for skill in skills:

            if contains_skill(
                raw_text,
                skill
            ):

                if skill not in result[category]:

                    result[category].append(
                        skill
                    )

    # Remove Firebase from database category
    if "Firebase" in result["databases"]:

        result["databases"].remove(
            "Firebase"
        )

    # Clean all categories
    for category in result:

        result[category] = clean_list(
            result[category]
        )

    return result


# ============================================================
# EDUCATION PARSER
# ============================================================

def parse_education(items):

    if not items:
        return []

    items = clean_list(items)

    education = []

    current = None

    degree_pattern = re.compile(
        r"\b("
        r"B\.?\s*Tech|"
        r"B\.?\s*E\.?|"
        r"B\.?\s*Sc|"
        r"B\.?\s*S\.?|"
        r"M\.?\s*Tech|"
        r"M\.?\s*E\.?|"
        r"M\.?\s*Sc|"
        r"M\.?\s*S\.?|"
        r"MBA|"
        r"Ph\.?\s*D|"
        r"Bachelor(?:'s)?|"
        r"Master(?:'s)?|"
        r"Diploma"
        r")\b",
        re.IGNORECASE
    )

    institution_words = [
        "university",
        "institute",
        "college",
        "school",
        "academy"
    ]

    for item in items:

        lower = item.lower()

        degree_match = degree_pattern.search(
            item
        )

        looks_like_institution = any(
            word in lower
            for word in institution_words
        )

        # ----------------------------------------------------
        # Institution
        # ----------------------------------------------------

        if (
            looks_like_institution
            and current is None
        ):

            current = {
                "institution": item,
                "location": None,
                "degree": None,
                "field_of_study": None,
                "start_date": None,
                "end_date": None,
                "graduation_year": None,
                "cgpa": None
            }

            education.append(
                current
            )

        # ----------------------------------------------------
        # Degree
        # ----------------------------------------------------

        if degree_match:

            if current is None:

                current = {
                    "institution": None,
                    "location": None,
                    "degree": None,
                    "field_of_study": None,
                    "start_date": None,
                    "end_date": None,
                    "graduation_year": None,
                    "cgpa": None
                }

                education.append(
                    current
                )

            current["degree"] = (
                degree_match.group(1)
                .replace(" ", "")
            )

            remainder = item[
                degree_match.end():
            ].strip()

            remainder = remainder.strip(
                " :-|,"
            )

            remainder = re.split(
                r"\bGraduation Year\b"
                r"|\bCGPA\b"
                r"|\bGPA\b",
                remainder,
                flags=re.IGNORECASE
            )[0]

            remainder = remainder.strip(
                " :-|,"
            )

            remainder = re.sub(
                r"^in\s+",
                "",
                remainder,
                flags=re.IGNORECASE
            )

            if remainder:

                current[
                    "field_of_study"
                ] = remainder.strip()

        # ----------------------------------------------------
        # Date
        # ----------------------------------------------------

        start, end = extract_date_range(
            item
        )

        if current and (start or end):

            current["start_date"] = start
            current["end_date"] = end

            if end and end.isdigit():

                current[
                    "graduation_year"
                ] = int(end)

        # ----------------------------------------------------
        # Graduation year
        # ----------------------------------------------------

        graduation_match = re.search(
            r"(?:Graduation Year|Graduated|Expected)"
            r"\s*[:\-]?\s*(\d{4})",
            item,
            re.IGNORECASE
        )

        if (
            graduation_match
            and current
        ):

            current[
                "graduation_year"
            ] = int(
                graduation_match.group(1)
            )

        # ----------------------------------------------------
        # CGPA
        # ----------------------------------------------------

        gpa = extract_gpa(item)

        if (
            gpa is not None
            and current
        ):

            current["cgpa"] = gpa

    return education


# ============================================================
# EXPERIENCE
# ============================================================

def looks_like_job_heading(text):

    keywords = [
        "intern",
        "engineer",
        "developer",
        "manager",
        "analyst",
        "representative",
        "consultant",
        "director",
        "specialist",
        "associate",
        "officer",
        "architect",
        "administrator",
        "coordinator",
        "designer",
        "scientist",
        "lead",
        "supervisor"
    ]

    lower = text.lower()

    return any(
        keyword in lower
        for keyword in keywords
    )


def parse_experience(items):

    if not items:
        return []

    items = clean_list(items)

    experience = []

    current = None

    for item in items:

        # Ignore image markers
        if item.startswith("[IMAGE:"):
            continue

        start, end = extract_date_range(
            item
        )

        # ----------------------------------------------------
        # New job
        # ----------------------------------------------------

        if (
            (start or end)
            and looks_like_job_heading(item)
        ):

            current = {
                "company": None,
                "job_title": None,
                "location": None,
                "start_date": start,
                "end_date": end,
                "responsibilities": [],
                "achievements": []
            }

            # Role — Company
            if " — " in item:

                role, company = item.split(
                    " — ",
                    1
                )

                current[
                    "job_title"
                ] = clean_text(role)

                company = re.sub(
                    r"\s*(?:Jan|Feb|Mar|Apr|May|Jun|"
                    r"Jul|Aug|Sep|Oct|Nov|Dec|"
                    r"[A-Za-z]+\s+\d{4}|\d{4}).*$",
                    "",
                    company,
                    flags=re.IGNORECASE
                )

                current[
                    "company"
                ] = clean_text(company)

            # Company – Location
            elif " – " in item:

                parts = item.split(
                    " – "
                )

                if parts:

                    current[
                        "company"
                    ] = clean_text(
                        parts[0]
                    )

            experience.append(
                current
            )

            continue

        # ----------------------------------------------------
        # Current job content
        # ----------------------------------------------------

        if current:

            lower = item.lower()

            achievement_words = [
                "recognized",
                "awarded",
                "won",
                "increased",
                "reduced",
                "ranked",
                "achieved",
                "saved",
                "generated",
                "improved"
            ]

            if any(
                word in lower
                for word in achievement_words
            ):

                current[
                    "achievements"
                ].append(item)

            else:

                current[
                    "responsibilities"
                ].append(item)

    return experience


# ============================================================
# PROJECT TECHNOLOGY EXTRACTION
# ============================================================

def extract_project_technologies(text):

    technologies = []

    for category, skills in SKILL_CATEGORIES.items():

        for skill in skills:

            if contains_skill(
                text,
                skill
            ):

                if skill not in technologies:

                    technologies.append(
                        skill
                    )

    return technologies


# ============================================================
# PROJECT DESCRIPTION DETECTION
# ============================================================

def is_project_description(text):

    description_starts = [
        "designed",
        "developed",
        "built",
        "implemented",
        "created",
        "integrated",
        "processed",
        "engineered",
        "developing",
        "worked",
        "used",
        "deployed",
        "automated"
    ]

    lower = text.lower().strip()

    return any(
        lower.startswith(word)
        for word in description_starts
    )


# ============================================================
# PROJECT HEADING
# ============================================================

def parse_project_heading(text):

    text = clean_text(text)

    technologies = (
        extract_project_technologies(
            text
        )
    )

    if technologies:

        positions = []

        for skill in technologies:

            match = re.search(
                re.escape(skill),
                text,
                re.IGNORECASE
            )

            if match:

                positions.append(
                    (
                        match.start(),
                        skill
                    )
                )

        if positions:

            first_position = min(
                positions,
                key=lambda x: x[0]
            )

            project_name = text[
                :first_position[0]
            ].strip(
                " :-–—|,"
            )

            if len(project_name) >= 3:

                return (
                    project_name,
                    technologies
                )

    return text, technologies


# ============================================================
# PROJECT PARSER
# ============================================================

def parse_projects(items):

    if not items:
        return []

    items = clean_list(items)

    projects = []

    current = None

    for item in items:

        if item.startswith("[IMAGE:"):
            continue

        # ----------------------------------------------------
        # Description
        # ----------------------------------------------------

        if (
            current
            and is_project_description(item)
        ):

            current[
                "description"
            ].append(item)

            continue

        project_name, technologies = (
            parse_project_heading(item)
        )

        # ----------------------------------------------------
        # New project
        # ----------------------------------------------------

        if current:

            if (
                len(item) < 180
                and not is_project_description(item)
            ):

                current = {
                    "name": project_name,
                    "description": [],
                    "technologies": technologies,
                    "achievements": []
                }

                projects.append(
                    current
                )

                continue

        # ----------------------------------------------------
        # First project
        # ----------------------------------------------------

        if current is None:

            current = {
                "name": project_name,
                "description": [],
                "technologies": technologies,
                "achievements": []
            }

            projects.append(
                current
            )

    for project in projects:

        project[
            "description"
        ] = clean_list(
            project[
                "description"
            ]
        )

        project[
            "technologies"
        ] = clean_list(
            project[
                "technologies"
            ]
        )

    return projects


# ============================================================
# SIMPLE SECTIONS
# ============================================================

def simple_list(data, section):

    value = data.get(
        section,
        []
    )

    if not isinstance(
        value,
        list
    ):

        value = [value]

    return clean_list(
        value
    )


# ============================================================
# FIND PHOTO IN RESUME DATA
# ============================================================

def extract_photo(data):

    # First check personal information
    personal = data.get(
        "personal_information",
        {}
    )

    photo = find_image_path(
        personal
    )

    if photo:
        return photo

    # Check header
    photo = find_image_path(
        data.get(
            "header",
            []
        )
    )

    if photo:
        return photo

    # Check entire JSON as fallback
    photo = find_image_path(
        data
    )

    return photo


# ============================================================
# TRANSFORM ONE RESUME
# ============================================================

def transform_resume(data):

    personal = data.get(
        "personal_information",
        {}
    )

    if not isinstance(
        personal,
        dict
    ):

        personal = {}

    photo = extract_photo(
        data
    )

    # --------------------------------------------------------
    # Personal information
    # --------------------------------------------------------

    personal_information = {

        "name":
            personal.get("name"),

        "email":
            personal.get("email"),

        "phone":
            personal.get("phone"),

        "location":
            personal.get("location"),

        "linkedin":
            personal.get("linkedin"),

        "github":
            personal.get("github"),

        "portfolio":
            personal.get("portfolio")
    }

    # --------------------------------------------------------
    # Add photo ONLY when present
    # --------------------------------------------------------

    if photo:

        personal_information[
            "photo"
        ] = photo

    # --------------------------------------------------------
    # Final Blueprint
    # --------------------------------------------------------

    final = {

        "personal_information":
            personal_information,

        "summary":
            data.get(
                "summary"
            ),

        "education":
            parse_education(
                data.get(
                    "education",
                    []
                )
            ),

        "experience":
            parse_experience(
                data.get(
                    "experience",
                    []
                )
            ),

        "skills":
            categorize_skills(
                data.get(
                    "skills",
                    {}
                )
            ),

        "projects":
            parse_projects(
                data.get(
                    "projects",
                    []
                )
            ),

        "certifications":
            simple_list(
                data,
                "certifications"
            ),

        "achievements":
            simple_list(
                data,
                "achievements"
            ),

        "languages":
            simple_list(
                data,
                "languages"
            ),

        "leadership":
            simple_list(
                data,
                "leadership"
            ),

        "publications":
            simple_list(
                data,
                "publications"
            ),

        "military_experience":
            simple_list(
                data,
                "military_experience"
            ),

        "affiliations":
            simple_list(
                data,
                "affiliations"
            ),

        "training":
            simple_list(
                data,
                "training"
            ),

        "coursework":
            simple_list(
                data,
                "coursework"
            )
    }

    return final


# ============================================================
# MAIN
# ============================================================

def main():

    files = sorted(
        INPUT_DIR.glob("*.json"),
        key=lambda x: x.name.lower()
    )

    print("=" * 70)
    print("FINAL BLUEPRINT GENERATOR")
    print("=" * 70)

    print(
        f"\nInput JSON files: {len(files)}"
    )

    if not files:

        print(
            "\nERROR: No JSON files found in:"
        )

        print(
            INPUT_DIR.resolve()
        )

        return

    successful = 0

    for file in files:

        print("-" * 70)

        print(
            f"Processing: {file.name}"
        )

        try:

            with open(
                file,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            final_data = transform_resume(
                data
            )

            output_file = (
                OUTPUT_DIR /
                file.name
            )

            with open(
                output_file,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    final_data,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

            # ------------------------------------------------
            # Show photo status
            # ------------------------------------------------

            photo = (
                final_data[
                    "personal_information"
                ].get("photo")
            )

            if photo:

                print(
                    f"Photo: {photo}"
                )

            else:

                print(
                    "Photo: None"
                )

            print(
                f"Created: "
                f"{output_file.name}"
            )

            successful += 1

        except Exception as e:

            print(
                f"ERROR: {e}"
            )

    print()
    print("=" * 70)
    print("FINAL BLUEPRINT GENERATION COMPLETE")
    print("=" * 70)

    print(
        f"Successfully processed: "
        f"{successful}/{len(files)}"
    )

    print(
        f"Output directory: "
        f"{OUTPUT_DIR.resolve()}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()