#!/usr/bin/env python3
"""
Dataset Quality Labeling
Automatically label datapoints in a dataset based on quality criteria.
"""

import os
import sys
import requests
from pathlib import Path

# Base URL for Prem Studio API - change this to point to a different environment if needed
BASE_URL = "https://studio.premai.io"

API_KEY = os.getenv("API_KEY")

if not API_KEY:
    print("Error: API_KEY environment variable is required")
    exit(1)

# Path to sample dataset
SCRIPT_DIR = Path(__file__).parent
SAMPLE_DATASET_PATH = SCRIPT_DIR / ".." / "resources" / "sample_dataset.jsonl"


def api(endpoint: str, method: str = "GET", **kwargs):
    """Helper function for API calls"""
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


def define_quality_labels() -> dict:
    """Define quality labels with static criteria"""
    print("\n=== Define Quality Labels ===\n")
    
    # Static quality labels configuration
    quality_labels = {
        "excellent": "Datapoints with exceptional quality: comprehensive, accurate, well-structured responses that demonstrate deep understanding and provide valuable insights. No errors or ambiguities.",
        "good": "Datapoints with solid quality: accurate and useful responses that address the query adequately. Minor improvements possible but overall reliable and informative.",
        "fair": "Datapoints with acceptable quality: responses that partially address the query but may lack depth, clarity, or completeness. Some inaccuracies or gaps present.",
        "poor": "Datapoints with low quality: responses that fail to adequately address the query, contain significant errors, are poorly structured, or provide minimal value."
    }
    
    print("   Quality labels defined:")
    for label_name, description in quality_labels.items():
        print(f"     - {label_name}: {description[:60]}...")
    
    return quality_labels


def create_project(project_name: str, goal: str) -> str:
    """Create a new project"""
    result = api(
        "/api/v1/public/projects/create",
        method="POST",
        headers={"Content-Type": "application/json"},
        json={"name": project_name, "goal": goal}
    )
    return result["project_id"]


def upload_dataset_from_jsonl(project_id: str, dataset_name: str, jsonl_path: Path) -> str:
    """Upload a dataset from a JSONL file"""
    print(f"   Uploading {dataset_name} from {jsonl_path}...")
    
    with open(jsonl_path, "rb") as f:
        files = {"file": (jsonl_path.name, f, "application/json")}
        data = {"project_id": project_id, "name": dataset_name}
        result = api("/api/v1/public/datasets/create-from-jsonl", method="POST", files=files, data=data)
    
    return result["dataset_id"]


def get_dataset_info(dataset_id: str) -> dict:
    """Get dataset information"""
    dataset = api(f"/api/v1/public/datasets/{dataset_id}")
    return dataset


def create_labels(dataset_id: str, quality_labels: dict) -> dict:
    """Create label definitions for the dataset"""
    print(f"\n=== Creating Label Definitions ===\n")
    
    # Prepare label_definitions array for API
    label_definitions = []
    for label_name, description in quality_labels.items():
        label_definitions.append({
            "name": label_name,
            "description": description
        })
    
    # Call create-labels endpoint
    print("   Creating label definitions...")
    result = api(
        f"/api/v1/public/datasets/{dataset_id}/create-labels",
        method="POST",
        headers={"Content-Type": "application/json"},
        json={"label_definitions": label_definitions}
    )
    
    return result


def start_auto_labeling(dataset_id: str) -> dict:
    """Start the auto-labeling process for the dataset"""
    print(f"\n=== Starting Auto-Labeling ===\n")
    
    # Call start-auto-labeling endpoint
    print("   Starting auto-labeling process...")
    result = api(
        f"/api/v1/public/datasets/{dataset_id}/start-auto-labeling",
        method="POST",
        headers={"Content-Type": "application/json"}
    )
    
    return result


def main():
    print("\n=== Dataset Quality Labeling ===\n")
    
    # Step 1: Create project
    print("Step 1: Creating Project")
    try:
        project_id = create_project(
            "Quality Labeling Project",
            "Label dataset datapoints based on quality criteria"
        )
        print(f"   ✓ Project created: {project_id}\n")
    except Exception as e:
        print(f"\n✗ Error creating project: {e}")
        exit(1)
    
    # Step 2: Upload sample dataset
    print("Step 2: Uploading Sample Dataset")
    if not SAMPLE_DATASET_PATH.exists():
        print(f"\n✗ Error: Sample dataset not found at {SAMPLE_DATASET_PATH}")
        exit(1)
    
    try:
        dataset_id = upload_dataset_from_jsonl(
            project_id,
            "Quality Labeling Sample Dataset",
            SAMPLE_DATASET_PATH
        )
        print(f"   ✓ Dataset created: {dataset_id}")
        
        # Wait a moment for dataset to be ready
        import time
        time.sleep(2)
        
        # Verify dataset
        dataset = get_dataset_info(dataset_id)
        print(f"   ✓ Datapoints: {dataset.get('datapoints_count', 0)}\n")
    except Exception as e:
        print(f"\n✗ Error uploading dataset: {e}")
        exit(1)
    
    # Step 3: Define quality labels
    print("Step 3: Define Quality Labels")
    quality_labels = define_quality_labels()
    
    print(f"\n   Summary of labels:")
    for label_name, description in quality_labels.items():
        print(f"     - {label_name}: {description[:50]}...")
    print()
    
    # Step 4: Create labels
    print("Step 4: Creating Label Definitions")
    try:
        create_result = create_labels(dataset_id, quality_labels)
        print(f"   ✓ {create_result.get('message', 'Labels created successfully')}")
    except Exception as e:
        print(f"\n✗ Error creating labels: {e}")
        exit(1)
    
    # Step 5: Start auto-labeling
    print("\nStep 5: Starting Auto-Labeling")
    try:
        labeling_result = start_auto_labeling(dataset_id)
        print(f"   ✓ {labeling_result.get('message', 'Auto-labeling started successfully')}")
        print("   The labeling process is running in the background.")
    except Exception as e:
        print(f"\n✗ Error starting auto-labeling: {e}")
        exit(1)
    
    print("\n✓ Done!")
    print(f"\nProject: {project_id}")
    print(f"Dataset: {dataset_id}")
    print(f"Quality labels applied: {', '.join(quality_labels.keys())}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"\n✗ Error: {err}")
        exit(1)

