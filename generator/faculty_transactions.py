
import random

from backend.database import get_connection

from generator.faculty_data import (
    generate_faculty_skills,
    generate_faculty_availability,
    generate_faculty_leaves
)


rng = random.Random(20261022)

connection = get_connection()
cursor = connection.cursor()

cursor.execute(
    "SELECT faculty_id FROM faculty ORDER BY faculty_id"
)
faculty = cursor.fetchall()

cursor.execute(
    "SELECT course_id FROM courses ORDER BY course_id"
)
courses = cursor.fetchall()

cursor.execute(
    """SELECT term_id, academic_year, semester,
    start_date, end_date, status
    FROM academic_terms ORDER BY term_id"""
)
terms = cursor.fetchall()

cursor.close()
connection.close()


skills = generate_faculty_skills(
    rng,
    faculty,
    courses
)

availability = generate_faculty_availability(
    faculty,
    terms
)

leaves = generate_faculty_leaves(
    rng,
    faculty
)


connection = get_connection()
cursor = connection.cursor()

try:

    cursor.executemany(
        """INSERT INTO faculty_skills
        (faculty_id, course_id, proficiency_level, years_experience)
        VALUES (%s, %s, %s, %s)""",
        skills
    )

    cursor.executemany(
        """INSERT INTO availability
        (faculty_id, start_datetime, end_datetime,
        availability_type, remarks)
        VALUES (%s, %s, %s, %s, %s)""",
        availability + leaves
    )

    connection.commit()

    print("\nFACULTY DATA INSERTION")
    print("----------------------")
    print("Faculty:", len(faculty))
    print("Faculty Skills:", len(skills))
    print("Availability Records:", len(availability))
    print("Leave Records:", len(leaves))
    print("All faculty records inserted successfully.")

except Exception as error:

    connection.rollback()
    print("Insertion failed:", error)

finally:

    cursor.close()
    connection.close()
