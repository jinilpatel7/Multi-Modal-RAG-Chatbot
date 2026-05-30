import os
import json
import pandas as pd

# Scan credentials/ for any .json file — handles any filename
_CREDS_DIR = os.path.join(os.path.dirname(__file__), "..", "credentials")


def _find_credentials_file() -> str | None:
    """Return the first .json file found in credentials/."""
    if not os.path.isdir(_CREDS_DIR):
        return None
    for f in os.listdir(_CREDS_DIR):
        if f.endswith(".json"):
            return os.path.join(_CREDS_DIR, f)
    return None


def load_data_from_bigquery(service_account_json_content: str | None, query: str):
    """
    Execute a BigQuery SQL query and return (DataFrame, error_string).

    Priority:
      1. JSON string passed from UI upload
      2. Any .json file found in credentials/ folder
    """
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account

        # ── Resolve credentials ───────────────────────────────────────────
        if service_account_json_content and service_account_json_content.strip():
            credentials_info = json.loads(service_account_json_content)
        else:
            creds_file = _find_credentials_file()
            if not creds_file:
                return None, (
                    "No credentials found. Upload a Service Account JSON in the sidebar, "
                    "or place it (any .json filename) inside the credentials/ folder."
                )
            with open(creds_file, "r") as f:
                credentials_info = json.load(f)

        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        client = bigquery.Client(credentials=credentials, project=credentials.project_id)
        df = client.query(query).to_dataframe()
        return df, None

    except Exception as e:
        return None, str(e)


def credentials_available() -> bool:
    """True if credentials are available locally (for UI hints)."""
    return _find_credentials_file() is not None


def credentials_filename() -> str | None:
    """Return just the filename of the detected credentials file."""
    f = _find_credentials_file()
    return os.path.basename(f) if f else None
