
import random

from backend.database import get_connection

from generator.history_data import generate_course_history


rng = random.Random(20261022)

connection = get_connection()
cursor = connection.cursor()

cursor.execute(
    """SELECT plan_id, student_id, program_id, term_id
    FROM student_plans
    ORDER BY plan_id"""
)

plans = cursor.fetchall()

cursor.execute(
    """SELECT ri.plan_id, ri.course_id
    FROM registration_interests ri
    ORDER BY ri.interest_id"""
)

interests = cursor.fetchall()

cursor.close()
connection.close()


history = generate_course_history(
    rng,
    plans,
    interests
)


connection = get_connection()
cursor = connection.cursor()

try:

    cursor.executemany(
        """INSERT INTO student_course_history
        (student_id, course_id, term_id, enrollment_status,
        final_grade, enrolled_at)
        VALUES (%s, %s, %s, %s, %s, %s)""",
        history
    )

    connection.commit()

    print("\nHISTORICAL ENROLLMENT DATA")
    print("--------------------------")
    print("Student Plans:", len(plans))
    print("Registration Interests:", len(interests))
    print("Historical Records:", len(history))
    print("Historical records inserted successfully.")

except Exception as error:

    connection.rollback()
    print("Insertion failed:", error)

finally:

    cursor.close()
    connection.close()
