import json
import re
from pathlib import Path
from copy import deepcopy


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_DIR = Path("sections")
OUTPUT_DIR = Path("json")
BLUEPRINT_FILE = Path("blueprint.json")

OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# LOAD BLUEPRINT
# ============================================================

with open(
    BLUEPRINT_FILE,
    "r",
    encoding="utf-8"
) as f:
    BLUEPRINT = json.load(f)


# ============================================================
# EMAIL EXTRACTION
# ============================================================

def extract_email(text):

    pattern = (
        r"[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    )

    match = re.search(pattern, text)

    if match:
        return match.group(0)

    return None


# ============================================================
# PHONE EXTRACTION
# ============================================================

def extract_phone(text):

    patterns = [
        r"\+?\d[\d\s().-]{8,}\d",
        r"\(\d{3}\)\s*\d{3}[-\s]\d{4}",
        r"\b\d{10}\b"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:
            return match.group(0).strip()

    return None


# ============================================================
# LINKEDIN EXTRACTION
# ============================================================

def extract_linkedin(text):

    pattern = (
        r"(?:https?://)?"
        r"(?:www\.)?"
        r"linkedin\.com/[^\s|]+"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if match:

        return match.group(0).rstrip(
            ".,)"
        )

    return None


# ============================================================
# GITHUB EXTRACTION
# ============================================================

def extract_github(text):

    pattern = (
        r"(?:https?://)?"
        r"(?:www\.)?"
        r"github\.com/[^\s|]+"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if match:

        return match.group(0).rstrip(
            ".,)"
        )

    return None


# ============================================================
# PORTFOLIO EXTRACTION
# ============================================================

def extract_portfolio(text):

    patterns = [
        r"https?://[^\s]+",
        r"[A-Za-z0-9.-]+\.vercel\.app"
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        for match in matches:

            lower = match.lower()

            if (
                "linkedin.com" not in lower
                and "github.com" not in lower
            ):

                return match.rstrip(
                    ".,)"
                )

    return None


# ============================================================
# IMAGE PATH EXTRACTION
# ============================================================

def extract_image_paths(text):

    if not text:
        return []

    pattern = (
        r"\[IMAGE:\s*(.*?)\]"
    )

    matches = re.findall(
        pattern,
        text,
        re.IGNORECASE
    )

    paths = []

    for match in matches:

        path = match.strip()

        if path and path not in paths:
            paths.append(path)

    return paths


# ============================================================
# NAME EXTRACTION
# ============================================================

def extract_name(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    ignored = {
        "HEADER",
        "SUMMARY",
        "SKILLS",
        "EXPERIENCE",
        "EDUCATION",
        "PROJECTS",
        "CERTIFICATIONS",
        "ACHIEVEMENTS",
        "LANGUAGES",
        "LEADERSHIP",
        "PUBLICATIONS",
        "TRAINING",
        "COURSEWORK",
        "AFFILIATIONS",
        "MILITARY EXPERIENCE"
    }

    for line in lines:

        # Never treat image marker as name
        if line.startswith("[IMAGE:"):
            continue

        upper = line.upper()

        if upper in ignored:
            continue

        # Ignore email
        if "@" in line:
            continue

        # Ignore phone / numbers
        if re.search(
            r"\d{3,}",
            line
        ):
            continue

        words = line.split()

        if 2 <= len(words) <= 5:

            if len(line) < 50:

                return line

    return None


# ============================================================
# GET SECTION CONTENT
# ============================================================

def get_section(
    text,
    section_name
):

    pattern = (

        r"={5,}\s*"

        + re.escape(
            section_name.upper()
        )

        + r"\s*={5,}"

        r"(.*?)(?=\n={5,}|\Z)"
    )

    match = re.search(
        pattern,
        text,
        re.DOTALL | re.IGNORECASE
    )

    if match:

        return match.group(1).strip()

    return None


# ============================================================
# SPLIT SECTION INTO LINES
# ============================================================

def clean_lines(text):

    if not text:
        return []

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if line:
            lines.append(line)

    return lines


# ============================================================
# SECTION → LIST
# ============================================================

def section_to_list(text):

    if not text:
        return []

    return clean_lines(text)


# ============================================================
# BUILD JSON
# ============================================================

def build_resume_json(section_text):

    data = deepcopy(
        BLUEPRINT
    )

    # ========================================================
    # HEADER
    # ========================================================

    header = get_section(
        section_text,
        "header"
    )

    if header:

        data[
            "personal_information"
        ][
            "name"
        ] = extract_name(
            header
        )

        data[
            "personal_information"
        ][
            "email"
        ] = extract_email(
            header
        )

        data[
            "personal_information"
        ][
            "phone"
        ] = extract_phone(
            header
        )

        data[
            "personal_information"
        ][
            "linkedin"
        ] = extract_linkedin(
            header
        )

        data[
            "personal_information"
        ][
            "github"
        ] = extract_github(
            header
        )

        data[
            "personal_information"
        ][
            "portfolio"
        ] = extract_portfolio(
            header
        )

    # ========================================================
    # PHOTO / IMAGES
    #
    # Search ENTIRE section file.
    # This is outside the header block intentionally.
    # ========================================================

    image_paths = extract_image_paths(
        section_text
    )

    if image_paths:

        # Primary photo
        data[
            "personal_information"
        ][
            "photo"
        ] = image_paths[0]

        # Preserve additional images if present
        if len(image_paths) > 1:

            data[
                "personal_information"
            ][
                "images"
            ] = image_paths

        print(
            f"  Photo/Image found: "
            f"{', '.join(image_paths)}"
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    summary = get_section(
        section_text,
        "summary"
    )

    if summary:

        data[
            "summary"
        ] = summary

    # ========================================================
    # EDUCATION
    # ========================================================

    education = get_section(
        section_text,
        "education"
    )

    if education:

        data[
            "education"
        ] = section_to_list(
            education
        )

    # ========================================================
    # EXPERIENCE
    # ========================================================

    experience = get_section(
        section_text,
        "experience"
    )

    if experience:

        data[
            "experience"
        ] = section_to_list(
            experience
        )

    # ========================================================
    # SKILLS
    # ========================================================

    skills = get_section(
        section_text,
        "skills"
    )

    if skills:

        data[
            "skills"
        ][
            "technical"
        ] = section_to_list(
            skills
        )

    # ========================================================
    # PROJECTS
    # ========================================================

    projects = get_section(
        section_text,
        "projects"
    )

    if projects:

        data[
            "projects"
        ] = section_to_list(
            projects
        )

    # ========================================================
    # CERTIFICATIONS
    # ========================================================

    certifications = get_section(
        section_text,
        "certifications"
    )

    if certifications:

        data[
            "certifications"
        ] = section_to_list(
            certifications
        )

    # ========================================================
    # ACHIEVEMENTS
    # ========================================================

    achievements = get_section(
        section_text,
        "achievements"
    )

    if achievements:

        data[
            "achievements"
        ] = section_to_list(
            achievements
        )

    # ========================================================
    # LANGUAGES
    # ========================================================

    languages = get_section(
        section_text,
        "languages"
    )

    if languages:

        data[
            "languages"
        ] = section_to_list(
            languages
        )

    # ========================================================
    # LEADERSHIP
    # ========================================================

    leadership = get_section(
        section_text,
        "leadership"
    )

    if leadership:

        data[
            "leadership"
        ] = section_to_list(
            leadership
        )

    # ========================================================
    # PUBLICATIONS
    # ========================================================

    publications = get_section(
        section_text,
        "publications"
    )

    if publications:

        data[
            "publications"
        ] = section_to_list(
            publications
        )

    # ========================================================
    # AFFILIATIONS
    # ========================================================

    affiliations = get_section(
        section_text,
        "affiliations"
    )

    if affiliations:

        data[
            "affiliations"
        ] = section_to_list(
            affiliations
        )

    # ========================================================
    # MILITARY EXPERIENCE
    # ========================================================

    military = get_section(
        section_text,
        "military_experience"
    )

    if military:

        data[
            "military_experience"
        ] = section_to_list(
            military
        )

    # ========================================================
    # TRAINING
    # ========================================================

    training = get_section(
        section_text,
        "training"
    )

    if training:

        data[
            "training"
        ] = section_to_list(
            training
        )

    # ========================================================
    # COURSEWORK
    # ========================================================

    coursework = get_section(
        section_text,
        "coursework"
    )

    if coursework:

        data[
            "coursework"
        ] = section_to_list(
            coursework
        )

    return data


# ============================================================
# PROCESS ALL RESUMES
# ============================================================

def main():

    files = sorted(
        INPUT_DIR.glob(
            "*_sections.txt"
        ),
        key=lambda x: x.name.lower()
    )

    print("=" * 70)
    print("JSON GENERATOR")
    print("=" * 70)

    print(
        f"\nSection files found: "
        f"{len(files)}"
    )

    if not files:

        print(
            "\nERROR: No section files found."
        )

        print(
            f"Check folder: "
            f"{INPUT_DIR.resolve()}"
        )

        return

    successful = 0

    for file in files:

        print()
        print("-" * 70)

        print(
            f"Processing: "
            f"{file.name}"
        )

        try:

            text = file.read_text(
                encoding="utf-8"
            )

            data = build_resume_json(
                text
            )

            output_name = (
                file.stem.replace(
                    "_sections",
                    ""
                )
                + ".json"
            )

            output_file = (
                OUTPUT_DIR /
                output_name
            )

            with open(
                output_file,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    data,
                    f,
                    indent=4,
                    ensure_ascii=False
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
    print("JSON GENERATION COMPLETE")
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
# RUN
# ============================================================

if __name__ == "__main__":
    main()