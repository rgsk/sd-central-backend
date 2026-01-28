import argparse
import sys

import firebase_admin
from firebase_admin import auth, credentials


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Firebase custom token for a user by email."
    )
    parser.add_argument(
        "email",
        help="User email to look up in Firebase Auth",
    )
    parser.add_argument(
        "--credentials",
        default="credentials-firebaseServiceAccountKey.json",
        help="Path to Firebase service account JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        cred = credentials.Certificate(args.credentials)
        firebase_admin.initialize_app(cred)
    except Exception as exc:
        print(f"Failed to initialize Firebase Admin: {exc}", file=sys.stderr)
        return 1

    try:
        user = auth.get_user_by_email(args.email)
    except Exception as exc:
        print(f"Failed to find user for email {args.email}: {exc}", file=sys.stderr)
        return 1

    try:
        token = auth.create_custom_token(user.uid)
    except Exception as exc:
        print(f"Failed to create custom token: {exc}", file=sys.stderr)
        return 1

    print(token.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
