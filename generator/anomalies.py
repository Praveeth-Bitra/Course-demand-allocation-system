
import csv
import json
import os


def create_anomaly_cases():
    anomaly_cases = [
        {
            "anomaly_id": "ANM-001",
            "anomaly_type": "FACULTY_SKILL_MISMATCH",
            "description": "A faculty member is assigned to a course outside their skill set.",
            "test_input": {
                "faculty_id": "TEST-FAC-001",
                "course_id": "TEST-CRS-001",
                "faculty_has_course_skill": False
            },
            "expected_result": "REJECTED",
            "ground_truth": "Faculty does not have the required course skill."
        },
        {
            "anomaly_id": "ANM-002",
            "anomaly_type": "WORKLOAD_EXCEEDED",
            "description": "A faculty member is assigned more hours than their maximum workload.",
            "test_input": {
                "faculty_id": "TEST-FAC-002",
                "maximum_workload": 16,
                "current_workload": 15,
                "additional_assigned_hours": 3
            },
            "expected_result": "REJECTED",
            "ground_truth": "Total assigned workload would become 18 hours, exceeding the limit of 16."
        },
        {
            "anomaly_id": "ANM-003",
            "anomaly_type": "SECTION_CAPACITY_TOO_LOW",
            "description": "The available section capacity is lower than forecast demand.",
            "test_input": {
                "course_id": "TEST-CRS-003",
                "forecast_demand": 80,
                "section_capacity": 50
            },
            "expected_result": "INSUFFICIENT_CAPACITY",
            "ground_truth": "The section has a shortage of 30 seats."
        },
        {
            "anomaly_id": "ANM-004",
            "anomaly_type": "PREREQUISITE_SCHEDULING_VIOLATION",
            "description": "A course is scheduled before its prerequisite course.",
            "test_input": {
                "course_id": "CRS-000007",
                "prerequisite_course_id": "CRS-000006",
                "course_section_id": "SEC-2027-000012",
                "course_start": "2027-01-11 11:00:00",
                "prerequisite_section_id": "SEC-2027-000010",
                "prerequisite_start": "2027-01-13 14:00:00"
            },
            "expected_result": "SCHEDULING_VIOLATION",
            "ground_truth": "Course CRS-000007 is scheduled before prerequisite CRS-000006. The prerequisite section starts later."
        },
        {
            "anomaly_id": "ANM-005",
            "anomaly_type": "DUPLICATE_FACULTY_ASSIGNMENT",
            "description": "The same faculty member is assigned to the same section more than once.",
            "test_input": {
                "faculty_id": "TEST-FAC-005",
                "section_id": "TEST-SEC-005",
                "assignment_count": 2
            },
            "expected_result": "DUPLICATE_DETECTED",
            "ground_truth": "The same faculty member has two assignment records for the same section."
        }
    ]

    return anomaly_cases


def validate_anomaly_cases(anomaly_cases):
    results = []

    for case in anomaly_cases:
        test_input = case["test_input"]
        anomaly_type = case["anomaly_type"]

        if anomaly_type == "FACULTY_SKILL_MISMATCH":
            detected = not test_input["faculty_has_course_skill"]

        elif anomaly_type == "WORKLOAD_EXCEEDED":
            total_workload = (
                test_input["current_workload"]
                + test_input["additional_assigned_hours"]
            )
            detected = total_workload > test_input["maximum_workload"]

        elif anomaly_type == "SECTION_CAPACITY_TOO_LOW":
            detected = (
                test_input["section_capacity"]
                < test_input["forecast_demand"]
            )

        elif anomaly_type == "PREREQUISITE_SCHEDULING_VIOLATION":
            detected = (
                test_input["course_start"]
                < test_input["prerequisite_start"]
            )

        elif anomaly_type == "DUPLICATE_FACULTY_ASSIGNMENT":
            detected = test_input["assignment_count"] > 1

        else:
            detected = False

        case["detected"] = detected
        case["validation_status"] = (
            "PASS" if detected else "FAIL"
        )

        results.append(case)

    return results


def export_ground_truth(anomaly_cases):
    output_directory = os.path.join(
        "data",
        "ground_truth"
    )

    os.makedirs(output_directory, exist_ok=True)

    json_path = os.path.join(
        output_directory,
        "anomaly_ground_truth.json"
    )

    csv_path = os.path.join(
        output_directory,
        "anomaly_ground_truth.csv"
    )

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(
            anomaly_cases,
            file,
            indent=4
        )

    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "anomaly_id",
            "anomaly_type",
            "description",
            "expected_result",
            "ground_truth",
            "detected",
            "validation_status",
            "test_input"
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for case in anomaly_cases:
            row = case.copy()
            row["test_input"] = json.dumps(
                case["test_input"]
            )
            writer.writerow(row)

    print("Ground-truth files created:")
    print(json_path)
    print(csv_path)


def main():
    anomaly_cases = create_anomaly_cases()

    results = validate_anomaly_cases(
        anomaly_cases
    )

    export_ground_truth(results)

    passed = 0

    print("\nANOMALY VALIDATION REPORT")
    print("--------------------------------")

    for case in results:
        print(
            "{} | {} | {}".format(
                case["anomaly_id"],
                case["anomaly_type"],
                case["validation_status"]
            )
        )

        if case["validation_status"] == "PASS":
            passed += 1

    print("--------------------------------")
    print("Passed: {}/{}".format(passed, len(results)))
    print("Failed: {}/{}".format(
        len(results) - passed,
        len(results)
    ))


if __name__ == "__main__":
    main()
