import json
from pathlib import Path


def main() -> None:
    data_path = Path(__file__).resolve().parents[1] / "data" / "old_students.json"
    with data_path.open() as file:
        students = json.load(file)
    print(len(students))


if __name__ == "__main__":
    main()
