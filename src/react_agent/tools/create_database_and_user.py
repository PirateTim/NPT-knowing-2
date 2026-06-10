"""
NPT Infrastructure Automation Tool: Database & User Initialization DDL
Architecture: Native pg8000 Pure-Python Connection Engine
"""

import os
import sys
import time
import pg8000

def create_database_and_user(instance_ip: str, db_name: str, user_name: str, password: str) -> str:
    """
    Connects directly to the public IP of an active Cloud SQL instance using pg8000
    to build the progeny state database, set up credentials, and apply schemas.
    """
    # Grab the root administrative password from the environment to log in initially
    root_password = os.getenv("DB_ROOT_PASSWORD", password) 
    
    print(f"[INFRA] Attempting direct TCP connection to Cloud SQL Instance at IP: {instance_ip}...")
    
    try:
        # Connect to the default 'postgres' maintenance database as the admin user
        conn = pg8000.connect(
            user="postgres",
            host=instance_ip,
            password=root_password,
            port=5432,
            timeout=30
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # 1. Compile the Progeny Storage Database
        print(f"[INFRA] Initializing DDL: Creating database '{db_name}'...")
        try:
            cursor.execute(f"CREATE DATABASE {db_name};")
        except Exception as db_err:
            if "already exists" in str(db_err):
                print(f"[INFRA] Target database '{db_name}' already exists. Skipping allocation.")
            else:
                raise db_err

        # 2. Compile the Application App User
        print(f"[INFRA] Initializing DDL: Compiling application user roles for '{user_name}'...")
        try:
            cursor.execute(f"CREATE USER {user_name} WITH PASSWORD '{password}';")
        except Exception as user_err:
            if "already exists" in str(user_err):
                print(f"[INFRA] Role '{user_name}' already exists. Skipping user configuration.")
            else:
                raise user_err
                
        # 3. Grant Structural Governance Privileges
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {user_name};")
        
        cursor.close()
        conn.close()
        
        return f"[SUCCESS] Progeny state database '{db_name}' and application user '{user_name}' successfully compiled on host {instance_ip}."
        
    except Exception as err:
        return f"[ERROR] Database DDL initialization execution fault: {str(err)}"