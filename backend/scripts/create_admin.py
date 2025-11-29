#!/usr/bin/env python3
"""
Create Admin User Script

Creates an initial admin user for the UNS Kobetsu Keiyakusho system.
Run this script after database initialization.

Usage:
    python scripts/create_admin.py
    python scripts/create_admin.py --email admin@company.com --password securepass123
"""
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.exc import IntegrityError
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User


def create_admin_user(email: str, password: str, full_name: str = "Admin User") -> bool:
    """
    Create an admin user in the database.

    Args:
        email: Admin email address
        password: Admin password
        full_name: Admin full name

    Returns:
        True if user created successfully, False otherwise
    """
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"\nUser with email {email} already exists!")
            print(f"User ID: {existing_user.id}")
            print(f"Role: {existing_user.role}")
            return False

        # Hash the password
        hashed_password = get_password_hash(password)

        # Create user
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        print("\n" + "=" * 60)
        print("Admin User Created Successfully!")
        print("=" * 60)
        print(f"User ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Full Name: {user.full_name}")
        print(f"Role: {user.role}")
        print(f"Active: {user.is_active}")
        print("=" * 60)
        print("\nYou can now log in with these credentials at /api/v1/auth/login")

        return True

    except IntegrityError as e:
        print(f"\nError: Email {email} is already registered")
        db.rollback()
        return False
    except Exception as e:
        print(f"\nError creating user: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Create an admin user for UNS Kobetsu Keiyakusho"
    )
    parser.add_argument(
        "--email",
        type=str,
        default="admin@example.com",
        help="Admin email address"
    )
    parser.add_argument(
        "--password",
        type=str,
        default="admin123",
        help="Admin password (min 8 characters)"
    )
    parser.add_argument(
        "--name",
        type=str,
        default="System Administrator",
        help="Admin full name"
    )

    args = parser.parse_args()

    # Validate password
    if len(args.password) < 8:
        print("Error: Password must be at least 8 characters")
        sys.exit(1)

    # Create admin
    success = create_admin_user(
        email=args.email,
        password=args.password,
        full_name=args.name
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
