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

API_KEY = os.getenv("API_KEY")

# Load templates from JSON file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_PATH = os.path.join(SCRIPT_DIR, "resources", "qa_templates.json")

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
        url=f"https://studio.premai.io{endpoint}",
        headers={"Authorization": f"Bearer {API_KEY}", **kwargs.pop("headers", {})},
        **kwargs
    )
    if not response.ok:
        err = response.json() if response.content else {}
        error_msg = err.get("error", str(err)) if isinstance(err, dict) else str(err)
        raise Exception(f"{response.status_code}: {error_msg}")
    return response.json()


def create_response_safety_dataset(project_id: str):
    """Create dataset for response safety classification"""
    print("   Creating response safety dataset...")

    template = TEMPLATES["response_safety"]
    question_format = template["question_format"]
    answer_format = template["answer_format"]

    form_data = {
        "project_id": project_id,
        "name": "Response Safety Classification Dataset",
        "pairs_to_generate": "50",
        "pair_type": "qa",
        "temperature": "0.3",
        "rules[]": template["rules"],
        "question_format": question_format,
        "answer_format": answer_format
    }

    # Add web URLs
    for i, url in enumerate(WEB_URLS):
        form_data[f"web_urls[{i}]"] = url

    result = api("/api/v1/public/datasets/create-synthetic", method="POST", data=form_data)
    return result["dataset_id"]


def create_user_prompt_safety_dataset(project_id: str):
    """Create dataset for user prompt safety classification"""
    print("   Creating user prompt safety dataset...")

    template = TEMPLATES["user_prompt_safety"]
    question_format = template["question_format"]
    answer_format = template["answer_format"]

    form_data = {
        "project_id": project_id,
        "name": "User Prompt Safety Classification Dataset",
        "pairs_to_generate": "50",
        "pair_type": "qa",
        "temperature": "0.3",
        "rules[]": template["rules"],
        "question_format": question_format,
        "answer_format": answer_format
    }

    # Add web URLs
    for i, url in enumerate(WEB_URLS):
        form_data[f"web_urls[{i}]"] = url

    result = api("/api/v1/public/datasets/create-synthetic", method="POST", data=form_data)
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
    result = api(
        "/api/v1/public/projects/create",
        method="POST",
        headers={"Content-Type": "application/json"},
        json={
            "name": "Safety Classification Project",
            "goal": "Generate safety classification datasets for content moderation"
        }
    )
    project_id = result["project_id"]
    print(f"   ✓ Project: {project_id}\n")

    # Generate response safety dataset
    print("2. Generating response safety dataset...")
    print(f"   URLs: {len(WEB_URLS)} web sources")
    response_dataset_id = create_response_safety_dataset(project_id)
    print(f"   ✓ Dataset: {response_dataset_id}")
    print("   Waiting for generation (may take 5-10 minutes)...")
    response_dataset = wait_for_dataset(response_dataset_id)
    print(f"   ✓ Ready: {response_dataset['datapoints_count']} datapoints\n")

    # Generate user prompt safety dataset
    print("3. Generating user prompt safety dataset...")
    print(f"   URLs: {len(WEB_URLS)} web sources")
    user_dataset_id = create_user_prompt_safety_dataset(project_id)
    print(f"   ✓ Dataset: {user_dataset_id}")
    print("   Waiting for generation (may take 5-10 minutes)...")
    user_dataset = wait_for_dataset(user_dataset_id)
    print(f"   ✓ Ready: {user_dataset['datapoints_count']} datapoints\n")

    # Create snapshots
    print("4. Creating snapshots...")
    response_snapshot = api(
        "/api/v1/public/snapshots/create",
        method="POST",
        headers={"Content-Type": "application/json"},
        json={"dataset_id": response_dataset_id, "split_percentage": 80}
    )
    response_snapshot_id = response_snapshot["snapshot_id"]
    print(f"   ✓ Response Safety Snapshot: {response_snapshot_id}")

    user_snapshot = api(
        "/api/v1/public/snapshots/create",
        method="POST",
        headers={"Content-Type": "application/json"},
        json={"dataset_id": user_dataset_id, "split_percentage": 80}
    )
    user_snapshot_id = user_snapshot["snapshot_id"]
    print(f"   ✓ User Prompt Safety Snapshot: {user_snapshot_id}\n")

    # Generate recommendations
    print("5. Generating recommendations...")
    api(
        "/api/v1/public/recommendations/generate",
        method="POST",
        headers={"Content-Type": "application/json"},
        json={"snapshot_id": response_snapshot_id}
    )

    while True:
        time.sleep(5)
        recs = api(f"/api/v1/public/recommendations/{response_snapshot_id}")
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
    print("6. Creating fine-tuning job...")
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
            "snapshot_id": response_snapshot_id,
            "name": "Response Safety Model",
            "experiments": experiments
        }
    )
    job_id = result["job_id"]
    print(f"   ✓ Job: {job_id}\n")

    # Monitor (5 minutes max)
    print("7. Monitoring job...")
    for i in range(30):
        time.sleep(10)
        job = api(f"/api/v1/public/finetuning/{job_id}")
        print(f"   Status: {job['status']}")
        for exp in job["experiments"]:
            print(f"     - Exp #{exp['experiment_number']}: {exp['status']} {exp.get('model_id', '')}")
        if job["status"] != "processing":
            break

    print("\n✓ Done!")
    print(f"\nGenerated datasets:")
    print(f"  - Response Safety: {response_dataset_id} ({response_dataset['datapoints_count']} datapoints)")
    print(f"  - User Prompt Safety: {user_dataset_id} ({user_dataset['datapoints_count']} datapoints)")
    print(f"\nFine-tuning job: {job_id}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"\n✗ Error: {err}")
        exit(1)

