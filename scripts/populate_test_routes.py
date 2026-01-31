#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

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


def fetch_json(url):
    headers = {"Accept": "application/json"}
    namespace = os.getenv("DB_NAMESPACE")
    if namespace:
        headers["X-Test-Namespace"] = namespace
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read()
    return json.loads(body.decode("utf-8"))


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(
        description="Populate JSON seed data from /test routes."
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)",
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

    base_url = args.base_url.rstrip("/")
    data_dir = os.path.join(BASE_DATA_DIR, args.data_name)
    routes = ROUTES
    if args.only:
        routes = {k: v for k, v in ROUTES.items() if k in args.only}
        missing = sorted(set(args.only) - set(routes))
        if missing:
            print(f"Unknown routes: {missing}")
            return 2

    failures = 0
    for route, filename in routes.items():
        url = f"{base_url}/test/{route}"
        file_path = os.path.join(data_dir, filename)
        print(f"Fetching {url} -> {file_path}...")
        try:
            data = fetch_json(url)
        except urllib.error.HTTPError as exc:
            print(f"  ERROR: HTTP {exc.code} {exc.reason}")
            failures += 1
            continue
        except urllib.error.URLError as exc:
            print(f"  ERROR: {exc.reason}")
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
