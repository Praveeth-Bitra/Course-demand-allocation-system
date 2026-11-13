
def generate_course_history(rng, plans, interests):

    history = []

    interests_by_plan = {}

    for interest in interests:

        plan_id = interest[0]
        course_id = interest[1]

        if plan_id not in interests_by_plan:
            interests_by_plan[plan_id] = []

        interests_by_plan[plan_id].append(course_id)

    for plan in plans:

        plan_id = plan[0]
        student_id = plan[1]
        term_id = plan[3]

        selected_courses = interests_by_plan.get(plan_id, [])

        for course_id in selected_courses:

            status = rng.choices(
                ["COMPLETED", "ENROLLED", "DROPPED", "FAILED"],
                weights=[65, 20, 10, 5],
                k=1
            )[0]

            record = (
                student_id,
                course_id,
                term_id,
                status,
                None,
                "2026-08-01"
            )

            history.append(record)

    return history
