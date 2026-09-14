import mysql.connector
from neo4j import GraphDatabase
from decimal import Decimal


# ============================================================
# MYSQL CONFIGURATION
# ============================================================

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "root123"
MYSQL_DATABASE = "employee_intelligence"


# ============================================================
# NEO4J CONFIGURATION
# ============================================================

NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Kavi@0607"
NEO4J_DATABASE = "neo4j"


# ============================================================
# CONVERT MYSQL VALUES TO NEO4J-SUPPORTED VALUES
# ============================================================

def clean_data(data):

    cleaned = {}

    for key, value in data.items():

        # MySQL DECIMAL → Python float
        if isinstance(value, Decimal):
            cleaned[key] = float(value)

        # MySQL DATE → string
        elif hasattr(value, "isoformat"):
            cleaned[key] = value.isoformat()

        else:
            cleaned[key] = value

    return cleaned


# ============================================================
# CONNECT TO MYSQL
# ============================================================

mysql_conn = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE
)

mysql_cursor = mysql_conn.cursor(dictionary=True)

print("Connected to MySQL")


# ============================================================
# CONNECT TO NEO4J
# ============================================================

neo4j_driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

print("Connected to Neo4j")


# ============================================================
# CLEAR OLD NEO4J GRAPH
# ============================================================

with neo4j_driver.session(database=NEO4J_DATABASE) as session:

    session.run("MATCH (n) DETACH DELETE n")

print("Old Neo4j graph cleared")


# ============================================================
# 1. CREATE COMPANY NODES
# ============================================================

mysql_cursor.execute("SELECT * FROM Company")

companies = mysql_cursor.fetchall()

with neo4j_driver.session(database=NEO4J_DATABASE) as session:

    for company in companies:

        company = clean_data(company)

        session.run(
            """
            MERGE (c:Company {
                company_id: $company_id
            })

            SET c.company_name = $company_name,
                c.industry = $industry,
                c.address = $address,
                c.city = $city,
                c.state = $state,
                c.country = $country,
                c.revenue = $revenue,
                c.employee_count = $employee_count
            """,
            **company
        )

print("Company nodes created")


# ============================================================
# 2. CREATE EMPLOYEE NODES
# ============================================================

mysql_cursor.execute("SELECT * FROM Employee")

employees = mysql_cursor.fetchall()

with neo4j_driver.session(database=NEO4J_DATABASE) as session:

    for employee in employees:

        employee = clean_data(employee)

        session.run(
            """
            MERGE (e:Employee {
                employee_id: $employee_id
            })

            SET e.employee_name = $employee_name,
                e.age = $age,
                e.gender = $gender,
                e.email = $email,
                e.phone = $phone,
                e.designation = $designation,
                e.department = $department,
                e.salary = $salary,
                e.joining_date = $joining_date

            WITH e

            MATCH (c:Company {
                company_id: $company_id
            })

            MERGE (e)-[:WORKS_AT]->(c)
            """,
            **employee
        )

print("Employee nodes and WORKS_AT relationships created")


# ============================================================
# 3. CREATE PERFORMANCE NODES
# ============================================================

mysql_cursor.execute("SELECT * FROM Performance")

performances = mysql_cursor.fetchall()

with neo4j_driver.session(database=NEO4J_DATABASE) as session:

    for performance in performances:

        performance = clean_data(performance)

        session.run(
            """
            MERGE (p:Performance {
                performance_id: $performance_id
            })

            SET p.review_year = $review_year,
                p.productivity_score = $productivity_score,
                p.teamwork_score = $teamwork_score,
                p.communication_score = $communication_score,
                p.technical_skill_score = $technical_skill_score,
                p.attendance_score = $attendance_score,
                p.leadership_score = $leadership_score,
                p.problem_solving_score = $problem_solving_score,
                p.innovation_score = $innovation_score,
                p.punctuality_score = $punctuality_score,
                p.work_quality_score = $work_quality_score,
                p.overall_score = $overall_score

            WITH p

            MATCH (e:Employee {
                employee_id: $employee_id
            })

            MERGE (e)-[:HAS_PERFORMANCE]->(p)
            """,
            **performance
        )

print("Performance nodes and HAS_PERFORMANCE relationships created")


# ============================================================
# CLOSE CONNECTIONS
# ============================================================

mysql_cursor.close()
mysql_conn.close()
neo4j_driver.close()


# ============================================================
# SUCCESS MESSAGE
# ============================================================

print()
print("==============================================")
print("STRUCTURED ETL COMPLETED SUCCESSFULLY!")
print("==============================================")
print("Company nodes      : 1")
print("Employee nodes     : 10")
print("Performance nodes  : 20")
print("==============================================")