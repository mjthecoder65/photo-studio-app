import os
from typing import Optional

from google.cloud import secretmanager
from functools import lru_cache


class SecretManagerService:
    """Service for accessing secrets from Google Cloud Secret Manager."""

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize the Secret Manager client.

        Args:
            project_id: GCP project ID. If not provided, will use GCS_PROJECT_ID from environment.
        """
        self.project_id = project_id or os.getenv("GCS_PROJECT_ID")
        if not self.project_id:
            raise ValueError(
                "GCS_PROJECT_ID must be set in environment or passed to constructor"
            )

        self.client = secretmanager.SecretManagerServiceClient()

    @lru_cache(maxsize=None)
    def get_secret(self, secret_id: str, version: str = "latest") -> str:
        """
        Access a secret from Secret Manager.

        Args:
            secret_id: The ID of the secret to access
            version: The version of the secret (default: "latest")

        Returns:
            str: The secret value

        Raises:
            Exception: If secret cannot be accessed
        """
        try:
            # Build the resource name of the secret version
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"

            # Access the secret version
            response = self.client.access_secret_version(request={"name": name})

            # Decode the secret payload
            payload = response.payload.data.decode("UTF-8")
            return payload

        except Exception as e:
            raise Exception(f"Failed to access secret '{secret_id}': {str(e)}")

    def get_secret_or_env(
        self, secret_id: str, env_var: str, version: str = "latest"
    ) -> str:
        """
        Get secret from Secret Manager, fallback to environment variable.

        This is useful for local development where secrets might be in .env file,
        but in production they're in Secret Manager.

        Args:
            secret_id: The ID of the secret in Secret Manager
            env_var: The environment variable name to use as fallback
            version: The version of the secret (default: "latest")

        Returns:
            str: The secret value from Secret Manager or environment variable

        Raises:
            ValueError: If secret is not found in either location
        """
        # Try Secret Manager first (for production)
        try:
            return self.get_secret(secret_id, version)
        except Exception:
            # Fallback to environment variable (for local development)
            value = os.getenv(env_var)
            if value is None:
                raise ValueError(
                    f"Secret '{secret_id}' not found in Secret Manager "
                    f"and environment variable '{env_var}' is not set"
                )
            return value

    def create_secret(self, secret_id: str, secret_value: str) -> str:
        """
        Create a new secret in Secret Manager.

        Args:
            secret_id: The ID for the new secret
            secret_value: The value to store

        Returns:
            str: The resource name of the created secret

        Raises:
            Exception: If secret creation fails
        """
        try:
            parent = f"projects/{self.project_id}"

            # Create the secret
            secret = self.client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {
                        "replication": {"automatic": {}},
                    },
                }
            )

            self.client.add_secret_version(
                request={
                    "parent": secret.name,
                    "payload": {"data": secret_value.encode("UTF-8")},
                }
            )

            return secret.name

        except Exception as e:
            raise Exception(f"Failed to create secret '{secret_id}': {str(e)}")

    def update_secret(self, secret_id: str, secret_value: str) -> str:
        """
        Update a secret by adding a new version.

        Args:
            secret_id: The ID of the secret to update
            secret_value: The new value to store

        Returns:
            str: The resource name of the new secret version

        Raises:
            Exception: If secret update fails
        """

        try:
            parent = f"projects/{self.project_id}/secrets/{secret_id}"

            # Add a new secret version
            version = self.client.add_secret_version(
                request={
                    "parent": parent,
                    "payload": {"data": secret_value.encode("UTF-8")},
                }
            )

            return version.name

        except Exception as e:
            raise Exception(f"Failed to update secret '{secret_id}': {str(e)}")

    def delete_secret(self, secret_id: str) -> None:
        """
        Delete a secret from Secret Manager.

        Args:
            secret_id: The ID of the secret to delete

        Raises:
            Exception: If secret deletion fails
        """

        try:
            name = f"projects/{self.project_id}/secrets/{secret_id}"
            self.client.delete_secret(request={"name": name})

        except Exception as e:
            raise Exception(f"Failed to delete secret '{secret_id}': {str(e)}")
