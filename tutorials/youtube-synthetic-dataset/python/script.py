#!/usr/bin/env python3
"""
Generate Synthetic Dataset from YouTube Videos
Create synthetic Q&A pairs for extracting investment insights from financial videos.
"""

import os
import json
import time
import requests

# Base URL for Prem Studio API
BASE_URL = "https://studio.premai.io"

API_KEY = os.getenv("API_KEY")

# Load templates from JSON file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_PATH = os.path.join(SCRIPT_DIR, "..", "resources", "templates.json")

with open(TEMPLATES_PATH, "r") as f:
    TEMPLATES = json.load(f)

# Define YouTube videos to analyze
YOUTUBE_URLS = [
    "https://www.youtube.com/watch?v=JH-k5f4Yclc",
    "https://www.youtube.com/watch?v=YEWhxcpMS1c",
    "https://www.youtube.com/watch?v=cb8up3HVXis",
    "https://www.youtube.com/watch?v=26xatIiMv88",
    "https://www.youtube.com/watch?v=-Da3gUdzCvs"
]

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

    # Prepare form data
    form_data = [
        ("project_id", project_id),
        ("name", dataset_name),
        ("pairs_to_generate", "50"),
        ("pair_type", "qa"),
        ("temperature", "0.3"),
        ("question_format", question_format),
        ("answer_format", answer_format),
    ]
    
    # Add rules
    for rule in rules:
        form_data.append(("rules[]", rule))

    # Add YouTube URLs
    for idx, url in enumerate(YOUTUBE_URLS):
        form_data.append((f"youtube_urls[{idx}]", url))

    # Use files parameter to force multipart/form-data encoding
    result = api("/api/v1/public/datasets/create-synthetic", method="POST", data=form_data, files={})
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
    print("\n=== YouTube Synthetic Dataset Workflow ===\n")

    # Create project
    print("1. Creating project...")
    project = api(
        "/api/v1/public/projects/create",
        method="POST",
        headers={"Content-Type": "application/json"},
        json={
            "name": "Stock Analysis Project",
            "goal": "Extract investment insights from financial videos"
        }
    )
    project_id = project["project_id"]
    print(f"   ✓ Project: {project_id}\n")

    # Generate synthetic dataset
    print("2. Generating synthetic dataset from YouTube...")
    print(f"   URLs: {len(YOUTUBE_URLS)} financial videos")
    
    dataset_id = create_synthetic_dataset(
        project_id,
        "Financial YouTube Dataset",
        "financial_analysis"
    )
    
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
    recommended_count = sum(1 for e in recs["recommended_experiments"] if e["recommended"])
    print(f"   Total experiments: {len(recs['recommended_experiments'])}, Recommended: {recommended_count}")
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
            "name": "YouTube Model",
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

