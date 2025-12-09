#!/usr/bin/env python3
"""
Dataset Quality Labeling
Automatically label datapoints in a dataset based on quality criteria.
"""

import os
import sys
import requests

# Base URL for Prem Studio API - change this to point to a different environment if needed
BASE_URL = "https://studio.premai.io"

API_KEY = os.getenv("API_KEY")

if not API_KEY:
    print("Error: API_KEY environment variable is required")
    exit(1)


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
    
    # Step 1: Dataset ID (static value - replace with your actual dataset ID)
    print("Step 1: Dataset Selection")
    dataset_id = "your-dataset-id-here"  # Replace with your actual dataset ID
    
    print(f"   Using dataset ID: {dataset_id}")
    
    # Verify dataset exists
    print("   Verifying dataset...")
    try:
        dataset = get_dataset_info(dataset_id)
        print(f"   ✓ Dataset found: {dataset.get('name', 'N/A')}")
        print(f"   ✓ Datapoints: {dataset.get('datapoints_count', 0)}")
    except Exception as e:
        print(f"\n✗ Error: Could not access dataset. {e}")
        print("   Please update the dataset_id variable in the script with your actual dataset ID.")
        exit(1)
    
    if dataset.get('datapoints_count', 0) == 0:
        print("\n✗ Error: Dataset has no datapoints to label.")
        exit(1)
    
    print()
    
    # Step 2: Create label definitions
    print("Step 2: Create Label Definitions")
    quality_labels = define_quality_labels()
    
    print(f"\n   Summary of labels:")
    for label_name, description in quality_labels.items():
        print(f"     - {label_name}: {description[:50]}...")
    print()
    
    # Step 3: Create labels
    print("Step 3: Creating Labels")
    try:
        create_result = create_labels(dataset_id, quality_labels)
        print(f"   ✓ {create_result.get('message', 'Labels created successfully')}")
    except Exception as e:
        print(f"\n✗ Error creating labels: {e}")
        exit(1)
    
    # Step 4: Start auto-labeling
    print("\nStep 4: Starting Auto-Labeling")
    try:
        labeling_result = start_auto_labeling(dataset_id)
        print(f"   ✓ {labeling_result.get('message', 'Auto-labeling started successfully')}")
        print("   The labeling process is running in the background.")
    except Exception as e:
        print(f"\n✗ Error starting auto-labeling: {e}")
        exit(1)
    
    print("\n✓ Done!")
    print(f"\nDataset: {dataset_id}")
    print(f"Quality labels applied: {', '.join(quality_labels.keys())}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"\n✗ Error: {err}")
        exit(1)

