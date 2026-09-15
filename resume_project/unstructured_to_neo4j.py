import os
import re
from neo4j import GraphDatabase


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_DIR = "extracted"

NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Kavi@0607"
NEO4J_DATABASE = "neo4j"


# ============================================================
# EMPLOYEES FROM MYSQL
# These names are used to connect resume data to Employee nodes
# ============================================================

EMPLOYEE_NAMES = [
    "Jennifer Hall",
    "ARYAN SHARMA",
    "JAISAL RATHI",
    "Lucy Harding",
    "Varad Singhal",
    "JACOB J. JACOBY",
    "VINCE D. CONLAN",
    "RICHARD A. LEVINSON",
    "DAVID H. ANDERS",
    "GEORGE REDMOND"
]


# ============================================================
# SKILLS
# We look for these skills inside the resume text
# ============================================================

SKILLS = [
    "Python",
    "Java",
    "C",
    "C++",
    "SQL",
    "AWS",
    "Azure",
    "Docker",
    "Kubernetes",
    "Git",
    "REST",
    "React",
    "Node.js",
    "Flutter",
    "Firebase",
    "Machine Learning",
    "Artificial Intelligence",
    "Data Engineering",
    "Cloud Computing",
    "Project Management",
    "Leadership",
    "Communication",
    "Customer Service",
    "Quality Assurance",
    "Six Sigma",
    "Lean",
    "Automation",
    "Logistics",
    "Sales",
    "Marketing",
    "Negotiation"
]


# ============================================================
# CERTIFICATIONS
# Words/phrases that commonly indicate certifications
# ============================================================

CERTIFICATION_KEYWORDS = [
    "certified",
    "certification",
    "certificate",
    "aws certified",
    "six sigma",
    "lean six sigma",
    "professional certification",
    "license",
    "licensed"
]


# ============================================================
# CREATE NEO4J DRIVER
# ============================================================

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

print("Connected to Neo4j")


# ============================================================
# FIND EMPLOYEE NAME IN RESUME
# ============================================================

def find_employee_name(text):

    text_lower = text.lower()

    for name in EMPLOYEE_NAMES:

        if name.lower() in text_lower:
            return name

    return None


# ============================================================
# EXTRACT SKILLS
# ============================================================

def extract_skills(text):

    found_skills = []

    text_lower = text.lower()

    for skill in SKILLS:

        if skill.lower() in text_lower:

            if skill not in found_skills:
                found_skills.append(skill)

    return found_skills


# ============================================================
# EXTRACT CERTIFICATIONS
# ============================================================

def extract_certifications(text):

    certifications = []

    lines = text.splitlines()

    inside_certification_section = False

    for line in lines:

        clean_line = line.strip()

        if not clean_line:
            continue

        upper_line = clean_line.upper()

        # Detect certification section
        if (
            "CERTIFICATION" in upper_line
            or "LICENSES" in upper_line
        ):
            inside_certification_section = True
            continue

        # Stop at another major section
        if inside_certification_section and any(
            section in upper_line
            for section in [
                "EDUCATION",
                "EXPERIENCE",
                "PROJECT",
                "SKILLS",
                "ACHIEVEMENT"
            ]
        ):
            inside_certification_section = False

        if inside_certification_section:

            # Ignore very short lines
            if len(clean_line) > 4:

                if clean_line not in certifications:
                    certifications.append(clean_line)

    return certifications[:10]


# ============================================================
# EXTRACT PROJECTS
# ============================================================

def extract_projects(text):

    projects = []

    lines = text.splitlines()

    inside_project_section = False

    for line in lines:

        clean_line = line.strip()

        if not clean_line:
            continue

        upper_line = clean_line.upper()

        # Detect project section
        if "PROJECT" in upper_line:

            inside_project_section = True
            continue

        # Stop when another section starts
        if inside_project_section and any(
            section in upper_line
            for section in [
                "EDUCATION",
                "EXPERIENCE",
                "SKILLS",
                "CERTIFICATION",
                "ACHIEVEMENT",
                "LANGUAGE"
            ]
        ):

            inside_project_section = False

        if inside_project_section:

            if len(clean_line) > 8:

                # Ignore bullet descriptions
                if not clean_line.startswith(("-", "•", "*")):

                    if clean_line not in projects:
                        projects.append(clean_line)

    return projects[:10]


# ============================================================
# CREATE FEEDBACK
# ============================================================

def create_feedback(text):

    feedback_sentences = []

    sentences = re.split(r'(?<=[.!?])\s+', text)

    feedback_words = [
        "leadership",
        "managed",
        "mentor",
        "mentoring",
        "trained",
        "recognized",
        "appreciated",
        "award",
        "improved",
        "customer",
        "client",
        "quality",
        "team",
        "successfully",
        "achievement"
    ]

    for sentence in sentences:

        sentence = sentence.strip()

        if len(sentence) < 30:
            continue

        sentence_lower = sentence.lower()

        if any(
            word in sentence_lower
            for word in feedback_words
        ):

            feedback_sentences.append(sentence)

    return feedback_sentences[:5]


# ============================================================
# PROCESS RESUME
# ============================================================

def process_resume(filename):

    filepath = os.path.join(INPUT_DIR, filename)

    with open(
        filepath,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as file:

        text = file.read()

    # Ignore sample resume
    if "sample purposes only" in text.lower():
        print(f"Skipped sample resume: {filename}")
        return

    employee_name = find_employee_name(text)

    if employee_name is None:

        print(f"No employee matched: {filename}")
        return

    print()
    print("------------------------------------------")
    print("Resume:", filename)
    print("Employee:", employee_name)

    skills = extract_skills(text)

    certifications = extract_certifications(text)

    projects = extract_projects(text)

    feedback = create_feedback(text)

    print("Skills:", len(skills))
    print("Certifications:", len(certifications))
    print("Projects:", len(projects))
    print("Feedback:", len(feedback))


    # ========================================================
    # SEND DATA TO NEO4J
    # ========================================================

    with driver.session(database=NEO4J_DATABASE) as session:

        # ----------------------------------------------------
        # SKILLS
        # ----------------------------------------------------

        for skill in skills:

            session.run(
                """
                MATCH (e:Employee {
                    employee_name: $employee_name
                })

                MERGE (s:Skill {
                    name: $skill
                })

                MERGE (e)-[:HAS_SKILL]->(s)
                """,
                employee_name=employee_name,
                skill=skill
            )


        # ----------------------------------------------------
        # CERTIFICATIONS
        # ----------------------------------------------------

        for certification in certifications:

            session.run(
                """
                MATCH (e:Employee {
                    employee_name: $employee_name
                })

                MERGE (c:Certification {
                    name: $certification
                })

                MERGE (e)-[:HAS_CERTIFICATION]->(c)
                """,
                employee_name=employee_name,
                certification=certification
            )


        # ----------------------------------------------------
        # PROJECTS
        # ----------------------------------------------------

        for project in projects:

            session.run(
                """
                MATCH (e:Employee {
                    employee_name: $employee_name
                })

                MERGE (p:Project {
                    name: $project
                })

                MERGE (e)-[:WORKED_ON]->(p)
                """,
                employee_name=employee_name,
                project=project
            )


        # ----------------------------------------------------
        # FEEDBACK
        # ----------------------------------------------------

        for feedback_text in feedback:

            session.run(
                """
                MATCH (e:Employee {
                    employee_name: $employee_name
                })

                CREATE (f:Feedback {
                    text: $feedback_text
                })

                CREATE (e)-[:RECEIVED_FEEDBACK]->(f)
                """,
                employee_name=employee_name,
                feedback_text=feedback_text
            )


# ============================================================
# PROCESS ALL TXT FILES
# ============================================================

if not os.path.exists(INPUT_DIR):

    print("ERROR: extracted folder not found.")

else:

    files = os.listdir(INPUT_DIR)

    txt_files = [
        file for file in files
        if file.lower().endswith(".txt")
    ]

    print()
    print("TXT files found:", len(txt_files))

    for filename in txt_files:

        process_resume(filename)


# ============================================================
# CLOSE NEO4J
# ============================================================

driver.close()

print()
print("==============================================")
print("UNSTRUCTURED ETL COMPLETED SUCCESSFULLY!")
print("==============================================")