
import random

from backend.database import get_connection

from generator.student_data import (
    generate_student_plans,
    generate_registration_interests
)


rng = random.Random(20261022)

connection = get_connection()
cursor = connection.cursor()

cursor.execute(
    "SELECT student_id FROM students ORDER BY student_id"
)
students = cursor.fetchall()

cursor.execute(
    "SELECT program_id FROM programs ORDER BY program_id"
)
programs = cursor.fetchall()

cursor.execute(
    "SELECT term_id, academic_year, semester, start_date, end_date, status FROM academic_terms ORDER BY term_id"
)
terms = cursor.fetchall()

cursor.execute(
    "SELECT program_id, course_id FROM program_courses ORDER BY program_course_id"
)
program_courses = cursor.fetchall()

cursor.close()
connection.close()


plans = generate_student_plans(
    students,
    programs,
    terms
)

interests = generate_registration_interests(
    rng,
    plans,
    program_courses
)


connection = get_connection()
cursor = connection.cursor()

try:

    for i in range(len(plans)):

        cursor.execute(
            """INSERT INTO student_plans
            (plan_id, student_id, program_id, term_id,
             current_semester, plan_status)
            VALUES (%s, %s, %s, %s, %s, %s)""",

            (
                i + 1,
                plans[i][0],
                plans[i][1],
                plans[i][2],
                plans[i][3],
                plans[i][4]
            )
        )

    cursor.executemany(
        """INSERT INTO registration_interests
        (plan_id, course_id, priority, interest_date, interest_status)
        VALUES (%s, %s, %s, %s, %s)""",
        interests
    )

    connection.commit()

    print("\nSTUDENT DATA INSERTION")
    print("----------------------")
    print("Students:", len(students))
    print("Student Plans:", len(plans))
    print("Registration Interests:", len(interests))
    print("All student records inserted successfully.")

except Exception as error:

    connection.rollback()
    print("Insertion failed:", error)

finally:

    cursor.close()
    connection.close()
