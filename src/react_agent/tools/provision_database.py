
"""
NPT Infrastructure Automation Tool: Cloud SQL Provisioning & Initialization
Architecture: Google API Client + Native pg8000 Connection Engine
"""

import os
import time
import pg8000
from googleapiclient.discovery import build

def provision_agent_state_db(instance_name: str, authorized_ip: str) -> str:
    """
    Autonomously provisions a cost-optimized, dev-tier Cloud SQL for PostgreSQL instance on GCP
    and configures firewall whitelisting for the designated IP.
    """
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        return "[ERROR] GCP_PROJECT_ID environment variable is not set."

    try:
        print(f"[GCP] Initializing Cloud SQL Admin API client for project: {project_id}...")
        sql_admin_service = build('sqladmin', 'v1beta4')

        instance_body = {
            "name": instance_name,
            "settings": {
                "tier": "db-f1-micro",
                "dataDiskSizeGb": "10",
                "ipConfiguration": {
                    "authorizedNetworks": [
                        {
                            "name": "local-dev-ip",
                            "value": authorized_ip
                        }
                    ],
                    "ipv4Enabled": True
                },
                "backupConfiguration": {
                    "enabled": False
                },
            },
            "databaseVersion": "POSTGRES_13",
            "region": "us-central1"
        }

        print(f"[GCP] Sending provisioning request for instance '{instance_name}'...")
        request = sql_admin_service.instances().insert(project=project_id, body=instance_body)
        response = request.execute()

        # Wait for the operation to complete
        while True:
            op_request = sql_admin_service.operations().get(project=project_id, operation=response['name'])
            op_response = op_request.execute()
            if op_response['status'] == 'DONE':
                if 'error' in op_response:
                    return f"[ERROR] GCP Deployment execution fault: {op_response['error']['errors']}"
                print(f"[GCP] Instance '{instance_name}' provisioned successfully.")
                break
            print("[GCP] Awaiting instance provisioning completion...")
            time.sleep(30)
            
        get_request = sql_admin_service.instances().get(project=project_id, instance=instance_name)
        get_response = get_request.execute()
        public_ip = get_response['ipAddresses'][0]['ipAddress']

        return f"[SUCCESS] Cloud SQL instance '{instance_name}' provisioned. Public IP: {public_ip}"

    except Exception as e:
        return f"[ERROR] GCP Deployment execution fault: {str(e)}"


def create_database_and_user(instance_ip: str, db_name: str, user_name: str, password: str) -> str:
    """
    Connects directly to the public IP of an active Cloud SQL instance using pg8000
    to build the progeny state database, set up credentials, and apply schemas.
    """
    root_password = password 
    
    print(f"[INFRA] Attempting direct TCP connection to Cloud SQL Instance at IP: {instance_ip}...")
    
    for i in range(4): # Increased retries
        try:
            conn = pg8000.connect(
                user="postgres",
                host=instance_ip,
                password=root_password,
                port=5432,
                timeout=30
            )
            conn.autocommit = True
            cursor = conn.cursor()
            
            print(f"[INFRA] Checking for existing database '{db_name}'...")
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'")
            if not cursor.fetchone():
                print(f"[INFRA] Initializing DDL: Creating database '{db_name}'...")
                cursor.execute(f"CREATE DATABASE {db_name};")
            else:
                print(f"[INFRA] Database '{db_name}' already exists.")

            print(f"[INFRA] Checking for existing user '{user_name}'...")
            cursor.execute(f"SELECT 1 FROM pg_roles WHERE rolname='{user_name}'")
            if not cursor.fetchone():
                print(f"[INFRA] Initializing DDL: Compiling application user roles for '{user_name}'...")
                cursor.execute(f"CREATE USER {user_name} WITH PASSWORD '{password}';")
            else:
                print(f"[INFRA] User '{user_name}' already exists.")
                
            print(f"[INFRA] Granting privileges...")
            cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {user_name};")
            
            cursor.close()
            conn.close()
            
            return f"[SUCCESS] Progeny state database '{db_name}' and application user '{user_name}' successfully configured on host {instance_ip}."
        
        except Exception as err:
            print(f"[WARN] Connection attempt {i+1}/4 failed: {err}. Retrying in 30 seconds...")
            time.sleep(30)
            
    return f"[ERROR] Database DDL initialization failed after multiple retries. Please check firewall rules and instance status."
