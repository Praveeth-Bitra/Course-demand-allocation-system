
import random

from backend.database import get_connection


def generate_program_courses(programs, courses):

    program_courses = []
    course_groups = {}

    for i in range(len(courses)):

        program_index = (i * len(programs)) // len(courses)

        program_id = programs[program_index][0]
        course_id = courses[i][0]

        semester = (i % 8) + 1

        program_courses.append((
            program_id,
            course_id,
            semester,
            True
        ))

        if program_id not in course_groups:
            course_groups[program_id] = []

        course_groups[program_id].append(course_id)

    return program_courses, course_groups


def generate_prerequisites(course_groups, rng):

    prerequisites = []

    for program_id in course_groups:

        courses = course_groups[program_id]

        for i in range(1, len(courses)):

            if rng.random() < 0.4:

                prerequisites.append((
                    courses[i],
                    courses[i - 1],
                    "D",
                    "2026-08-01",
                    None
                ))

    return prerequisites


def insert_relationships(program_courses, prerequisites):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.executemany(
            """INSERT INTO program_courses
            (program_id, course_id, recommended_semester, is_mandatory)
            VALUES (%s, %s, %s, %s)""",
            program_courses
        )

        cursor.executemany(
            """INSERT INTO prerequisites
            (course_id, prerequisite_course_id, minimum_grade,
             effective_from, effective_to)
            VALUES (%s, %s, %s, %s, %s)""",
            prerequisites
        )

        connection.commit()

        print("Program-course relationships inserted:", len(program_courses))
        print("Prerequisites inserted:", len(prerequisites))

    except Exception as error:
        connection.rollback()
        print("Insertion failed:", error)

    finally:
        cursor.close()
        connection.close()
