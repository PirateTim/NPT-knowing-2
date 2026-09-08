"""
Helper Script: Manuscript Processing & pgVector Ingestion (Chapter-Level or Full)
Usage:
    python helper_scripts/run_full_pgvector_load.py [--chapter 1]
"""
import os
import sys
import argparse
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from react_agent.tools.manuscript_etl import process_bronze_manuscript, embed_and_load_manuscript

load_dotenv()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Manuscript ETL and pgVector Load")
    parser.add_argument("--chapter", "-c", type=int, default=1, help="Specific chapter number to process/load (default: 1)")
    parser.add_argument("--all", action="store_true", help="Process and load all chapters")
    args = parser.parse_args()

    target_ch = None if args.all else args.chapter

    print("=================================================================")
    print(" NPT FLEET: MANUSCRIPT INGESTION & PGVECTOR LOAD (BILGELADLE)")
    print(f" TARGET CHAPTER: {target_ch if target_ch is not None else 'ALL CHAPTERS'}")
    print("=================================================================")

    # 1. Execute Step 1: Chapter Slicing, Reference Expansion & Syntax Normalization
    print(f"\n[STEP 1] Slicing chapter {target_ch if target_ch is not None else 'all'}, expanding localized references, and normalizing Markdown syntax...")
    res_step1 = process_bronze_manuscript(target_chapter=target_ch)
    print(f"Result: {res_step1}")

    if "[ERROR]" in res_step1:
        print("[FATAL] Step 1 failed. Aborting Step 2.")
        sys.exit(1)

    # 2. Execute Step 2: pgVector Ingestion
    print(f"\n[STEP 2] Paragraph slicing, embedding generation, and pgVector loading into ship.letters_of_marque for chapter {target_ch if target_ch is not None else 'all'}...")
    res_step2 = embed_and_load_manuscript(target_chapter=target_ch)
    print(f"Result: {res_step2}")

    if "[ERROR]" in res_step2:
        print("[FATAL] Step 2 failed.")
        sys.exit(1)

    print("\n=================================================================")
    print(" MANUSCRIPT INGESTION AND VECTOR LOAD COMPLETE SUCCESS")
    print("=================================================================")
