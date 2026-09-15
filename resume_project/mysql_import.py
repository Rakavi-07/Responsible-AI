import mysql.connector
from mysql.connector import Error


# ============================================================
# MYSQL CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root123",
    "database": "employee_intelligence"
}


# ============================================================
# EMPLOYEE → COMPANY / ORGANIZATION DATA
# Based on the actual resumes
# ============================================================

EMPLOYMENT_DATA = {

    "Jennifer Hall": [
        {
            "company": "IEM",
            "designation": "Information Systems Manager"
        },
        {
            "company": "Face To Face",
            "designation": "Air Export Agent"
        }
    ],

    "ARYAN SHARMA": [
        {
            "company": "Accemberg Technologies Pvt. Ltd.",
            "designation": "Backend Development Intern"
        },
        {
            "company": "Jharkhand Education Project Council (JEPC)",
            "designation": "Intern"
        }
    ],

    "JAISAL RATHI": [],

    "Lucy Harding": [
        {
            "company": "Everyday Market",
            "designation": "Customer Service Assistant"
        },
        {
            "company": "Common Room Café",
            "designation": "Front Desk Assistant"
        },
        {
            "company": "Corner Retail",
            "designation": "Sales Floor Assistant"
        }
    ],

    "Varad Singhal": [
        {
            "company": "Printellect Innovations",
            "designation": "Application Developer Intern"
        },
        {
            "company": "Tellwell Digital Services",
            "designation": "Application Developer Intern"
        }
    ],

    "JACOB J. JACOBY": [
        {
            "company": "ABC Plumbing and Heating",
            "designation": "Apprentice Plumber"
        },
        {
            "company": "United States Army",
            "designation": "Sergeant / E-5"
        }
    ],

    "VINCE D. CONLAN": [
        {
            "company": "United States Navy",
            "designation": "Manager, Airframes Intermediate Maintenance"
        }
    ],

    "RICHARD A. LEVINSON": [
        {
            "company": "United States Navy",
            "designation": "Department Head"
        },
        {
            "company": "United States Marine Corps",
            "designation": "Department Supervisor"
        }
    ],

    "DAVID H. ANDERS": [
        {
            "company": "United States Navy",
            "designation": "Director of Operations"
        }
    ],

    "GEORGE REDMOND": [
        {
            "company": "Framing Supplies Inc",
            "designation": "Inside Sales Representative"
        },
        {
            "company": "HSS Marketing",
            "designation": "Independent Sales Representative"
        },
        {
            "company": "Radio Hub",
            "designation": "Marketing Associate"
        }
    ]
}


# ============================================================
# CONNECT TO MYSQL
# ============================================================

try:

    connection = mysql.connector.connect(**DB_CONFIG)

    if not connection.is_connected():
        print("MySQL connection failed!")
        exit()

    print("MySQL connection successful!")

    cursor = connection.cursor()


    # ========================================================
    # CREATE EMPLOYEE_COMPANY TABLE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_company (
            employee_id INT,
            company_id INT,
            designation VARCHAR(100),
            joining_date DATE,
            leaving_date DATE,

            PRIMARY KEY (employee_id, company_id),

            FOREIGN KEY (employee_id)
                REFERENCES employee(employee_id),

            FOREIGN KEY (company_id)
                REFERENCES company(company_id)
        )
    """)

    connection.commit()

    print("employee_company table ready.")


    # ========================================================
    # CLEAN OLD DATA
    # IMPORTANT: ORDER MATTERS BECAUSE OF FOREIGN KEYS
    # ========================================================

    # Step 1:
    # Remove employee → company references first
    cursor.execute("""
        UPDATE employee
        SET company_id = NULL
    """)

    # Step 2:
    # Remove old employee-company relationships
    cursor.execute("""
        DELETE FROM employee_company
    """)

    # Step 3:
    # Now companies can safely be deleted
    cursor.execute("""
        DELETE FROM company
    """)

    connection.commit()

    print("Old company relationships cleared.")


    # ========================================================
    # REMOVE SAMPLE/TEMPLATE EMPLOYEE
    # ========================================================

    cursor.execute("""
        DELETE FROM employee
        WHERE employee_name = 'Resume for Sample Purposes Only'
    """)

    connection.commit()

    print("Sample resume removed.")


    # ========================================================
    # INSERT COMPANY + EMPLOYEE-COMPANY RELATIONSHIPS
    # ========================================================

    for employee_name, jobs in EMPLOYMENT_DATA.items():

        # ----------------------------------------------------
        # Find employee
        # ----------------------------------------------------

        cursor.execute("""
            SELECT employee_id
            FROM employee
            WHERE employee_name = %s
        """, (employee_name,))

        result = cursor.fetchone()

        if not result:

            print(
                f"\nWARNING: Employee not found -> "
                f"{employee_name}"
            )

            continue

        employee_id = result[0]

        print(f"\nEmployee: {employee_name}")


        # ----------------------------------------------------
        # No company information
        # ----------------------------------------------------

        if not jobs:

            print("  -> No employment organization found")

            continue


        # ----------------------------------------------------
        # Process every company
        # ----------------------------------------------------

        for index, job in enumerate(jobs):

            company_name = job["company"]
            designation = job["designation"]


            # ------------------------------------------------
            # Check whether company already exists
            # ------------------------------------------------

            cursor.execute("""
                SELECT company_id
                FROM company
                WHERE company_name = %s
            """, (company_name,))

            company_result = cursor.fetchone()


            # ------------------------------------------------
            # Insert company if it does not exist
            # ------------------------------------------------

            if company_result:

                company_id = company_result[0]

            else:

                cursor.execute("""
                    INSERT INTO company
                    (
                        company_name
                    )
                    VALUES (%s)
                """, (company_name,))

                company_id = cursor.lastrowid


            # ------------------------------------------------
            # Insert employee-company relationship
            # ------------------------------------------------

            cursor.execute("""
                INSERT INTO employee_company
                (
                    employee_id,
                    company_id,
                    designation
                )
                VALUES (%s, %s, %s)
            """, (
                employee_id,
                company_id,
                designation
            ))


            print(
                f"  -> {company_name}"
                f" | {designation}"
            )


            # ------------------------------------------------
            # Store first/current company in employee table
            #
            # employee.company_id is retained because it is
            # already part of the lab schema.
            #
            # Complete employment history is stored in
            # employee_company.
            # ------------------------------------------------

            if index == 0:

                cursor.execute("""
                    UPDATE employee
                    SET
                        company_id = %s,
                        designation = %s
                    WHERE employee_id = %s
                """, (
                    company_id,
                    designation,
                    employee_id
                ))


    # ========================================================
    # COMMIT EVERYTHING
    # ========================================================

    connection.commit()


    # ========================================================
    # IMPORT SUMMARY
    # ========================================================

    print("\n")
    print("==============================================")
    print("              IMPORT COMPLETE")
    print("==============================================")


    # Number of employees
    cursor.execute("""
        SELECT COUNT(*)
        FROM employee
    """)

    employee_count = cursor.fetchone()[0]


    # Number of companies
    cursor.execute("""
        SELECT COUNT(*)
        FROM company
    """)

    company_count = cursor.fetchone()[0]


    # Number of employment relationships
    cursor.execute("""
        SELECT COUNT(*)
        FROM employee_company
    """)

    relationship_count = cursor.fetchone()[0]


    print(f"Employees             : {employee_count}")
    print(f"Companies              : {company_count}")
    print(f"Employment links       : {relationship_count}")


    # ========================================================
    # DISPLAY COMPANY TABLE
    # ========================================================

    print("\n")
    print("==============================================")
    print("                 COMPANIES")
    print("==============================================")

    cursor.execute("""
        SELECT
            company_id,
            company_name
        FROM company
        ORDER BY company_id
    """)

    companies = cursor.fetchall()

    for company in companies:

        print(
            f"{company[0]} | {company[1]}"
        )


    # ========================================================
    # DISPLAY EMPLOYEE → COMPANY RELATIONSHIPS
    # ========================================================

    print("\n")
    print("==============================================")
    print("       EMPLOYEE → COMPANY RELATIONSHIPS")
    print("==============================================")

    cursor.execute("""
        SELECT
            e.employee_name,
            c.company_name,
            ec.designation
        FROM employee_company ec

        JOIN employee e
            ON ec.employee_id = e.employee_id

        JOIN company c
            ON ec.company_id = c.company_id

        ORDER BY e.employee_name
    """)

    relationships = cursor.fetchall()


    for row in relationships:

        print(
            f"{row[0]} "
            f"-> {row[1]} "
            f"| {row[2]}"
        )


    # ========================================================
    # FINAL VERIFICATION
    # ========================================================

    print("\n")
    print("==============================================")
    print("                 VERIFICATION")
    print("==============================================")


    # Employees without companies
    cursor.execute("""
        SELECT employee_name
        FROM employee
        WHERE company_id IS NULL
    """)

    no_company = cursor.fetchall()


    print(
        f"Employees without a company: "
        f"{len(no_company)}"
    )

    for employee in no_company:

        print(
            f"  - {employee[0]}"
        )


    # ========================================================
    # CLOSE CONNECTION
    # ========================================================

    cursor.close()
    connection.close()

    print("\nMySQL connection closed.")
    print("Done! ✅")


except Error as e:

    print("\nMySQL Error:")
    print(e)