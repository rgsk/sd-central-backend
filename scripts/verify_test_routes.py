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


FOREIGN_KEY_ROUTES = {
    "student_id": "students",
    "enrollment_id": "enrollments",
    "academic_session_id": "academic_sessions",
    "academic_class_id": "academic_classes",
    "academic_term_id": "academic_terms",
    "subject_id": "subjects",
    "academic_class_subject_id": "academic_class_subjects",
    "academic_class_subject_term_id": "academic_class_subject_terms",
    "report_card_id": "report_cards",
    "report_card_subject_id": "report_card_subjects",
    "date_sheet_id": "date_sheets",
    "date_sheet_subject_id": "date_sheet_subjects",
    "user_id": "users",
}

REMAPPED_IGNORE_FIELDS = {"created_at", "updated_at", "deleted_at"}


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def fetch_json(url):
    headers = {"Accept": "application/json"}
    namespace = os.getenv("DB_NAMESPACE")
    if namespace:
        headers["X-Test-Namespace"] = namespace
    req = urllib.request.Request(url, headers=headers)
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


def _strip_id(item):
    if not isinstance(item, dict):
        return item
    return {key: value for key, value in item.items() if key != "id"}


def _strip_fields_for_remap(item):
    if not isinstance(item, dict):
        return item
    return {
        key: value
        for key, value in item.items()
        if key not in REMAPPED_IGNORE_FIELDS
    }


def _normalize_for_id_remap(items):
    if not isinstance(items, list):
        return None
    normalized = []
    for item in items:
        if not isinstance(item, dict) or "id" not in item:
            return None
        normalized.append(_strip_fields_for_remap(item))
    normalized.sort(key=lambda value: json.dumps(value, sort_keys=True))
    return normalized


def _build_id_map_by_index(expected, actual):
    if not isinstance(expected, list) or not isinstance(actual, list):
        return None
    if len(expected) != len(actual):
        return None
    mapping = {}
    for expected_item, actual_item in zip(expected, actual):
        if not isinstance(expected_item, dict) or not isinstance(actual_item, dict):
            return None
        if "id" not in expected_item or "id" not in actual_item:
            return None
        mapping[expected_item["id"]] = actual_item["id"]
    return mapping


def _remap_foreign_key_value(value, route, id_maps):
    if route not in id_maps:
        return value
    mapping = id_maps[route]
    if isinstance(value, list):
        remapped = []
        for item in value:
            remapped.append(mapping.get(item, item))
        return remapped
    return mapping.get(value, value)


def _remap_expected_items(items, id_maps):
    remapped_items = []
    for item in items:
        if not isinstance(item, dict):
            remapped_items.append(item)
            continue
        updated = dict(item)
        if "id" in updated:
            updated["id"] = id_maps.get("self", {}).get(
                updated["id"], updated["id"])
        for key, value in list(updated.items()):
            route = FOREIGN_KEY_ROUTES.get(key)
            if route:
                updated[key] = _remap_foreign_key_value(value, route, id_maps)
        remapped_items.append(updated)
    return remapped_items


def compare_lists(expected, actual, allow_id_remap=False, id_maps=None):
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

    if allow_id_remap:
        if id_maps is None:
            errors.append("list contents differ (id remap unavailable)")
            return errors
        remapped_expected = _remap_expected_items(
            expected,
            {
                "self": id_maps.get("self", {}),
                **id_maps,
            },
        )
        expected_normalized = _normalize_for_id_remap(remapped_expected)
        actual_normalized = _normalize_for_id_remap(actual)
        if expected_normalized is None or actual_normalized is None:
            errors.append("list contents differ (id remap unsupported)")
            return errors
        if expected_normalized != actual_normalized:
            errors.append("list contents differ (id remap allowed)")
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
        description="Verify /dev routes match JSON seed data."
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
    parser.add_argument(
        "--data-name",
        required=True,
        help="Seed data folder name under seeders/data",
    )
    parser.add_argument(
        "--logical-compare",
        action="store_true",
        help="Compare normalized data (ignore volatile fields and remap ids)",
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
    route_data = {}
    for route, filename in routes.items():
        url = f"{base_url}/dev/{route}"
        file_path = os.path.join(data_dir, filename)
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
        route_data[route] = {"expected": expected, "actual": actual}

    id_maps_by_route = {}
    if args.logical_compare:
        for route, payload in route_data.items():
            mapping = _build_id_map_by_index(
                payload["expected"], payload["actual"]
            )
            if mapping is not None:
                id_maps_by_route[route] = mapping

    for route, payload in route_data.items():
        id_maps = {}
        if args.logical_compare:
            id_maps = dict(id_maps_by_route)
            id_maps["self"] = id_maps_by_route.get(route, {})

        errors = compare_lists(
            payload["expected"],
            payload["actual"],
            allow_id_remap=args.logical_compare,
            id_maps=id_maps,
        )
        if errors:
            failures += 1
            for error in errors:
                print(f"  MISMATCH ({route}): {error}")
        else:
            print(f"  OK ({route})")

    if failures:
        print(f"\nFAILED: {failures} route(s) mismatched.")
        return 1

    print("\nALL OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
