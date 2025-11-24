#!/usr/bin/env python3
"""
Generate Safety Classification Dataset from Web Sources
Create synthetic Q&A pairs for both response and user prompt safety classification
using Llama Guard 3 templates.
"""

import os
import json
import time
import requests

# Base URL for Prem Studio API - change this to point to a different environment if needed
BASE_URL = "https://studio.premai.io"

API_KEY = os.getenv("API_KEY")

# Load templates from JSON file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_PATH = os.path.join(SCRIPT_DIR, "..", "resources", "qa_templates.json")

with open(TEMPLATES_PATH, "r") as f:
    TEMPLATES = json.load(f)

# Define web sources (10 pages from Anthropic HH-RLHF dataset)
WEB_URLS = [
    f"https://huggingface.co/datasets/Anthropic/hh-rlhf/viewer/default/train?p={i}"
    for i in range(1, 11)
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

    # Prepare form data as list of tuples for multipart/form-data (allows duplicate keys for arrays)
    form_data = [
        ("project_id", project_id),
        ("name", dataset_name),
        ("pairs_to_generate", "50"),
        ("temperature", "0.0"),
        ("question_format", question_format),
        ("answer_format", answer_format),
        ("rules[]", rules),
    ]

    # Add website URLs as array (each URL as separate entry with website_urls[idx] key, indexed like youtube_urls)
    for idx, url in enumerate(WEB_URLS):
        form_data.append((f"website_urls[{idx}]", url))

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
    print("\n=== Web Synthetic Safety Dataset Workflow ===\n")

    # Create project
    print("1. Creating project...")
    project = api(
        "/api/v1/public/projects/create",
        method="POST",
        headers={"Content-Type": "application/json"},
        json={
            "name": "Safety Classification Project",
            "goal": "Generate response safety classification dataset for content moderation"
        }
    )
    project_id = project["project_id"]
    print(f"   ✓ Project: {project_id}\n")

    # Generate response safety dataset
    print("2. Generating response safety dataset...")
    print(f"   URLs: {len(WEB_URLS)} web sources")
    print(f"   Using response_safety template with {len(TEMPLATES['response_safety']['rules'])} rules")
    dataset_id = create_synthetic_dataset(
        project_id,
        "Response Safety Classification Dataset",
        "response_safety"
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
            "name": "Response Safety Model",
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
    print(f"\nGenerated dataset:")
    print(f"  - Response Safety: {dataset_id} ({dataset['datapoints_count']} datapoints)")
    print(f"\nFine-tuning job: {job_id}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"\n✗ Error: {err}")
        exit(1)

