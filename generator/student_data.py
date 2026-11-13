
def generate_student_plans(students, programs, terms):

    plans = []
    plan_id = 1

    for student in students:

        student_id = student[0]

        program_index = (plan_id - 1) % len(programs)
        program_id = programs[program_index][0]

        for term in terms:

            if term[2] == "ODD":
                semester = 1
            else:
                semester = 2

            plan = (
                student_id,
                program_id,
                term[0],
                semester,
                "ACTIVE"
            )

            plans.append(plan)
            plan_id += 1

    return plans


def generate_registration_interests(rng, plans, program_courses):

    interests = []

    courses_by_program = {}

    for relationship in program_courses:

        program_id = relationship[0]
        course_id = relationship[1]

        if program_id not in courses_by_program:
            courses_by_program[program_id] = []

        courses_by_program[program_id].append(course_id)

    for plan_id in range(len(plans)):

        plan = plans[plan_id]

        program_id = plan[1]
        available_courses = courses_by_program[program_id]

        selected_courses = rng.sample(
            available_courses,
            min(3, len(available_courses))
        )

        for course_id in selected_courses:

            interest = (
                plan_id + 1,
                course_id,
                rng.randint(1, 5),
                "2026-08-01",
                "PENDING"
            )

            interests.append(interest)

    return interests
