#!/usr/bin/env python3
import argparse
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

from sqlmodel import Session  # noqa: E402

from db import engine, normalize_db_namespace  # noqa: E402
from routers import dev as dev_routes  # noqa: E402

BASE_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "seeders",
    "data",
)


ROUTES = {
    "students": "students.json",
    "enrollments": "enrollments.json",
    "academic_sessions": "academic_sessions.json",
    "academic_classes": "academic_classes.json",
    "academic_terms": "academic_terms.json",
    "subjects": "subjects.json",
    "academic_class_subjects": "academic_class_subjects.json",
    "academic_class_subject_terms": "academic_class_subject_terms.json",
    "report_cards": "report_cards.json",
    "report_card_subjects": "report_card_subjects.json",
    "date_sheets": "date_sheets.json",
    "date_sheet_subjects": "date_sheet_subjects.json",
    "users": "users.json",
}


def fetch_route_data(route: str, session: Session):
    items = dev_routes.fetch_route_data(route, session)
    response_model = dev_routes.ROUTE_RESPONSE_MODELS[route]
    return [
        response_model.model_validate(item).model_dump(mode="json")
        for item in items
    ]


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(
        description="Populate JSON seed data from DB data."
    )
    parser.add_argument(
        "--only",
        nargs="*",
        help="Only update these routes (space-separated)",
    )
    parser.add_argument(
        "--data-name",
        required=True,
        help="Seed data folder name under seeders/data",
    )
    args = parser.parse_args()

    data_dir = os.path.join(BASE_DATA_DIR, args.data_name)
    routes = ROUTES
    if args.only:
        routes = {k: v for k, v in ROUTES.items() if k in args.only}
        missing = sorted(set(args.only) - set(routes))
        if missing:
            print(f"Unknown routes: {missing}")
            return 2

    try:
        namespace = normalize_db_namespace(os.getenv("DB_NAMESPACE"))
    except ValueError as exc:
        print(f"  ERROR: {exc}")
        return 2

    failures = 0
    with Session(engine) as session:
        session.info["db_namespace"] = namespace
        for route, filename in routes.items():
            file_path = os.path.join(data_dir, filename)
            print(f"Fetching {route} -> {file_path}...")
            try:
                data = fetch_route_data(route, session)
            except KeyError as exc:
                print(f"  ERROR: {exc}")
                failures += 1
                continue
            except Exception as exc:
                print(f"  ERROR: {exc}")
                failures += 1
                continue

            try:
                write_json(file_path, data)
            except OSError as exc:
                print(f"  ERROR: {exc}")
                failures += 1
                continue

            print("  OK")

    if failures:
        print(f"\nFAILED: {failures} route(s) not written.")
        return 1

    print("\nDONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
