import os
from typing import Optional

from google.cloud import secretmanager
from functools import lru_cache


class SecretManagerService:
    """Service for accessing secrets from Google Cloud Secret Manager."""

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv("GCS_PROJECT_ID")
        if not self.project_id:
            raise ValueError(
                "GCS_PROJECT_ID must be set in environment or passed to constructor"
            )

        self.client = secretmanager.SecretManagerServiceClient()

    @lru_cache(maxsize=None)
    def get_secret(self, secret_id: str, version: str = "latest") -> str:
        try:
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
            response = self.client.access_secret_version(request={"name": name})
            payload = response.payload.data.decode("UTF-8")
            return payload

        except Exception as e:
            raise Exception(f"Failed to access secret '{secret_id}': {str(e)}")

    def get_secret_or_env(
        self, secret_id: str, env_var: str, version: str = "latest"
    ) -> str:
        try:
            return self.get_secret(secret_id, version)
        except Exception:
            value = os.getenv(env_var)
            if value is None:
                raise ValueError(
                    f"Secret '{secret_id}' not found in Secret Manager "
                    f"and environment variable '{env_var}' is not set"
                )
            return value

    def create_secret(self, secret_id: str, secret_value: str) -> str:
        try:
            parent = f"projects/{self.project_id}"

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
        try:
            parent = f"projects/{self.project_id}/secrets/{secret_id}"

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
        try:
            name = f"projects/{self.project_id}/secrets/{secret_id}"
            self.client.delete_secret(request={"name": name})

        except Exception as e:
            raise Exception(f"Failed to delete secret '{secret_id}': {str(e)}")
