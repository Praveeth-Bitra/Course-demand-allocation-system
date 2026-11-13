'''
rng.sample() selects different courses without repetition for each faculty member.
proficiency_level represents how well the faculty member knows a subject.
years_experience represents teaching experience.
AVAILABLE records represent term availability.
LEAVE records identify periods when a faculty member cannot be assigned.'''

def generate_faculty_skills(rng, faculty, courses):

    skills = []

    for member in faculty:

        faculty_id = member[0]

        selected_courses = rng.sample(
            courses,
            min(3, len(courses))
        )

        for course in selected_courses:

            skill = (
                faculty_id,
                course[0],
                rng.choice([
                    "INTERMEDIATE",
                    "ADVANCED",
                    "EXPERT"
                ]),
                rng.randint(1, 15)
            )

            skills.append(skill)

    return skills


def generate_faculty_availability(faculty, terms):

    availability = []

    for member in faculty:

        faculty_id = member[0]

        for term in terms:

            record = (
                faculty_id,
                str(term[3]) + " 00:00:00",
                str(term[4]) + " 23:59:59",
                "AVAILABLE",
                "Available during academic term"
            )

            availability.append(record)

    return availability


def generate_faculty_leaves(rng, faculty):

    leaves = []

    selected_faculty = rng.sample(
        faculty,
        min(5, len(faculty))
    )

    leave_dates = [
        ("2026-10-12 00:00:00", "2026-10-16 23:59:59"),
        ("2027-03-08 00:00:00", "2027-03-12 23:59:59")
    ]

    for member in selected_faculty:

        faculty_id = member[0]
        leave = rng.choice(leave_dates)

        record = (
            faculty_id,
            leave[0],
            leave[1],
            "LEAVE",
            "Planned faculty leave"
        )

        leaves.append(record)

    return leaves

