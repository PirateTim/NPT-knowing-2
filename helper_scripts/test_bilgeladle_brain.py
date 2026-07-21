"""
Helper Script: Bilgeladle Brain Sandbox Pre-Check (Chapter 1 Dry Run)
Usage:
    python helper_scripts/test_bilgeladle_brain.py
"""
import os
from dotenv import load_dotenv
from src.react_agent.tools.manuscript_etl import process_bronze_manuscript, embed_and_load_manuscript

# Load database wire targets and environment keys
load_dotenv()

BRONZE_PATH = "gs://npt-ship/2026-02-24AChapters_complete.md"
SILVER_DIR = "gs://npt-ship/manuscript/silver"

if __name__ == "__main__":
    print("==================================================")
    print(" STARTING LOW-COST PRE-CHECK: BILGELADLE BRAIN")
    print("==================================================")
    
    # 1. Execute the Chapter-Isolated Text Transformation
    print("\n[PHASE 1] Slicing and enriching Chapter 1...")
    try:
        process_bronze_manuscript(BRONZE_PATH, SILVER_DIR, target_chapter=1)
        print("[SUCCESS] Chapter 1 silver markdown written to GCS.")
    except Exception as e:
        print(f"[FATAL ERROR] Phase 1 failed: {str(e)}")
        exit(1)
        
    # 2. Execute the Cost-Controlled Vector Population
    print("\n[PHASE 2] Splitting, hashing, and embedding Chapter 1 chunks...")
    try:
        embed_and_load_manuscript(SILVER_DIR, target_chapter=1)
        print("[SUCCESS] Chapter 1 vectors loaded into ship.letters_of_marque.")
    except Exception as e:
        print(f"[FATAL ERROR] Phase 2 failed: {str(e)}")
        exit(1)

    print("\n==================================================")
    print(" PRE-CHECK COMPLETE: SANDBOX OPERATION SUCCESSFUL")
    print("==================================================")
