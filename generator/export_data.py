
import csv
import json
import os

from datetime import date, datetime
from decimal import Decimal

from backend.database import get_connection


def convert_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, bytes):
        return value.hex()

    return value


def sql_value(value):
    if value is None:
        return "NULL"

    if isinstance(value, bool):
        return "1" if value else "0"

    if isinstance(value, (int, float, Decimal)):
        return str(value)

    if isinstance(value, (datetime, date)):
        value = value.isoformat()

    if isinstance(value, bytes):
        return "0x" + value.hex()

    value = str(value)

    value = value.replace("\\", "\\\\")
    value = value.replace("'", "\\'")
    value = value.replace("\0", "\\0")
    value = value.replace("\n", "\\n")
    value = value.replace("\r", "\\r")
    value = value.replace("\b", "\\b")
    value = value.replace("\t", "\\t")
    value = value.replace("\x1a", "\\Z")

    return "'" + value + "'"


def export_csv(table_name, columns, records, output_directory):
    file_path = os.path.join(
        output_directory,
        table_name + ".csv"
    )

    with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)

        writer.writerow(columns)

        for record in records:
            writer.writerow([
                convert_value(record[column])
                for column in columns
            ])

    return file_path


def export_json(database_name, all_data, output_directory):
    file_path = os.path.join(
        output_directory,
        "project_data.json"
    )

    export_data = {
        "database": database_name,
        "tables": all_data
    }

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            export_data,
            file,
            indent=4,
            default=convert_value
        )

    return file_path


def export_sql(cursor, all_data, output_directory):
    file_path = os.path.join(
        output_directory,
        "project_data.sql"
    )

    with open(file_path, "w", encoding="utf-8") as file:
        file.write("SET NAMES utf8mb4;\n")
        file.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")

        for table_name, table_data in all_data.items():

            cursor.execute(
                "SHOW CREATE TABLE `{}`".format(table_name)
            )

            create_statement = cursor.fetchone()["Create Table"]

            create_statement = create_statement.replace(
                "CREATE TABLE",
                "CREATE TABLE IF NOT EXISTS",
                1
            )

            file.write("-- Table: {}\n".format(table_name))
            file.write(create_statement + ";\n\n")

            columns = table_data["columns"]
            records = table_data["records"]

            if not records:
                continue

            column_names = ", ".join(
                "`{}`".format(column)
                for column in columns
            )

            file.write(
                "-- Data for table: {}\n".format(table_name)
            )

            batch_size = 500

            for start in range(0, len(records), batch_size):

                batch = records[start:start + batch_size]

                insert_rows = []

                for record in batch:

                    values = ", ".join(
                        sql_value(record[column])
                        for column in columns
                    )

                    insert_rows.append("(" + values + ")")

                insert_statement = (
                    "INSERT INTO `{}` ({}) VALUES\n{};\n\n"
                ).format(
                    table_name,
                    column_names,
                    ",\n".join(insert_rows)
                )

                file.write(insert_statement)

        file.write("SET FOREIGN_KEY_CHECKS = 1;\n")

    return file_path


def get_primary_key_columns(cursor, table_name):

    cursor.execute(
        "SHOW KEYS FROM `{}` WHERE Key_name = 'PRIMARY'".format(
            table_name
        )
    )

    primary_keys = cursor.fetchall()

    primary_keys.sort(
        key=lambda row: row["Seq_in_index"]
    )

    return [
        row["Column_name"]
        for row in primary_keys
    ]


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

    os.makedirs(csv_directory, exist_ok=True)

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    all_data = {}
    total_records = 0

    try:

        cursor.execute("SELECT DATABASE() AS database_name")
        database_name = cursor.fetchone()["database_name"]

        cursor.execute("SHOW TABLES")
        table_results = cursor.fetchall()

        table_names = sorted(
            list(table.values())[0]
            for table in table_results
        )

        print("DATABASE EXPORT")
        print("=" * 45)
        print("Database:", database_name)
        print("Tables found:", len(table_names))

        for table_name in table_names:

            # Retrieve primary-key columns for stable ordering
            primary_key_columns = get_primary_key_columns(
                cursor,
                table_name
            )

            if primary_key_columns:

                order_by = ", ".join(
                    "`{}`".format(column)
                    for column in primary_key_columns
                )

                query = (
                    "SELECT * FROM `{}` ORDER BY {}".format(
                        table_name,
                        order_by
                    )
                )

            else:

                query = "SELECT * FROM `{}`".format(table_name)

                print(
                    "WARNING: No primary key found for table:",
                    table_name
                )

            cursor.execute(query)

            records = cursor.fetchall()

            columns = [
                description[0]
                for description in cursor.description
            ]

            all_data[table_name] = {
                "columns": columns,
                "records": records
            }

            export_csv(
                table_name,
                columns,
                records,
                csv_directory
            )

            record_count = len(records)
            total_records += record_count

            print(
                "Exported: {} | Records: {}".format(
                    table_name,
                    record_count
                )
            )

        json_path = export_json(
            database_name,
            all_data,
            export_directory
        )

        sql_path = export_sql(
            cursor,
            all_data,
            export_directory
        )

        print("\n" + "=" * 45)
        print("EXPORT COMPLETED")
        print("=" * 45)

        print("Tables exported:", len(table_names))
        print("Total records exported:", total_records)
        print("CSV directory:", csv_directory)
        print("JSON file:", json_path)
        print("SQL file:", sql_path)

    finally:

        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
