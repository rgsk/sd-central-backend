#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "seeders",
    "academic_classes_students",
    "data",
)

ROUTES = {
    "students": "students.json",
    "academic_sessions": "academic_sessions.json",
    "academic_classes": "academic_classes.json",
    "academic_terms": "academic_terms.json",
    "subjects": "subjects.json",
    "academic_class_subjects": "academic_class_subjects.json",
    "report_cards": "report_cards.json",
    "report_card_subjects": "report_card_subjects.json",
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def fetch_json(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read()
    return json.loads(body.decode("utf-8"))


def index_by_id(items):
    if not isinstance(items, list):
        return None, "expected list"
    seen = {}
    for item in items:
        if not isinstance(item, dict) or "id" not in item:
            return None, "missing id"
        if item["id"] in seen:
            return None, f"duplicate id {item['id']}"
        seen[item["id"]] = item
    return seen, None


def diff_dict(expected, actual):
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    changed = []
    for key in sorted(set(expected) & set(actual)):
        if expected[key] != actual[key]:
            changed.append(key)
    return missing, extra, changed


def compare_lists(expected, actual):
    errors = []
    expected_index, expected_issue = index_by_id(expected)
    actual_index, actual_issue = index_by_id(actual)

    if expected_issue or actual_issue:
        if expected != actual:
            errors.append("list contents differ (non-id comparison)")
        return errors

    if expected_index is None or actual_index is None:
        errors.append("list contents differ (non-id comparison)")
        return errors

    expected_ids = set(expected_index)
    actual_ids = set(actual_index)
    missing_ids = sorted(expected_ids - actual_ids)
    extra_ids = sorted(actual_ids - expected_ids)
    if missing_ids:
        errors.append(f"missing ids: {missing_ids}")
    if extra_ids:
        errors.append(f"extra ids: {extra_ids}")

    for item_id in sorted(expected_ids & actual_ids):
        missing, extra, changed = diff_dict(
            expected_index[item_id], actual_index[item_id]
        )
        if missing or extra or changed:
            errors.append(
                "id "
                f"{item_id} diffs missing={missing} extra={extra} changed={changed}"
            )
    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Verify /test routes match JSON seed data."
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        help="Only check these routes (space-separated)",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
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
        file_path = os.path.join(DATA_DIR, filename)
        print(f"Checking {url} against {file_path}...")
        try:
            expected = load_json(file_path)
        except FileNotFoundError:
            print(f"  ERROR: missing seed file {file_path}")
            failures += 1
            continue
        try:
            actual = fetch_json(url)
        except urllib.error.HTTPError as exc:
            print(f"  ERROR: HTTP {exc.code} {exc.reason}")
            failures += 1
            continue
        except urllib.error.URLError as exc:
            print(f"  ERROR: {exc.reason}")
            failures += 1
            continue

        errors = compare_lists(expected, actual)
        if errors:
            failures += 1
            for error in errors:
                print(f"  MISMATCH: {error}")
        else:
            print("  OK")

    if failures:
        print(f"\nFAILED: {failures} route(s) mismatched.")
        return 1

    print("\nALL OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
