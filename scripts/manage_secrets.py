#!/usr/bin/env python3

"""
CLI tool for managing secrets in Google Cloud Secret Manager.

Usage:
    python scripts/manage_secrets.py create <secret-id> <secret-value>
    python scripts/manage_secrets.py update <secret-id> <secret-value>
    python scripts/manage_secrets.py get <secret-id>
    python scripts/manage_secrets.py delete <secret-id>
    python scripts/manage_secrets.py setup-all

"""

import argparse
import logging
import os
import sys
from enum import Enum
from pathlib import Path

from services.secret_manager import SecretManagerService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

sys.path.insert(0, str(Path(__file__).parent.parent))


class CommandType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    GET = "get"
    DELETE = "delete"
    SETUP_ALL = "setup-all"


def create_secret(
    secret_manager: SecretManagerService, secret_id: str, secret_value: str
):
    """Create a new secret."""
    try:
        result = secret_manager.create_secret(secret_id, secret_value)
        logger.info(f"✅ Secret '{secret_id}' created successfully: {result}")
    except Exception as e:
        logger.error(f"❌ Error creating secret: {e}")
        sys.exit(1)


def update_secret(
    secret_manager: SecretManagerService, secret_id: str, secret_value: str
):
    """Update an existing secret."""
    try:
        result = secret_manager.update_secret(secret_id, secret_value)
        logger.info(f"✅ Secret '{secret_id}' updated successfully: {result}")
    except Exception as e:
        logger.error(f"❌ Error updating secret: {e}")
        sys.exit(1)


def get_secret(secret_manager: SecretManagerService, secret_id: str):
    """Get a secret value."""
    try:
        value = secret_manager.get_secret(secret_id)
        print(f"Secret '{secret_id}': {value}")
    except Exception as e:
        print(f"❌ Error getting secret: {e}")
        sys.exit(1)


def delete_secret(secret_manager: SecretManagerService, secret_id: str):
    """Delete a secret."""
    try:
        secret_manager.delete_secret(secret_id)
        print(f"✅ Secret '{secret_id}' deleted successfully")
    except Exception as e:
        print(f"❌ Error deleting secret: {e}")
        sys.exit(1)


def setup_all_secrets(secret_manager: SecretManagerService):
    """
    Setup all required secrets from environment variables.

    This is useful for initial setup - it reads secrets from .env file
    and creates them in Secret Manager.
    """
    from dotenv import load_dotenv

    load_dotenv()

    secrets_mapping = {
        "database-url": "DATABASE_URL",
        "jwt-secret-key": "JWT_SECRET_KEY",
        "gemini-api-key": "GEMINI_API_KEY",
    }

    print("🔐 Setting up secrets in Google Cloud Secret Manager...\n")

    for secret_id, env_var in secrets_mapping.items():
        value = os.getenv(env_var)

        if not value:
            print(f"⚠️  Skipping '{secret_id}': {env_var} not found in environment")
            continue

        try:
            # Try to create the secret
            secret_manager.create_secret(secret_id, value)
            print(f"✅ Created secret: {secret_id}")
        except Exception as e:
            # If creation fails, try to update instead
            if "already exists" in str(e).lower():
                try:
                    secret_manager.update_secret(secret_id, value)
                    print(f"✅ Updated secret: {secret_id}")
                except Exception as update_error:
                    print(f"❌ Failed to update '{secret_id}': {update_error}")
            else:
                print(f"❌ Failed to create '{secret_id}': {e}")

    print("\n✅ Secret setup complete!")
    print("\n📝 Next steps:")
    print("1. Set USE_SECRET_MANAGER=true in your production environment")
    print("2. Remove sensitive values from .env file in production")
    print("3. Ensure your service account has 'Secret Manager Secret Accessor' role")


def main():
    parser = argparse.ArgumentParser(
        description="Manage secrets in Google Cloud Secret Manager"
    )

    parser.add_argument(
        "command",
        choices=[
            CommandType.CREATE,
            CommandType.UPDATE,
            CommandType.GET,
            CommandType.DELETE,
            CommandType.SETUP_ALL,
        ],
        help="Command to execute",
    )

    parser.add_argument(
        "secret_id", nargs="?", help="Secret ID (not required for setup-all)"
    )

    parser.add_argument(
        "secret_value", nargs="?", help="Secret value (required for create and update)"
    )

    parser.add_argument(
        "--project-id", help="GCP Project ID (defaults to GCS_PROJECT_ID env var)"
    )

    args = parser.parse_args()

    project_id = args.project_id or os.getenv("GCS_PROJECT_ID")
    if not project_id:
        logger.error(
            "❌ Error: GCS_PROJECT_ID must be set in environment or passed with --project-id"
        )
        sys.exit(1)

    secret_manager = SecretManagerService(project_id=project_id)

    if args.command == CommandType.CREATE:
        if not args.secret_id or not args.secret_value:
            print("❌ Error: create requires <secret-id> and <secret-value>")
            sys.exit(1)
        create_secret(secret_manager, args.secret_id, args.secret_value)

    elif args.command == CommandType.UPDATE:
        if not args.secret_id or not args.secret_value:
            print("❌ Error: update requires <secret-id> and <secret-value>")
            sys.exit(1)
        update_secret(secret_manager, args.secret_id, args.secret_value)

    elif args.command == CommandType.GET:
        if not args.secret_id:
            print("❌ Error: get requires <secret-id>")
            sys.exit(1)
        get_secret(secret_manager, args.secret_id)

    elif args.command == CommandType.DELETE:
        if not args.secret_id:
            print("❌ Error: delete requires <secret-id>")
            sys.exit(1)
        delete_secret(secret_manager, args.secret_id)

    elif args.command == CommandType.SETUP_ALL:
        setup_all_secrets(secret_manager)


if __name__ == "__main__":
    main()
