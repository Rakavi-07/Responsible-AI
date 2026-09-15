import json
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_DIR = Path("final_json")
OUTPUT_FILE = Path("graph_data.json")


# ============================================================
# GLOBAL GRAPH STORAGE
# ============================================================

nodes = {}
relationships = []


# ============================================================
# ID NORMALIZATION
# ============================================================

def normalize(value):

    if value is None:
        return ""

    return " ".join(
        str(value).strip().lower().split()
    )


def make_id(label, value):

    normalized = normalize(value)

    safe_value = "".join(
        c if c.isalnum() else "_"
        for c in normalized
    )

    safe_value = "_".join(
        x for x in safe_value.split("_")
        if x
    )

    return f"{label.lower()}_{safe_value}"


# ============================================================
# ADD NODE
# ============================================================

def add_node(
    label,
    name,
    properties=None
):

    if not name:
        return None

    node_id = make_id(
        label,
        name
    )

    if node_id not in nodes:

        node = {

            "id": node_id,

            "label": label,

            "properties": {

                "name": str(name).strip()
            }
        }

        if properties:

            for key, value in properties.items():

                if value is not None:

                    node["properties"][key] = value

        nodes[node_id] = node

    else:

        # Add any new properties to existing node
        if properties:

            for key, value in properties.items():

                if value is not None:

                    nodes[node_id][
                        "properties"
                    ][key] = value

    return node_id


# ============================================================
# ADD RELATIONSHIP
# ============================================================

def add_relationship(
    source,
    relationship_type,
    target,
    properties=None
):

    if not source or not target:
        return

    relationship = {

        "source": source,

        "type": relationship_type,

        "target": target
    }

    if properties:

        relationship["properties"] = properties

    relationships.append(
        relationship
    )


# ============================================================
# PROCESS PERSONAL INFORMATION
# ============================================================

def process_person(
    data,
    resume_id
):

    personal = data.get(
        "personal_information",
        {}
    )

    name = personal.get(
        "name"
    )

    if not name:

        # If no name was extracted,
        # create a resume-level identifier
        name = f"Unknown Candidate {resume_id}"

    person_id = add_node(

        "Person",

        name,

        {
            "email": personal.get("email"),

            "phone": personal.get("phone"),

            "linkedin": personal.get("linkedin"),

            "github": personal.get("github"),

            "portfolio": personal.get("portfolio")
        }
    )

    return person_id


# ============================================================
# PROCESS EDUCATION
# ============================================================

def process_education(
    data,
    person_id
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

    for index, education in enumerate(
        education_list
    ):

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

        field = education.get(
            "field_of_study"
        )

        # ----------------------------------------------------
        # Education node
        # ----------------------------------------------------

        education_name = (
            f"{institution or 'Unknown Institution'} "
            f"{degree or ''} "
            f"{field or ''}"
        ).strip()

        education_id = add_node(

            "Education",

            education_name,

            {
                "institution": institution,

                "degree": degree,

                "field_of_study": field,

                "start_date":
                    education.get(
                        "start_date"
                    ),

                "end_date":
                    education.get(
                        "end_date"
                    ),

                "graduation_year":
                    education.get(
                        "graduation_year"
                    ),

                "cgpa":
                    education.get(
                        "cgpa"
                    )
            }
        )

        add_relationship(

            person_id,

            "HAS_EDUCATION",

            education_id
        )

        # ----------------------------------------------------
        # Institution
        # ----------------------------------------------------

        if institution:

            institution_id = add_node(

                "Institution",

                institution
            )

            add_relationship(

                person_id,

                "STUDIED_AT",

                institution_id
            )

            add_relationship(

                education_id,

                "AT_INSTITUTION",

                institution_id
            )

        # ----------------------------------------------------
        # Degree
        # ----------------------------------------------------

        if degree:

            degree_id = add_node(

                "Degree",

                degree
            )

            add_relationship(

                education_id,

                "HAS_DEGREE",

                degree_id
            )


# ============================================================
# PROCESS EXPERIENCE
# ============================================================

def process_experience(
    data,
    person_id
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

        # ----------------------------------------------------
        # Experience node
        # ----------------------------------------------------

        experience_name = (
            f"{company or 'Unknown Company'} "
            f"{role or ''}"
        ).strip()

        experience_id = add_node(

            "Experience",

            experience_name,

            {
                "start_date":
                    experience.get(
                        "start_date"
                    ),

                "end_date":
                    experience.get(
                        "end_date"
                    ),

                "location":
                    experience.get(
                        "location"
                    ),

                "responsibilities":
                    experience.get(
                        "responsibilities",
                        []
                    ),

                "achievements":
                    experience.get(
                        "achievements",
                        []
                    )
            }
        )

        add_relationship(

            person_id,

            "HAS_EXPERIENCE",

            experience_id
        )

        # ----------------------------------------------------
        # Company
        # ----------------------------------------------------

        if company:

            company_id = add_node(

                "Company",

                company
            )

            add_relationship(

                person_id,

                "WORKED_AT",

                company_id
            )

            add_relationship(

                experience_id,

                "AT_COMPANY",

                company_id
            )

        # ----------------------------------------------------
        # Job Role
        # ----------------------------------------------------

        if role:

            role_id = add_node(

                "JobRole",

                role
            )

            add_relationship(

                experience_id,

                "HAS_ROLE",

                role_id
            )


# ============================================================
# PROCESS SKILLS
# ============================================================

def process_skills(
    data,
    person_id
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

    categories = [

        "programming_languages",

        "frameworks",

        "databases",

        "tools",

        "cloud",

        "soft_skills"
    ]

    for category in categories:

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

            skill_id = add_node(

                "Skill",

                skill,

                {
                    "category": category
                }
            )

            add_relationship(

                person_id,

                "HAS_SKILL",

                skill_id,

                {
                    "category": category
                }
            )


# ============================================================
# PROCESS PROJECTS
# ============================================================

def process_projects(
    data,
    person_id
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

        if not name:
            continue

        project_id = add_node(

            "Project",

            name,

            {
                "description":
                    project.get(
                        "description",
                        []
                    ),

                "achievements":
                    project.get(
                        "achievements",
                        []
                    )
            }
        )

        add_relationship(

            person_id,

            "WORKED_ON",

            project_id
        )

        # ----------------------------------------------------
        # Technologies
        # ----------------------------------------------------

        technologies = project.get(
            "technologies",
            []
        )

        if isinstance(
            technologies,
            list
        ):

            for technology in technologies:

                if not technology:
                    continue

                technology_id = add_node(

                    "Technology",

                    technology
                )

                add_relationship(

                    project_id,

                    "USES_TECHNOLOGY",

                    technology_id
                )

                # A technology is also a skill
                skill_id = add_node(

                    "Skill",

                    technology,

                    {
                        "source":
                            "project_technology"
                    }
                )

                add_relationship(

                    person_id,

                    "HAS_SKILL",

                    skill_id
                )


# ============================================================
# PROCESS CERTIFICATIONS
# ============================================================

def process_certifications(
    data,
    person_id
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

        if not certification:
            continue

        certification_id = add_node(

            "Certification",

            certification
        )

        add_relationship(

            person_id,

            "HAS_CERTIFICATION",

            certification_id
        )


# ============================================================
# PROCESS ACHIEVEMENTS
# ============================================================

def process_achievements(
    data,
    person_id
):

    achievements = data.get(
        "achievements",
        []
    )

    if not isinstance(
        achievements,
        list
    ):
        return

    for achievement in achievements:

        if not achievement:
            continue

        achievement_id = add_node(

            "Achievement",

            achievement
        )

        add_relationship(

            person_id,

            "HAS_ACHIEVEMENT",

            achievement_id
        )


# ============================================================
# PROCESS LANGUAGES
# ============================================================

def process_languages(
    data,
    person_id
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

        if not language:
            continue

        language_id = add_node(

            "Language",

            language
        )

        add_relationship(

            person_id,

            "SPEAKS",

            language_id
        )


# ============================================================
# PROCESS LEADERSHIP
# ============================================================

def process_leadership(
    data,
    person_id
):

    leadership = data.get(
        "leadership",
        []
    )

    if not isinstance(
        leadership,
        list
    ):
        return

    for item in leadership:

        if not item:
            continue

        leadership_id = add_node(

            "LeadershipExperience",

            item
        )

        add_relationship(

            person_id,

            "HAS_LEADERSHIP_EXPERIENCE",

            leadership_id
        )


# ============================================================
# PROCESS AFFILIATIONS
# ============================================================

def process_affiliations(
    data,
    person_id
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

        if not affiliation:
            continue

        organization_id = add_node(

            "Organization",

            affiliation
        )

        add_relationship(

            person_id,

            "MEMBER_OF",

            organization_id
        )


# ============================================================
# PROCESS MILITARY EXPERIENCE
# ============================================================

def process_military(
    data,
    person_id
):

    military = data.get(
        "military_experience",
        []
    )

    if not isinstance(
        military,
        list
    ):
        return

    for item in military:

        if not item:
            continue

        military_id = add_node(

            "MilitaryExperience",

            item
        )

        add_relationship(

            person_id,

            "HAS_MILITARY_EXPERIENCE",

            military_id
        )


# ============================================================
# PROCESS TRAINING
# ============================================================

def process_training(
    data,
    person_id
):

    training = data.get(
        "training",
        []
    )

    if not isinstance(
        training,
        list
    ):
        return

    for item in training:

        if not item:
            continue

        training_id = add_node(

            "Training",

            item
        )

        add_relationship(

            person_id,

            "COMPLETED_TRAINING",

            training_id
        )


# ============================================================
# PROCESS PUBLICATIONS
# ============================================================

def process_publications(
    data,
    person_id
):

    publications = data.get(
        "publications",
        []
    )

    if not isinstance(
        publications,
        list
    ):
        return

    for publication in publications:

        if not publication:
            continue

        publication_id = add_node(

            "Publication",

            publication
        )

        add_relationship(

            person_id,

            "AUTHORED",

            publication_id
        )


# ============================================================
# PROCESS COURSEWORK
# ============================================================

def process_coursework(
    data,
    person_id
):

    coursework = data.get(
        "coursework",
        []
    )

    if not isinstance(
        coursework,
        list
    ):
        return

    for course in coursework:

        if not course:
            continue

        # Coursework may contain multiple
        # subjects separated by commas.
        subjects = [
            x.strip()
            for x in course.split(",")
            if x.strip()
        ]

        for subject in subjects:

            course_id = add_node(

                "Course",

                subject
            )

            add_relationship(

                person_id,

                "COMPLETED_COURSE",

                course_id
            )


# ============================================================
# PROCESS ONE RESUME
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

    person_id = process_person(
        data,
        resume_id
    )

    process_education(
        data,
        person_id
    )

    process_experience(
        data,
        person_id
    )

    process_skills(
        data,
        person_id
    )

    process_projects(
        data,
        person_id
    )

    process_certifications(
        data,
        person_id
    )

    process_achievements(
        data,
        person_id
    )

    process_languages(
        data,
        person_id
    )

    process_leadership(
        data,
        person_id
    )

    process_affiliations(
        data,
        person_id
    )

    process_military(
        data,
        person_id
    )

    process_training(
        data,
        person_id
    )

    process_publications(
        data,
        person_id
    )

    process_coursework(
        data,
        person_id
    )


# ============================================================
# REMOVE DUPLICATE RELATIONSHIPS
# ============================================================

def deduplicate_relationships():

    unique = []

    seen = set()

    for relationship in relationships:

        properties = json.dumps(
            relationship.get(
                "properties",
                {}
            ),
            sort_keys=True
        )

        key = (

            relationship["source"],

            relationship["type"],

            relationship["target"],

            properties
        )

        if key not in seen:

            seen.add(key)

            unique.append(
                relationship
            )

    return unique


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("GRAPH BUILDER")
    print("=" * 70)

    files = list(
        INPUT_DIR.glob("*.json")
    )

    print(
        f"\nBlueprint files found: "
        f"{len(files)}\n"
    )

    if not files:

        print(
            "ERROR: No JSON files found."
        )

        print(
            f"Expected directory: "
            f"{INPUT_DIR.resolve()}"
        )

        return

    # --------------------------------------------------------
    # Process resumes
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
    # Remove duplicate relationships
    # --------------------------------------------------------

    final_relationships = (
        deduplicate_relationships()
    )

    # --------------------------------------------------------
    # Create final graph object
    # --------------------------------------------------------

    graph = {

        "graph_schema": {

            "description":
                "Knowledge graph generated from the canonical resume Blueprint.",

            "node_labels": sorted(
                list(
                    set(
                        node["label"]
                        for node in nodes.values()
                    )
                )
            ),

            "relationship_types": sorted(
                list(
                    set(
                        relationship["type"]
                        for relationship
                        in final_relationships
                    )
                )
            )
        },

        "nodes": list(
            nodes.values()
        ),

        "relationships":
            final_relationships
    }

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            graph,
            f,
            indent=4,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("GRAPH STATISTICS")
    print("=" * 70)

    print(
        f"Nodes         : {len(nodes)}"
    )

    print(
        f"Relationships  : "
        f"{len(final_relationships)}"
    )

    print(
        f"Output         : "
        f"{OUTPUT_FILE.resolve()}"
    )

    print("\n")
    print("=" * 70)
    print("GRAPH BUILD COMPLETE")
    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()