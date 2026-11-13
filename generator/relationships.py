
import random

from backend.database import get_connection

from generator.relationship_data import (
    generate_program_courses,
    generate_prerequisites,
    insert_relationships
)


rng = random.Random(20261022)

connection = get_connection()
cursor = connection.cursor()

cursor.execute("SELECT program_id FROM programs ORDER BY program_id")
programs = cursor.fetchall()

cursor.execute("SELECT course_id FROM courses ORDER BY course_id")
courses = cursor.fetchall()

cursor.close()
connection.close()

program_courses, course_groups = generate_program_courses(
    programs,
    courses
)

prerequisites = generate_prerequisites(course_groups, rng)

print("RELATIONSHIP DATA GENERATION")
print("----------------------------")
print("Programs:", len(programs))
print("Courses:", len(courses))
print("Program-course relationships:", len(program_courses))
print("Prerequisites:", len(prerequisites))

insert_relationships(program_courses, prerequisites)
