import json
import re
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_DIR = Path("final_json")
OUTPUT_FILE = Path("global_entities.json")


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_name(value):

    if not value:
        return None

    value = str(value)

    # Remove zero-width characters
    value = value.replace("\u200b", "")
    value = value.replace("\ufeff", "")

    # Normalize whitespace
    value = re.sub(r"\s+", " ", value)

    # Remove unnecessary punctuation at ends
    value = value.strip(" ,.;:-")

    return value.strip()


def entity_key(value):

    """
    Used only for comparison/deduplication.

    Example:
        Python
        python
        PYTHON

    become the same key.
    """

    if not value:
        return None

    value = normalize_name(value)

    if not value:
        return None

    return value.lower()


# ============================================================
# ENTITY STORE
# ============================================================

ENTITY_TYPES = [

    "persons",
    "companies",
    "institutions",
    "skills",
    "technologies",
    "job_roles",
    "projects",
    "degrees",
    "certifications",
    "languages",
    "organizations",
    "locations"
]


entities = {
    entity_type: {}
    for entity_type in ENTITY_TYPES
}


# ============================================================
# ADD ENTITY
# ============================================================

def add_entity(
    entity_type,
    name,
    resume_id,
    extra=None
):

    name = normalize_name(name)

    if not name:
        return

    key = entity_key(name)

    if not key:
        return

    if key not in entities[entity_type]:

        entities[entity_type][key] = {

            "id": f"{entity_type[:-1]}_{len(entities[entity_type]) + 1}",

            "name": name,

            "source_resumes": [],

            "properties": {}
        }

    entity = entities[entity_type][key]

    if resume_id not in entity["source_resumes"]:

        entity["source_resumes"].append(
            resume_id
        )

    if extra:

        for property_name, value in extra.items():

            if value is not None:

                entity["properties"][
                    property_name
                ] = value


# ============================================================
# EXTRACT PERSON
# ============================================================

def extract_person(data, resume_id):

    personal = data.get(
        "personal_information",
        {}
    )

    name = personal.get("name")

    if name:

        add_entity(
            "persons",
            name,
            resume_id,
            {
                "email": personal.get("email"),
                "phone": personal.get("phone"),
                "linkedin": personal.get("linkedin"),
                "github": personal.get("github")
            }
        )


# ============================================================
# EXTRACT EDUCATION
# ============================================================

def extract_education(
    data,
    resume_id
):

    education_list = data.get(
        "education",
        []
    )

    if not isinstance(
        education_list,
        list
    ):
        return

    for education in education_list:

        if not isinstance(
            education,
            dict
        ):
            continue

        institution = education.get(
            "institution"
        )

        degree = education.get(
            "degree"
        )

        location = education.get(
            "location"
        )

        # ----------------------------------------------------
        # Institution
        # ----------------------------------------------------

        if institution:

            add_entity(
                "institutions",
                institution,
                resume_id,
                {
                    "location": location
                }
            )

        # ----------------------------------------------------
        # Degree
        # ----------------------------------------------------

        if degree:

            add_entity(
                "degrees",
                degree,
                resume_id
            )

        # ----------------------------------------------------
        # Location
        # ----------------------------------------------------

        if location:

            add_entity(
                "locations",
                location,
                resume_id
            )


# ============================================================
# EXTRACT EXPERIENCE
# ============================================================

def extract_experience(
    data,
    resume_id
):

    experience_list = data.get(
        "experience",
        []
    )

    if not isinstance(
        experience_list,
        list
    ):
        return

    for experience in experience_list:

        if not isinstance(
            experience,
            dict
        ):
            continue

        company = experience.get(
            "company"
        )

        role = experience.get(
            "job_title"
        )

        location = experience.get(
            "location"
        )

        # ----------------------------------------------------
        # Company
        # ----------------------------------------------------

        if company:

            add_entity(
                "companies",
                company,
                resume_id,
                {
                    "location": location
                }
            )

        # ----------------------------------------------------
        # Job role
        # ----------------------------------------------------

        if role:

            add_entity(
                "job_roles",
                role,
                resume_id
            )

        # ----------------------------------------------------
        # Location
        # ----------------------------------------------------

        if location:

            add_entity(
                "locations",
                location,
                resume_id
            )


# ============================================================
# EXTRACT SKILLS
# ============================================================

def extract_skills(
    data,
    resume_id
):

    skills = data.get(
        "skills",
        {}
    )

    if not isinstance(
        skills,
        dict
    ):
        return

    skill_categories = [

        "programming_languages",

        "frameworks",

        "databases",

        "tools",

        "cloud",

        "soft_skills"
    ]

    for category in skill_categories:

        skill_list = skills.get(
            category,
            []
        )

        if not isinstance(
            skill_list,
            list
        ):
            continue

        for skill in skill_list:

            if not skill:
                continue

            # Programming languages, frameworks,
            # databases, tools, cloud and soft skills
            # are all globally searchable skills.

            add_entity(
                "skills",
                skill,
                resume_id,
                {
                    "category": category
                }
            )


# ============================================================
# EXTRACT PROJECTS
# ============================================================

def extract_projects(
    data,
    resume_id
):

    projects = data.get(
        "projects",
        []
    )

    if not isinstance(
        projects,
        list
    ):
        return

    for project in projects:

        if not isinstance(
            project,
            dict
        ):
            continue

        name = project.get(
            "name"
        )

        description = project.get(
            "description"
        )

        technologies = project.get(
            "technologies",
            []
        )

        # ----------------------------------------------------
        # Project entity
        # ----------------------------------------------------

        if name:

            add_entity(
                "projects",
                name,
                resume_id,
                {
                    "description": description
                }
            )

        # ----------------------------------------------------
        # Technologies
        # ----------------------------------------------------

        if isinstance(
            technologies,
            list
        ):

            for technology in technologies:

                add_entity(
                    "technologies",
                    technology,
                    resume_id
                )


# ============================================================
# EXTRACT CERTIFICATIONS
# ============================================================

def extract_certifications(
    data,
    resume_id
):

    certifications = data.get(
        "certifications",
        []
    )

    if not isinstance(
        certifications,
        list
    ):
        return

    for certification in certifications:

        add_entity(
            "certifications",
            certification,
            resume_id
        )


# ============================================================
# EXTRACT LANGUAGES
# ============================================================

def extract_languages(
    data,
    resume_id
):

    languages = data.get(
        "languages",
        []
    )

    if not isinstance(
        languages,
        list
    ):
        return

    for language in languages:

        add_entity(
            "languages",
            language,
            resume_id
        )


# ============================================================
# EXTRACT OTHER ORGANIZATIONS
# ============================================================

def extract_organizations(
    data,
    resume_id
):

    affiliations = data.get(
        "affiliations",
        []
    )

    if not isinstance(
        affiliations,
        list
    ):
        return

    for affiliation in affiliations:

        add_entity(
            "organizations",
            affiliation,
            resume_id
        )


# ============================================================
# EXTRACT ALL ENTITIES FROM ONE RESUME
# ============================================================

def process_resume(
    file_path
):

    resume_id = file_path.stem

    print(
        f"Processing: {file_path.name}"
    )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    extract_person(
        data,
        resume_id
    )

    extract_education(
        data,
        resume_id
    )

    extract_experience(
        data,
        resume_id
    )

    extract_skills(
        data,
        resume_id
    )

    extract_projects(
        data,
        resume_id
    )

    extract_certifications(
        data,
        resume_id
    )

    extract_languages(
        data,
        resume_id
    )

    extract_organizations(
        data,
        resume_id
    )


# ============================================================
# CONVERT DICTIONARIES TO LISTS
# ============================================================

def finalize_entities():

    result = {}

    for entity_type in ENTITY_TYPES:

        result[entity_type] = list(
            entities[
                entity_type
            ].values()
        )

    return result


# ============================================================
# STATISTICS
# ============================================================

def print_statistics(
    final_entities
):

    print("\n")
    print("=" * 70)
    print("GLOBAL ENTITY STATISTICS")
    print("=" * 70)

    for entity_type, entity_list in final_entities.items():

        print(
            f"{entity_type:25} : "
            f"{len(entity_list)}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("GLOBAL ENTITY EXTRACTION")
    print("=" * 70)

    files = list(
        INPUT_DIR.glob("*.json")
    )

    print(
        f"\nBlueprint JSON files found: "
        f"{len(files)}\n"
    )

    if not files:

        print(
            "ERROR: No files found in:"
        )

        print(
            INPUT_DIR.resolve()
        )

        return

    # --------------------------------------------------------
    # Process all resumes
    # --------------------------------------------------------

    for file in files:

        try:

            process_resume(
                file
            )

            print(
                "  OK"
            )

        except Exception as e:

            print(
                f"  ERROR: {e}"
            )

    # --------------------------------------------------------
    # Finalize
    # --------------------------------------------------------

    final_entities = finalize_entities()

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    print_statistics(
        final_entities
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output = {

        "entity_model": {

            "description":
                "Global entities extracted from resume Blueprint JSONs.",

            "entity_types":
                ENTITY_TYPES
        },

        "entities":
            final_entities
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=4,
            ensure_ascii=False
        )

    print("\n")
    print("=" * 70)
    print("GLOBAL ENTITY EXTRACTION COMPLETE")
    print("=" * 70)

    print(
        f"\nSaved to: "
        f"{OUTPUT_FILE.resolve()}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()