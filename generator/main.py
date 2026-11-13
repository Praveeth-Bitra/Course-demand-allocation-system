
import random

from generator.master_data import (
    generate_programs,
    generate_courses,
    generate_students,
    generate_faculty,
    generate_rooms,
    generate_terms
)

from backend.database import get_connection


SEED = 20261022
SCALE = "starter"

if SCALE == "starter":
    program_count = 10
    course_count = 100
    student_count = 1000
    faculty_count = 50
    room_count = 10
else:
    program_count = 100
    course_count = 1000
    student_count = 10000
    faculty_count = 500
    room_count = 100


rng = random.Random(SEED)

programs = generate_programs(rng, program_count)
courses = generate_courses(rng, course_count)
students = generate_students(rng, student_count)
faculty = generate_faculty(rng, faculty_count)
rooms = generate_rooms(rng, room_count)
terms = generate_terms()


def insert_master_data(programs, courses, students, faculty, rooms, terms):

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.executemany(
            """INSERT INTO programs
            (program_id, program_name, degree_level,
             duration_years, department_name, status)
            VALUES (%s, %s, %s, %s, %s, %s)""",
            programs
        )

        cursor.executemany(
            """INSERT INTO courses
            (course_id, course_name, course_code, credits,
             course_type, description, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            courses
        )

        cursor.executemany(
            """INSERT INTO students
            (student_id, student_name, email, admission_year, status)
            VALUES (%s, %s, %s, %s, %s)""",
            students
        )

        cursor.executemany(
            """INSERT INTO faculty
            (faculty_id, faculty_name, department_name, email,
             max_workload_hours, employment_type, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            faculty
        )

        cursor.executemany(
            """INSERT INTO rooms
            (room_id, room_name, building, capacity, room_type, status)
            VALUES (%s, %s, %s, %s, %s, %s)""",
            rooms
        )

        cursor.executemany(
            """INSERT INTO academic_terms
            (term_id, academic_year, semester, start_date,
             end_date, status)
            VALUES (%s, %s, %s, %s, %s, %s)""",
            terms
        )

        connection.commit()

        print("\nMASTER DATA INSERTION")
        print("----------------------")
        print("All master records inserted successfully.")

    except Exception as error:
        connection.rollback()
        print("Insertion failed:", error)

    finally:
        cursor.close()
        connection.close()


print("MASTER DATA GENERATION")
print("----------------------")
print("Programs:", len(programs))
print("Courses:", len(courses))
print("Students:", len(students))
print("Faculty:", len(faculty))
print("Rooms:", len(rooms))
print("Academic Terms:", len(terms))

insert_master_data(
    programs,
    courses,
    students,
    faculty,
    rooms,
    terms
)
