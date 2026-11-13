
import csv
import json
import os


def main():
    base_directory = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )

    export_directory = os.path.join(
        base_directory,
        "data",
        "exports"
    )

    csv_directory = os.path.join(
        export_directory,
        "csv"
    )

    json_path = os.path.join(
        export_directory,
        "project_data.json"
    )

    sql_path = os.path.join(
        export_directory,
        "project_data.sql"
    )

    print("EXPORT VALIDATION")
    print("=" * 45)

    passed = 0
    failed = 0

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as file:
            json_data = json.load(file)

        print("PASS: JSON file is readable")
        passed += 1
    else:
        print("FAIL: JSON file missing")
        failed += 1
        return

    if os.path.exists(sql_path) and os.path.getsize(sql_path) > 0:
        print("PASS: SQL file exists")
        passed += 1
    else:
        print("FAIL: SQL file missing or empty")
        failed += 1

    tables = json_data["tables"]

    print("\nTABLE RECORD VALIDATION")
    print("-" * 45)

    for table_name, table_data in tables.items():
        expected_count = len(table_data["records"])

        csv_path = os.path.join(
            csv_directory,
            table_name + ".csv"
        )

        if not os.path.exists(csv_path):
            print("FAIL: {} CSV missing".format(table_name))
            failed += 1
            continue

        with open(
            csv_path,
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as file:
            reader = csv.reader(file)
            rows = list(reader)

        actual_count = len(rows) - 1

        if actual_count == expected_count:
            print(
                "PASS: {} ({})".format(
                    table_name,
                    actual_count
                )
            )
            passed += 1
        else:
            print(
                "FAIL: {} (JSON: {}, CSV: {})".format(
                    table_name,
                    expected_count,
                    actual_count
                )
            )
            failed += 1

    print("\n" + "=" * 45)
    print("Passed:", passed)
    print("Failed:", failed)
    print("Total checks:", passed + failed)

    if failed == 0:
        print("\nALL EXPORT CHECKS PASSED")
    else:
        print("\nEXPORT VALIDATION FAILED")


if __name__ == "__main__":
    main()
