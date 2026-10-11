"""
NPT Fleet: Resilient Cloud SQL Startup & IP Auto-Authorizer
Description:
Powers ON the Cloud SQL instance, automatically detects the local machine's public IP,
ensures it is authorized in Cloud SQL with /32 CIDR, waits for the instance to become RUNNABLE,
and verifies PostgreSQL port 5432 connectivity.
"""

import os
import sys
import json
import time
import socket
import urllib.request
import subprocess
from dotenv import load_dotenv

load_dotenv(override=True)

INSTANCE_NAME = "npt-instance-postgressql"
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "npt-reckoning-1")

def get_current_public_ip() -> str:
    """Fetches current public IPv4 address."""
    try:
        req = urllib.request.urlopen("https://api.ipify.org", timeout=5)
        return req.read().decode("utf-8").strip()
    except Exception as e:
        print(f"[WARN] Failed to fetch IP from ipify ({e}), trying ifconfig.me...", file=sys.stderr)
        req = urllib.request.urlopen("https://ifconfig.me/ip", timeout=5)
        return req.read().decode("utf-8").strip()

def run_gcloud_json(cmd_list) -> dict:
    """Runs a gcloud command and parses JSON output."""
    full_cmd = ["gcloud"] + cmd_list + ["--format=json"]
    res = subprocess.run(full_cmd, capture_output=True, text=True, shell=True)
    if res.returncode != 0:
        raise RuntimeError(f"gcloud error ({res.returncode}): {res.stderr}")
    return json.loads(res.stdout) if res.stdout.strip() else {}

def is_port_open(host: str, port: int = 5432, timeout: float = 3.0) -> bool:
    """Tests TCP connection to the database port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

def start_and_authorize_db():
    print("="*75)
    print("  NPT FLEET: CLOUD SQL POWER & RESILIENT IP RE-AUTHORIZATION")
    print("="*75)

    # 1. Detect public IP
    my_ip = get_current_public_ip()
    my_cidr = f"{my_ip}/32"
    print(f"[1/5] Detected current local public IP: {my_ip} ({my_cidr})")

    # 2. Inspect Cloud SQL instance
    print(f"[2/5] Inspecting Cloud SQL instance '{INSTANCE_NAME}' in project '{PROJECT_ID}'...")
    info = run_gcloud_json(["sql", "instances", "describe", INSTANCE_NAME, f"--project={PROJECT_ID}"])
    
    state = info.get("state", "UNKNOWN")
    settings = info.get("settings", {})
    policy = settings.get("activationPolicy", "UNKNOWN")
    ip_config = settings.get("ipConfiguration", {})
    authorized_networks = ip_config.get("authorizedNetworks", [])
    
    ip_list = info.get("ipAddresses", [])
    db_ip = next((ip["ipAddress"] for ip in ip_list if ip.get("type") == "PRIMARY"), None)
    print(f"      Instance State: {state} | Policy: {policy} | Primary IP: {db_ip}")

    # 3. Check if IP authorization needs updating
    authorized_cidrs = [net.get("value", "") for net in authorized_networks]
    ip_needs_auth = (my_ip not in authorized_cidrs and my_cidr not in authorized_cidrs)
    policy_needs_start = (policy != "ALWAYS")

    if not policy_needs_start and not ip_needs_auth and state == "RUNNABLE":
        print(f"[3/5] Instance is already ALWAYS active and IP {my_cidr} is authorized.")
    else:
        # Build patch command
        print(f"[3/5] Applying configuration patch (Start={policy_needs_start}, UpdateIP={ip_needs_auth})...")
        
        # Build network list preserving existing names if possible
        new_networks = []
        found_current = False
        for net in authorized_networks:
            val = net.get("value", "")
            # Ensure /32 on single IPs
            val_normalized = val if "/" in val else f"{val}/32"
            if val == my_ip or val == my_cidr:
                val_normalized = my_cidr
                found_current = True
            new_networks.append(val_normalized)
            
        if not found_current:
            new_networks.append(my_cidr)

        net_str = ",".join(new_networks)
        
        patch_cmd = [
            "sql", "instances", "patch", INSTANCE_NAME,
            f"--project={PROJECT_ID}",
            "--activation-policy=ALWAYS",
            f"--authorized-networks={net_str}",
            "--quiet"
        ]
        
        print(f"      Executing: gcloud {' '.join(patch_cmd)}")
        res = subprocess.run(["gcloud"] + patch_cmd, capture_output=True, text=True, shell=True)
        if res.returncode != 0:
            print(f"[ERROR] Patch failed: {res.stderr}", file=sys.stderr)
            sys.exit(1)
        print("      Patch request accepted by Google Cloud.")

    # 4. Wait for RUNNABLE state
    print(f"[4/5] Verifying instance is RUNNABLE...")
    for attempt in range(24): # up to 2 minutes
        curr_info = run_gcloud_json(["sql", "instances", "describe", INSTANCE_NAME, f"--project={PROJECT_ID}"])
        curr_state = curr_info.get("state")
        if curr_state == "RUNNABLE":
            print(f"      Instance confirmed RUNNABLE.")
            break
        print(f"      Waiting for instance (currently {curr_state})... ({attempt+1}/24)")
        time.sleep(5)

    # 5. Verify TCP port 5432
    print(f"[5/5] Testing TCP connectivity to {db_ip}:5432...")
    connected = False
    for attempt in range(12):
        if is_port_open(db_ip, 5432, timeout=2.0):
            connected = True
            break
        print(f"      Waiting for PostgreSQL port 5432 to accept connections... ({attempt+1}/12)")
        time.sleep(3)

    if connected:
        print("\n" + "="*75)
        print("  [SUCCESS] Cloud SQL is ONLINE, AUTHORIZED, and accepting connections!")
        print(f"  Target: {db_ip}:5432 | Authorized IP: {my_cidr}")
        print("="*75 + "\n")
    else:
        print(f"\n[WARNING] Cloud SQL is RUNNABLE, but port 5432 is not responding yet to {my_ip}.", file=sys.stderr)
        print("Wait 10 seconds and test again, or check corporate VPN/firewall settings.", file=sys.stderr)

if __name__ == "__main__":
    start_and_authorize_db()
