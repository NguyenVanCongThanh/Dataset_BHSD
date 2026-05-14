import os
import subprocess
import argparse

def run_pipeline(limit=None):
    print("=== Phase 1: Processing New Studies ===")
    cmd1 = ["python3", "scripts/add_external_studies.py"]
    if limit:
        cmd1.extend(["--limit", str(limit)])
    
    result1 = subprocess.run(cmd1)
    if result1.returncode != 0:
        print("Error in Phase 1. Aborting.")
        return

    print("\n=== Phase 2: Updating Global Viewer Data ===")
    cmd2 = ["python3", "scripts/create_global_viewer.py"]
    result2 = subprocess.run(cmd2)
    if result2.returncode != 0:
        print("Error in Phase 2. Aborting.")
        return

    print("\n=== Pipeline Execution Finished Successfully ===")
    print("You can now refresh the browser to see the new studies.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master Pipeline for Study Ingestion")
    parser.add_argument("--limit", type=int, default=None, help="Number of new studies to process")
    args = parser.parse_args()
    
    run_pipeline(args.limit)
