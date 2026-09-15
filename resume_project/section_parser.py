import re
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

INPUT_DIR = Path("extracted")
OUTPUT_DIR = Path("sections")

OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# CANONICAL SECTION BLUEPRINT
# ============================================================
# Different resumes use different headings for the same section.
# We map all of them to one canonical section name.

SECTION_ALIASES = {

    "summary": [
        "SUMMARY",
        "PROFESSIONAL SUMMARY",
        "CAREER SUMMARY",
        "OBJECTIVE",
        "CAREER OBJECTIVE",
        "PROFESSIONAL OBJECTIVE",
        "QUALIFICATION SUMMARY",
        "SUMMARY OF QUALIFICATIONS",
        "CAREER FOCUS",
        "CAREER TARGET",
        "PROFESSIONAL PROFILE",
        "PROFILE",
        "CAREER PROFILE"
    ],

    "education": [
        "EDUCATION",
        "EDUCATION AND CREDENTIALS",
        "EDUCATION & CREDENTIALS",
        "EDUCATION/CREDENTIALS",
        "EDUCATION AND CERTIFICATION",
        "EDUCATION AND CERTIFICATIONS",
        "EDUCATION/CERTIFICATION",
        "EDUCATION/CERTIFICATIONS",

        # Handles typo found in one of the resumes
        "ENDUCATION AND CERTIFICATION",
        "ENDUCATION AND CERTIFICATIONS",
        "ENDUCATION AND CREDENTIALS"
    ],

    "experience": [
        "EXPERIENCE",
        "PROFESSIONAL EXPERIENCE",
        "PROFESSIONAL EXPERIENCE:",
        "WORK EXPERIENCE",
        "EMPLOYMENT EXPERIENCE",
        "EMPLOYMENT HISTORY",
        "WORK HISTORY",
        "CAREER HISTORY"
    ],

    "skills": [
        "SKILLS",
        "TECHNICAL SKILLS",
        "TECHNICAL PROFICIENCIES",
        "TECHNICAL PROFICIENCY",
        "CORE SKILLS",
        "CORE SKILL AREAS",
        "CORE STRENGTHS",
        "AREAS OF EXPERTISE",
        "KEY SKILLS",
        "KEY VALUE-OFFERED QUALIFICATIONS",
        "COMPETENCIES",
        "CORE COMPETENCIES",
        "AREAS OF STRENGTH"
    ],

    "projects": [
        "PROJECTS",
        "PROJECT EXPERIENCE",
        "ACADEMIC PROJECTS",
        "PERSONAL PROJECTS",
        "KEY PROJECTS"
    ],

    "certifications": [
        "CERTIFICATIONS",
        "CERTIFICATION",
        "CERTIFICATIONS & ACHIEVEMENTS",
        "CERTIFICATIONS AND ACHIEVEMENTS",
        "CERTIFICATIONS, LICENSES & DESIGNATIONS",
        "CERTIFICATIONS, LICENSES AND DESIGNATIONS",
        "LICENSES AND CERTIFICATIONS",
        "LICENSES & CERTIFICATIONS"
    ],

    "achievements": [
        "ACHIEVEMENTS",
        "AWARDS",
        "AWARDS & ACHIEVEMENTS",
        "AWARDS AND ACHIEVEMENTS",
        "HONORS",
        "HONORS & AWARDS",
        "HONORS AND AWARDS"
    ],

    "languages": [
        "LANGUAGES",
        "LANGUAGE",
        "LANGUAGE SKILLS"
    ],

    "leadership": [
        "LEADERSHIP",
        "LEADERSHIP EXPERIENCE",
        "LEADERSHIP & INVOLVEMENT",
        "CAMPUS INVOLVEMENT",
        "LEADERSHIP AND CAMPUS INVOLVEMENT"
    ],

    "publications": [
        "PUBLICATIONS",
        "PUBLICATION",
        "RESEARCH PUBLICATIONS"
    ],

    "affiliations": [
        "AFFILIATIONS",
        "PROFESSIONAL AFFILIATIONS",
        "MEMBERSHIPS",
        "PROFESSIONAL MEMBERSHIPS",
        "ASSOCIATIONS"
    ],

    "military_experience": [
        "MILITARY EXPERIENCE",
        "MILITARY SERVICE",
        "MILITARY HISTORY",
        "MILITARY BACKGROUND"
    ],

    "training": [
        "TRAINING",
        "PROFESSIONAL DEVELOPMENT",
        "TRAINING & DEVELOPMENT",
        "PROFESSIONAL TRAINING"
    ],

    "coursework": [
        "COURSEWORK",
        "RELEVANT COURSEWORK",
        "RELEVANT COURSES"
    ]
}


# ============================================================
# CREATE REVERSE LOOKUP
# ============================================================

HEADING_TO_SECTION = {}

for section, headings in SECTION_ALIASES.items():

    for heading in headings:

        normalized_heading = heading.upper().strip()

        HEADING_TO_SECTION[normalized_heading] = section


# ============================================================
# NORMALIZE A LINE
# ============================================================

def normalize_line(line):

    line = line.strip()

    # Preserve image path exactly
    if line.startswith("[IMAGE:") and line.endswith("]"):
        return line

    # Remove common bullet characters
    line = re.sub(
        r"^[•●▪■□◆◇◦\-*]+\s*",
        "",
        line
    )

    # Replace multiple spaces with one
    line = re.sub(r"\s+", " ", line)

    return line.strip()


# ============================================================
# DETECT SECTION HEADING
# ============================================================

def detect_heading(line):

    cleaned = normalize_line(line)

    if not cleaned:
        return None

    upper = cleaned.upper()

    # --------------------------------------------------------
    # Exact heading match
    # --------------------------------------------------------

    if upper in HEADING_TO_SECTION:
        return HEADING_TO_SECTION[upper]

    # --------------------------------------------------------
    # Remove trailing colon
    # --------------------------------------------------------

    without_colon = upper.rstrip(" :")

    if without_colon in HEADING_TO_SECTION:
        return HEADING_TO_SECTION[without_colon]

    # --------------------------------------------------------
    # Some PDF extraction creates weird spacing
    # --------------------------------------------------------

    compact = re.sub(r"\s+", " ", without_colon)

    if compact in HEADING_TO_SECTION:
        return HEADING_TO_SECTION[compact]

    return None


# ============================================================
# PARSE SECTIONS
# ============================================================

def parse_sections(text):

    sections = {}

    current_section = "header"

    sections[current_section] = []

    lines = text.splitlines()

    for line in lines:

        cleaned = normalize_line(line)

        if not cleaned:
            continue

        # Check whether this line is a section heading
        detected_section = detect_heading(cleaned)

        if detected_section:

            current_section = detected_section

            # Avoid overwriting an already existing section
            if current_section not in sections:
                sections[current_section] = []

            continue

        # Add normal content to current section
        sections[current_section].append(cleaned)

    # --------------------------------------------------------
    # Convert lists to strings
    # --------------------------------------------------------

    final_sections = {}

    for section, content in sections.items():

        cleaned_content = []

        for line in content:

            if line.strip():
                cleaned_content.append(line.strip())

        if cleaned_content:

            final_sections[section] = "\n".join(cleaned_content)

    return final_sections


# ============================================================
# SAVE PARSED SECTIONS
# ============================================================

def save_sections(output_file, sections):

    with output_file.open(
        "w",
        encoding="utf-8"
    ) as f:

        for section, content in sections.items():

            f.write("\n")
            f.write("=" * 70)
            f.write("\n")

            f.write(section.upper())
            f.write("\n")

            f.write("=" * 70)
            f.write("\n")

            f.write(content)
            f.write("\n")


# ============================================================
# MAIN PROCESSING
# ============================================================

def main():

    txt_files = list(INPUT_DIR.glob("*.txt"))

    print("=" * 70)
    print("RESUME SECTION PARSER")
    print("=" * 70)

    print(f"\nInput folder : {INPUT_DIR}")
    print(f"Output folder: {OUTPUT_DIR}")
    print(f"Files found  : {len(txt_files)}\n")

    if not txt_files:

        print("ERROR: No TXT files found.")
        print()
        print("Make sure you have already run:")
        print("    python extract.py")
        return

    successful = 0

    for txt_file in txt_files:

        print("-" * 70)
        print(f"Processing: {txt_file.name}")

        try:

            # Read extracted text
            text = txt_file.read_text(
                encoding="utf-8"
            )

            # Parse sections
            sections = parse_sections(text)

            # Output filename
            output_file = (
                OUTPUT_DIR /
                f"{txt_file.stem}_sections.txt"
            )

            # Save
            save_sections(
                output_file,
                sections
            )

            # Display result
            print(
                f"  Sections detected: "
                f"{list(sections.keys())}"
            )

            print(
                f"  Saved: {output_file.name}"
            )

            successful += 1

        except Exception as e:

            print(
                f"  ERROR processing file: {e}"
            )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("\n")
    print("=" * 70)
    print("SECTION PARSING COMPLETE")
    print("=" * 70)

    print(f"Successfully processed: {successful}/{len(txt_files)}")
    print(f"Output directory: {OUTPUT_DIR}")


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()