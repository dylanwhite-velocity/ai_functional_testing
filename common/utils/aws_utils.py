"""This module provides utility functions for interacting with AWS services."""

import boto3
from botocore.exceptions import ClientError
from loguru import logger


def get_secret(secret_name: str) -> str:
    """Retrieve a Secret from AWS Secrets Manager.

    Args:
        secret_name: The name of the secret to retrieve.

    Returns:
        The secret value.
    """
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name="us-west-2")

    try:
        logger.debug(f"Retrieving secret from AWS Secrets Manager: {secret_name}")
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise AWSSUTConfigError(f"Failed to retrieve the SUTConfig from AWS: {e}") from e

    secret = get_secret_value_response["SecretString"]
    return secret


def list_secrets_with_prefix(prefix: str, region_name: str | None = None) -> list[str]:
    """Return a list of AWS Secrets Manager secret names that start with the given prefix.

    Optionally specify the AWS region.
    """
    client = boto3.client("secretsmanager", region_name=region_name)
    secrets = []
    paginator = client.get_paginator("list_secrets")
    for page in paginator.paginate():
        for secret in page.get("SecretList", []):
            name = secret.get("Name", "")
            if name.startswith(prefix):
                secrets.append(name)
    return secrets


class AWSSUTConfigError(Exception):
    """An error occurred while retrieving the SUTConfig from AWS."""

    pass
