# rng = Random Number Generator
# f"PRG-{i:06d}" = It generates zero-padded IDs
def generate_programs(rng, count):
    departments = [
        "Computer Science",
        "Information Technology",
        "Electronics",
        "Mechanical",
        "Civil",
        "Electrical",
        "Business Administration",
        "Mathematics",
        "Physics",
        "Data Science"
    ]

    programs = []

    for i in range(1, count + 1):
        degree = rng.choice(["BACHELOR", "MASTER"])
        duration = 4 if degree == "BACHELOR" else 2
        department = departments[(i - 1) % len(departments)]

        program = (
            f"PRG-{i:06d}",
            f"{degree} in {department}",
            degree,
            duration,
            department,
            "ACTIVE"
        )

        programs.append(program)

    return programs


def generate_courses(rng, count):
    subjects = [
        "Python Programming",
        "Database Management",
        "Machine Learning",
        "Data Structures",
        "Computer Networks",
        "Artificial Intelligence",
        "Statistics",
        "Cloud Computing",
        "Data Analytics",
        "Operating Systems",
        "Web Development",
        "Big Data",
        "Software Engineering",
        "Cyber Security",
        "Mathematics"
    ]

    courses = []

    for i in range(1, count + 1):
        subject = rng.choice(subjects)

        course = (
            f"CRS-{i:06d}",
            f"{subject} {i}",
            f"CRS-{i:04d}",
            rng.choice([2, 3, 4]),
            rng.choice(["CORE", "ELECTIVE", "LAB"]),
            f"Study of {subject}",
            "ACTIVE"
        )

        courses.append(course)

    return courses


def generate_students(rng, count):
    students = []

    for i in range(1, count + 1):
        student = (
            f"STD-{i:06d}",
            f"Student {i:05d}",
            f"student{i}@example.edu",
            rng.randint(2022, 2026),
            "ACTIVE"
        )

        students.append(student)

    return students


def generate_faculty(rng, count):
    departments = [
        "Computer Science",
        "Information Technology",
        "Electronics",
        "Mechanical",
        "Civil",
        "Electrical",
        "Business Administration",
        "Mathematics",
        "Physics",
        "Data Science"
    ]

    faculty = []

    for i in range(1, count + 1):
        member = (
            f"FAC-{i:06d}",
            f"Faculty {i:04d}",
            rng.choice(departments),
            f"faculty{i}@example.edu",
            rng.choice([12, 14, 16, 18, 20]),
            rng.choice(["FULL_TIME", "PART_TIME"]),
            "ACTIVE"
        )

        faculty.append(member)

    return faculty


def generate_rooms(rng, count):
    rooms = []

    for i in range(1, count + 1):
        room = (
            f"ROM-{i:06d}",
            f"Room {i:03d}",
            f"Building {rng.randint(1, 5)}",
            rng.choice([30, 40, 50, 60, 100, 150]),
            rng.choice(["CLASSROOM", "LAB", "LECTURE_HALL"]),
            "AVAILABLE"
        )

        rooms.append(room)

    return rooms


def generate_terms():
    terms = [
        (
            "TERM-2026-ODD",
            "2026-2027",
            "ODD",
            "2026-08-01",
            "2026-12-15",
            "ACTIVE"
        ),
        (
            "TERM-2027-EVEN",
            "2026-2027",
            "EVEN",
            "2027-01-10",
            "2027-05-20",
            "PLANNED"
        )
    ]

    return terms
