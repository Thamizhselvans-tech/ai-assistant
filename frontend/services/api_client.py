"""Compatibility wrapper re-exporting APIClient from frontend.api_client."""

from frontend.api_client import APIClient, api_client

__all__ = ["APIClient", "api_client"]
