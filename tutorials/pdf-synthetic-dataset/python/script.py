#!/usr/bin/env python3
"""
Generate Synthetic Dataset from PDF Documents
Create synthetic Q&A pairs for extracting structured data from invoice PDFs.
"""

import os
import json
import time
import glob
import requests

# Base URL for Prem Studio API
BASE_URL = "https://studio.premai.io"

API_KEY = os.getenv("API_KEY")

# Load templates from JSON file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(SCRIPT_DIR, "..", "resources")
TEMPLATES_PATH = os.path.join(RESOURCES_DIR, "templates.json")

with open(TEMPLATES_PATH, "r") as f:
    TEMPLATES = json.load(f)

# Define invoice PDF files to process from resources directory
# Find all PDF files in the resources directory
PDF_FILES = sorted(glob.glob(os.path.join(RESOURCES_DIR, "*.pdf")))

if not API_KEY:
    print("Error: API_KEY environment variable is required")
    exit(1)


def api(endpoint: str, method: str = "GET", **kwargs):
    response = requests.request(
        method=method,
        url=f"{BASE_URL}{endpoint}",
        headers={"Authorization": f"Bearer {API_KEY}", **kwargs.pop("headers", {})},
        **kwargs
    )
    if not response.ok:
        err = response.json() if response.content else {}
        error_msg = err.get("error", str(err)) if isinstance(err, dict) else str(err)
        raise Exception(f"{response.status_code}: {error_msg}")
    return response.json()


def create_synthetic_dataset(project_id: str, dataset_name: str, template_key: str):
    """Create synthetic dataset with proper template and rules"""
    print(f"   Creating {dataset_name}...")

    template = TEMPLATES[template_key]
    question_format = template["question_format"]
    answer_format = template["answer_format"]
    rules = template["rules"]

    # Prepare files to upload
    files = []
    for file_path in PDF_FILES:
        if os.path.exists(file_path):
            files.append(('files[]', (os.path.basename(file_path), open(file_path, 'rb'), 'application/pdf')))
        else:
            print(f"   Warning: File {file_path} not found. Skipping.")

    if not files:
        print(f"   Error: No PDF files found in {RESOURCES_DIR}.")
        return None
    
    print(f"   Found {len(files)} PDF files.")

    # Prepare form data
    # We set pairs_to_generate equal to the number of files to ensure 1 pair per file on average/total
    data = {
        "project_id": project_id,
        "name": dataset_name,
        "pairs_to_generate": str(len(files)),
        "pair_type": "qa",
        "temperature": "0",
        "question_format": question_format,
        "answer_format": answer_format,
        "rules[]": rules
    }
    
    # Use files parameter to force multipart/form-data encoding
    result = api("/api/v1/public/datasets/create-synthetic", method="POST", data=data, files=files)
    
    # Close file handles
    for _, (_, f, _) in files:
        f.close()
        
    return result["dataset_id"]


def wait_for_dataset(dataset_id: str):
    """Wait for dataset generation to complete"""
    checks = 0
    while True:
        time.sleep(5)
        dataset = api(f"/api/v1/public/datasets/{dataset_id}")
        if checks % 6 == 0:
            print(f"   Status: {dataset['status']}, {dataset['datapoints_count']} datapoints")
        checks += 1
        if dataset["status"] != "processing":
            break
    return dataset


def main():
    print("\n=== PDF Synthetic Dataset Workflow ===\n")

    # Create project
    print("1. Creating project...")
    project = api(
        "/api/v1/public/projects/create",
        method="POST",
        headers={"Content-Type": "application/json"},
        json={
            "name": "Invoice Extraction Project",
            "goal": "Extract structured data from receipts"
        }
    )
    project_id = project["project_id"]
    print(f"   ✓ Project: {project_id}\n")

    # Generate synthetic dataset
    print("2. Generating synthetic dataset from PDFs...")
    print(f"   Source: {RESOURCES_DIR}")
    
    dataset_id = create_synthetic_dataset(
        project_id,
        "Invoice Receipts Dataset",
        "invoice_extraction"
    )
    
    if not dataset_id:
        exit(1)
    
    print(f"   ✓ Dataset: {dataset_id}")
    print("   Waiting for generation (may take 5-10 minutes)...")
    dataset = wait_for_dataset(dataset_id)
    print(f"   ✓ Ready: {dataset['datapoints_count']} datapoints\n")

    # Create snapshot
    print("3. Creating snapshot...")
    snapshot = api(
        "/api/v1/public/snapshots/create",
        method="POST",
        headers={"Content-Type": "application/json"},
        json={"dataset_id": dataset_id, "split_percentage": 80}
    )
    snapshot_id = snapshot["snapshot_id"]
    print(f"   ✓ Snapshot: {snapshot_id}\n")

    # Generate recommendations
    print("4. Generating recommendations...")
    api(
        "/api/v1/public/recommendations/generate",
        method="POST",
        headers={"Content-Type": "application/json"},
        json={"snapshot_id": snapshot_id}
    )

    while True:
        time.sleep(5)
        recs = api(f"/api/v1/public/recommendations/{snapshot_id}")
        if recs["status"] != "processing":
            break

    print("   ✓ Recommended experiments:")
    recommended_count = len(recs.get("recommended_models", []))
    print(f"   Recommended experiments: {len(recs['recommended_experiments'])}, Total models: {recommended_count}")
    for e in recs["recommended_experiments"]:
        if e["recommended"]:
            print(f"     - {e['base_model_id']} (LoRA: {e['lora']})")
    print()

    # Create fine-tuning job
    print("5. Creating fine-tuning job...")
    experiments = [
        {k: v for k, v in exp.items() if k not in ["recommended", "reason_for_recommendation"]}
        for exp in recs["recommended_experiments"] if exp["recommended"]
    ]

    if not experiments:
        print("\n✗ Error: No recommended experiments found. Cannot create finetuning job.")
        exit(1)

    result = api(
        "/api/v1/public/finetuning/create",
        method="POST",
        headers={"Content-Type": "application/json"},
        json={
            "snapshot_id": snapshot_id,
            "name": "Invoice Extraction Model",
            "experiments": experiments
        }
    )
    job_id = result["job_id"]
    print(f"   ✓ Job: {job_id}\n")

    # Monitor (5 minutes max)
    print("6. Monitoring job...")
    for i in range(30):
        time.sleep(10)
        job = api(f"/api/v1/public/finetuning/{job_id}")
        print(f"   Status: {job['status']}")
        for exp in job["experiments"]:
            print(f"     - Exp #{exp['experiment_number']}: {exp['status']} {exp.get('model_id', '')}")
        if job["status"] != "processing":
            break

    print("\n✓ Done!")
    print(f"\nGenerated dataset: {dataset_id}")
    print(f"Fine-tuning job: {job_id}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"\n✗ Error: {err}")
        exit(1)
