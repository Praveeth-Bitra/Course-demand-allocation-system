
from datetime import datetime, timedelta, time

from backend.database import get_connection


FORECAST_RUN_ID = "FORECAST-2027-EVEN-001"


def get_weekday(start_date, days_to_add):
    current_date = start_date
    added_days = 0

    while added_days < days_to_add:
        current_date += timedelta(days=1)

        if current_date.weekday() < 5:
            added_days += 1

    return current_date


def get_schedule(slot_number, term_start, term_end):
    day_number = slot_number // 3
    time_number = slot_number % 3

    first_day = term_start

    while first_day.weekday() >= 5:
        first_day += timedelta(days=1)

    if day_number == 0:
        schedule_date = first_day
    else:
        schedule_date = get_weekday(first_day, day_number)

    if schedule_date > term_end:
        return None, None

    time_slots = [
        (time(9, 0), time(11, 0)),
        (time(11, 0), time(13, 0)),
        (time(14, 0), time(16, 0))
    ]

    start_time, end_time = time_slots[time_number]

    start_datetime = datetime.combine(schedule_date, start_time)
    end_datetime = datetime.combine(schedule_date, end_time)

    return start_datetime, end_datetime


def get_suitable_rooms(course_type, rooms):
    suitable_rooms = []

    for room in rooms:
        room_id, capacity, room_type = room

        if course_type == "LAB":
            if room_type == "LAB":
                suitable_rooms.append(room)
        else:
            if room_type in ("CLASSROOM", "LECTURE_HALL"):
                suitable_rooms.append(room)

    suitable_rooms.sort(key=lambda room: room[1], reverse=True)

    return suitable_rooms


def order_courses_by_prerequisites(course_ids, prerequisites):
    dependencies = {}

    for course_id in course_ids:
        dependencies[course_id] = set()

    for course_id, prerequisite_course_id in prerequisites:
        if course_id in dependencies and prerequisite_course_id in dependencies:
            dependencies[course_id].add(prerequisite_course_id)

    remaining = set(course_ids)
    ordered_courses = []

    while remaining:
        ready_courses = []

        for course_id in remaining:
            unfinished_prerequisites = dependencies[course_id].intersection(
                remaining
            )

            if not unfinished_prerequisites:
                ready_courses.append(course_id)

        if not ready_courses:
            raise ValueError(
                "Circular prerequisite relationship detected. "
                "Section generation stopped."
            )

        ready_courses.sort()

        for course_id in ready_courses:
            ordered_courses.append(course_id)
            remaining.remove(course_id)

    return ordered_courses, dependencies


def generate_sections():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                forecast_id,
                course_id,
                term_id,
                predicted_enrollment,
                course_type
            FROM demand_forecasts
            JOIN courses USING (course_id)
            WHERE forecast_run_id = %s
            ORDER BY course_id
        """, (FORECAST_RUN_ID,))

        forecasts = cursor.fetchall()

        if not forecasts:
            print("No forecast records found.")
            return

        term_id = forecasts[0][2]

        cursor.execute("""
            SELECT start_date, end_date
            FROM academic_terms
            WHERE term_id = %s
        """, (term_id,))

        term = cursor.fetchone()

        if not term:
            print("Academic term not found.")
            return

        term_start = term[0]
        term_end = term[1]

        cursor.execute("""
            SELECT room_id, capacity, room_type
            FROM rooms
            WHERE status = 'AVAILABLE'
        """)

        rooms = cursor.fetchall()

        if not rooms:
            print("No available rooms found.")
            return

        cursor.execute("""
            SELECT COUNT(*)
            FROM sections
            WHERE term_id = %s
        """, (term_id,))

        existing_sections = cursor.fetchone()[0]

        if existing_sections > 0:
            print("Sections already exist for this term.")
            print("Generation stopped to prevent duplicate records.")
            return

        cursor.execute("""
            SELECT course_id, prerequisite_course_id
            FROM prerequisites
            WHERE (effective_from IS NULL OR effective_from <= %s)
              AND (effective_to IS NULL OR effective_to >= %s)
        """, (term_end, term_start))

        prerequisites = cursor.fetchall()

        forecasts_by_course = {}

        for forecast in forecasts:
            forecasts_by_course[forecast[1]] = forecast

        course_ids = list(forecasts_by_course.keys())

        ordered_courses, dependencies = order_courses_by_prerequisites(
            course_ids,
            prerequisites
        )

        room_usage = {}

        for room in rooms:
            room_usage[room[0]] = 0

        # Stores the latest finishing time of every generated course.
        course_latest_end = {}

        section_counter = 1
        total_sections = 0
        total_students = 0
        total_unmet = 0

        for course_id in ordered_courses:
            forecast = forecasts_by_course[course_id]

            forecast_id = forecast[0]
            course_term_id = forecast[2]
            demand = forecast[3]
            course_type = forecast[4]

            if demand <= 0:
                continue

            # Find when all prerequisite sections have finished.
            prerequisite_end = None

            for prerequisite_course_id in dependencies[course_id]:
                prerequisite_course_end = course_latest_end.get(
                    prerequisite_course_id
                )

                if prerequisite_course_end is not None:
                    if (
                        prerequisite_end is None
                        or prerequisite_course_end > prerequisite_end
                    ):
                        prerequisite_end = prerequisite_course_end

            suitable_rooms = get_suitable_rooms(course_type, rooms)

            remaining_demand = demand
            section_number = 1
            course_section_ends = []

            while remaining_demand > 0:
                if not suitable_rooms:
                    break

                selected_room = None
                selected_start = None
                selected_end = None
                selected_slot = None

                for room in suitable_rooms:
                    room_id = room[0]

                    slot_number = room_usage[room_id]

                    # Skip slots until the prerequisite completion rule is met.
                    while True:
                        start_datetime, end_datetime = get_schedule(
                            slot_number,
                            term_start,
                            term_end
                        )

                        if start_datetime is None:
                            break

                        if (
                            prerequisite_end is None
                            or start_datetime > prerequisite_end
                        ):
                            break

                        slot_number += 1

                    if start_datetime is None:
                        continue

                    selected_room = room
                    selected_start = start_datetime
                    selected_end = end_datetime
                    selected_slot = slot_number
                    break

                if selected_room is None:
                    break

                room_id = selected_room[0]
                room_capacity = selected_room[1]

                section_capacity = min(
                    remaining_demand,
                    room_capacity
                )

                section_id = f"SEC-2027-{section_counter:06d}"

                cursor.execute("""
                    INSERT INTO sections (
                        section_id,
                        course_id,
                        term_id,
                        room_id,
                        section_number,
                        capacity,
                        scheduled_start,
                        scheduled_end,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    section_id,
                    course_id,
                    course_term_id,
                    room_id,
                    section_number,
                    section_capacity,
                    selected_start,
                    selected_end,
                    "PROPOSED"
                ))

                # Reserve this room slot.
                room_usage[room_id] = selected_slot + 1

                section_counter += 1
                section_number += 1

                total_sections += 1
                total_students += section_capacity

                remaining_demand -= section_capacity

                course_section_ends.append(selected_end)

            if course_section_ends:
                course_latest_end[course_id] = max(course_section_ends)

            if remaining_demand > 0:
                cursor.execute("""
                    INSERT INTO unmet_demand (
                        forecast_id,
                        course_id,
                        term_id,
                        unmet_quantity,
                        issue_type,
                        resolution_status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    forecast_id,
                    course_id,
                    course_term_id,
                    remaining_demand,
                    "ROOM_CAPACITY",
                    "OPEN"
                ))

                total_unmet += remaining_demand

        connection.commit()

        print("\nSECTION GENERATION COMPLETED")
        print("--------------------------------")
        print(f"Forecast run: {FORECAST_RUN_ID}")
        print(f"Courses processed: {len(ordered_courses)}")
        print(f"Total sections created: {total_sections}")
        print(f"Total seats allocated: {total_students}")
        print(f"Total unmet demand: {total_unmet}")

    except Exception as error:
        connection.rollback()
        print(f"Section generation failed: {error}")

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    generate_sections()
