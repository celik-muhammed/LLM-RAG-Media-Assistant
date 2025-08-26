import os
import json
import requests
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------- Grafana configuration ----------------
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
GRAFANA_USER = os.getenv("GRAFANA_ADMIN_USER", "admin")
GRAFANA_PASSWORD = os.getenv("GRAFANA_ADMIN_PASSWORD", "admin")

# ---------------- PostgreSQL configuration ----------------
PG_DB = os.getenv("POSTGRES_DB", "media_assistant")
PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_USER = os.getenv("POSTGRES_USER", "admin")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "admin")


def create_api_key():
    auth = (GRAFANA_USER, GRAFANA_PASSWORD)
    headers = {"Content-Type": "application/json"}
    payload = {
        "name": "ProgrammaticKey",
        "role": "Admin",
    }
    response = requests.post(
        f"{GRAFANA_URL}/api/auth/keys",
        json=payload,
        headers=headers,
        auth=auth,
    )

    if response.status_code == 200:
        logger.info("API key created successfully.")
        return response.json()["key"]

    elif response.status_code == 409:  # Conflict, key already exists
        logger.info("API key exists, re-creating...")
        # Find the existing key
        keys_response = requests.get(f"{GRAFANA_URL}/api/auth/keys", auth=auth)
        if keys_response.status_code == 200:
            for key in keys_response.json():
                if key["name"] == "ProgrammaticKey":
                    # Delete the existing key
                    delete_response = requests.delete(
                        f"{GRAFANA_URL}/api/auth/keys/{key['id']}", auth=auth
                    )
                    if delete_response.status_code == 200:
                        print("Existing key deleted")
                        # Create a new key
                        return create_api_key()
        logger.error(f"Failed to create API key: {response.text}")
        return None
    else:
        print(f"Failed to create API key: {response.text}")
        return None


def create_or_update_datasource(api_key, datasource_name="PostgreSQL"):
    """
    Create or update a PostgreSQL datasource in Grafana.
    Returns the datasource UID on success, None on failure.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "name": datasource_name,
        "type": "postgres",
        "url": f"{PG_HOST}:{PG_PORT}",
        "access": "proxy",
        "user": PG_USER,
        "database": PG_DB,
        "basicAuth": False,
        "isDefault": True,
        "jsonData": {"sslmode": "disable", "postgresVersion": 1300},
        "secureJsonData": {"password": PG_PASSWORD},
    }
    print("Datasource payload:")
    print(json.dumps(payload, indent=2))

    # Check if datasource exists, try to get the existing datasource
    response = requests.get(
        f"{GRAFANA_URL}/api/datasources/name/{datasource_name}",
        headers=headers,
    )
    if response.status_code == 200:
        # Datasource exists, let's update it
        datasource_id = response.json()["id"]
        logger.info("Updating existing datasource with ID %s", datasource_id)
        response = requests.put(
            f"{GRAFANA_URL}/api/datasources/{datasource_id}",
            json=payload,
            headers=headers,
        )
    else:
        # Datasource doesn't exist, create a new one
        logger.info("Creating new datasource: %s", datasource_name)
        response = requests.post(
            f"{GRAFANA_URL}/api/datasources",
            json=payload,
            headers=headers,
        )
    print(f"Response status code: {response.status_code}")
    print(f"Response headers: {response.headers}")
    print(f"Response content: {response.text}")

    if response.status_code in [200, 201]:
        logger.info("Datasource created/updated successfully.")
        return response.json().get("datasource", {}).get("uid") or response.json().get("uid")
    logger.error("Failed to create/update datasource: %s", response.text)
    return None


def create_dashboard(api_key, datasource_uid, dashboard_file="dashboard.json"):
    """
    Create or update a Grafana dashboard.
    Updates all panels to use the provided datasource UID.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        with open(dashboard_file, "r") as f:
            dashboard_json = json.load(f)
            print("Dashboard JSON loaded successfully.")
    except FileNotFoundError:
        logger.error("Dashboard file %s not found.", dashboard_file)
        return
    except json.JSONDecodeError as e:
        logger.error("Error decoding dashboard JSON: %s", str(e))
        return

    # Update datasource UID in all panels
    panels_updated = 0
    for panel in dashboard_json.get("panels", []):
        if isinstance(panel.get("datasource"), dict):
            panel["datasource"]["uid"] = datasource_uid
            panels_updated += 1
        if isinstance(panel.get("targets"), list):
            for target in panel["targets"]:
                if isinstance(target.get("datasource"), dict):
                    target["datasource"]["uid"] = datasource_uid
                    panels_updated += 1
    logger.info("Updated datasource UID for %d panels/targets.", panels_updated)

    # Remove keys for new dashboard creation that shouldn't be included when creating a new dashboard
    for key in ["id", "uid", "version"]:
        dashboard_json.pop(key, None)

    # Prepare the payload
    print("Sending dashboard creation request...")
    payload = {
        "dashboard": dashboard_json,
        "overwrite": True,
        "message": "Updated by Python script",
    }
    response = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        headers=headers,
        json=payload,
    )
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.text}")

    if response.status_code == 200:
        logger.info("Dashboard created/updated successfully.")
        return response.json().get("uid")
    logger.error("Failed to create dashboard: %s", response.text)
    return None


def main():
    logger.info("Starting Grafana setup...")

    api_key = create_api_key()
    if not api_key:
        logger.error("API key creation failed. Exiting.")
        return

    datasource_uid = create_or_update_datasource(api_key)
    if not datasource_uid:
        logger.error("Datasource creation failed. Exiting.")
        return

    create_dashboard(api_key, datasource_uid)
    logger.info("Grafana setup completed.")


if __name__ == "__main__":
    main()
