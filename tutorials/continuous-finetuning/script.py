#!/usr/bin/env python3
"""
Continuous Fine-tuning Tutorial
Demonstrates full fine-tuning followed by LoRA fine-tuning on the finetuned model.
"""

import os
import json
import time
import requests

# Base URL for Prem Studio API - change this to point to a different environment if needed
BASE_URL = "https://studio.premai.io"

API_KEY = os.getenv("API_KEY")

# Base model for fine-tuning (using a common finetunable model)
# You can check available models at https://studio.premai.io/public/models
BASE_MODEL_ID = "meta-llama/Llama-3.2-3B-Instruct"

# Dataset paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FULL_FT_DATASET_PATH = os.path.join(SCRIPT_DIR, "resources", "full_ft_dataset.jsonl")
LORA_FT_DATASET_PATH = os.path.join(SCRIPT_DIR, "resources", "lora_ft_dataset.jsonl")

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


def upload_dataset_from_jsonl(project_id: str, dataset_name: str, jsonl_path: str):
    """Upload a dataset from a JSONL file"""
    print(f"   Uploading {dataset_name}...")
    
    with open(jsonl_path, "rb") as f:
        files = {"file": (jsonl_path, f, "application/json")}
        data = {"project_id": project_id, "name": dataset_name}
        result = api("/api/v1/public/datasets/create-from-jsonl", method="POST", files=files, data=data)
    
    return result["dataset_id"]


def wait_for_dataset(dataset_id: str):
    """Wait for dataset processing to complete"""
    checks = 0
    while True:
        time.sleep(5)
        dataset = api(f"/api/v1/public/datasets/{dataset_id}")
        if checks % 6 == 0:
            print(f"   Status: {dataset['status']}, {dataset.get('datapoints_count', 0)} datapoints")
        checks += 1
        if dataset["status"] != "processing":
            break
    return dataset


def wait_for_finetuning_job(job_id: str, max_iterations: int = 120):
    """Wait for fine-tuning job to complete"""
    print("   Monitoring job progress...")
    for i in range(max_iterations):
        time.sleep(10)
        job = api(f"/api/v1/public/finetuning/{job_id}")
        print(f"   Status: {job['status']}")
        for exp in job["experiments"]:
            status = exp.get('status', 'unknown')
            model_id = exp.get('model_id', '')
            exp_num = exp.get('experiment_number', '')
            print(f"     - Exp #{exp_num}: {status} {model_id}")
        
        if job["status"] not in ["processing", "queued"]:
            return job
        
        if i % 6 == 0 and i > 0:
            print(f"   Still processing... (checked {i+1} times, ~{(i+1)*10//60} minutes)")
    
    print("   ⚠ Maximum wait time reached. Job may still be processing.")
    return job


def main():
    print("\n=== Continuous Fine-tuning Tutorial ===\n")
    print("This tutorial demonstrates:")
    print("1. Full fine-tuning on a general software engineering dataset")
    print("2. LoRA fine-tuning on top of the finetuned model using ML engineering dataset\n")

    # Step 1: Create project
    print("Step 1: Creating project...")
    project = api(
        "/api/v1/public/projects/create",
        method="POST",
        headers={"Content-Type": "application/json"},
        json={
            "name": "Continuous Fine-tuning Project",
            "goal": "Demonstrate continuous fine-tuning: full FT followed by LoRA FT"
        }
    )
    project_id = project["project_id"]
    print(f"   ✓ Project: {project_id}\n")

    # Step 2: Upload first dataset (for full fine-tuning)
    print("Step 2: Uploading dataset for full fine-tuning...")
    print(f"   Dataset: General Software Engineering (80 Q&A pairs)")
    full_ft_dataset_id = upload_dataset_from_jsonl(
        project_id,
        "Software Engineering Dataset (Full FT)",
        FULL_FT_DATASET_PATH
    )
    print(f"   ✓ Dataset ID: {full_ft_dataset_id}")
    print("   Waiting for dataset processing...")
    full_ft_dataset = wait_for_dataset(full_ft_dataset_id)
    print(f"   ✓ Ready: {full_ft_dataset.get('datapoints_count', 0)} datapoints\n")

    # Step 3: Create snapshot for full fine-tuning
    print("Step 3: Creating snapshot for full fine-tuning...")
    full_ft_snapshot = api(
        "/api/v1/public/snapshots/create",
        method="POST",
        headers={"Content-Type": "application/json"},
        json={"dataset_id": full_ft_dataset_id, "split_percentage": 80}
    )
    full_ft_snapshot_id = full_ft_snapshot["snapshot_id"]
    print(f"   ✓ Snapshot: {full_ft_snapshot_id}\n")

    # Step 4: Create full fine-tuning job (skip recommendations, use base model directly)
    print("Step 4: Creating full fine-tuning job...")
    print(f"   Base Model: {BASE_MODEL_ID}")
    print("   Method: Full fine-tuning (all parameters)")
    
    full_ft_experiments = [{
        "base_model_id": BASE_MODEL_ID,
        "lora": False,  # Full fine-tuning
        "batch_size": 1,
        "learning_rate_multiplier": 0.00002,
        "n_epochs": 3,
    }]
    
    full_ft_job = api(
        "/api/v1/public/finetuning/create",
        method="POST",
        headers={"Content-Type": "application/json"},
        json={
            "snapshot_id": full_ft_snapshot_id,
            "name": "Full Fine-tuning - Software Engineering",
            "experiments": full_ft_experiments
        }
    )
    full_ft_job_id = full_ft_job["job_id"]
    print(f"   ✓ Job ID: {full_ft_job_id}\n")

    # Step 5: Wait for full fine-tuning to complete
    print("Step 5: Waiting for full fine-tuning to complete...")
    print("   This may take 30-60 minutes depending on dataset size and model...")
    full_ft_result = wait_for_finetuning_job(full_ft_job_id)
    
    if full_ft_result["status"] != "completed":
        print(f"\n✗ Full fine-tuning job failed or incomplete. Status: {full_ft_result['status']}")
        print("   Cannot proceed with LoRA fine-tuning.")
        exit(1)
    
    # Extract the finetuned model ID
    finetuned_model_id = None
    for exp in full_ft_result["experiments"]:
        if exp.get("status") == "completed" and exp.get("model_id"):
            finetuned_model_id = exp["model_id"]
            break
    
    if not finetuned_model_id:
        print("\n✗ Error: Could not find finetuned model ID from completed job.")
        exit(1)
    
    print(f"   ✓ Full fine-tuning completed!")
    print(f"   ✓ Finetuned Model ID: {finetuned_model_id}\n")

    # Step 6: Upload second dataset (for LoRA fine-tuning)
    print("Step 6: Uploading dataset for LoRA fine-tuning...")
    print(f"   Dataset: Machine Learning Engineering (80 Q&A pairs)")
    print("   This dataset deep dives into ML engineering topics")
    lora_ft_dataset_id = upload_dataset_from_jsonl(
        project_id,
        "ML Engineering Dataset (LoRA FT)",
        LORA_FT_DATASET_PATH
    )
    print(f"   ✓ Dataset ID: {lora_ft_dataset_id}")
    print("   Waiting for dataset processing...")
    lora_ft_dataset = wait_for_dataset(lora_ft_dataset_id)
    print(f"   ✓ Ready: {lora_ft_dataset.get('datapoints_count', 0)} datapoints\n")

    # Step 7: Create snapshot for LoRA fine-tuning
    print("Step 7: Creating snapshot for LoRA fine-tuning...")
    lora_ft_snapshot = api(
        "/api/v1/public/snapshots/create",
        method="POST",
        headers={"Content-Type": "application/json"},
        json={"dataset_id": lora_ft_dataset_id, "split_percentage": 80}
    )
    lora_ft_snapshot_id = lora_ft_snapshot["snapshot_id"]
    print(f"   ✓ Snapshot: {lora_ft_snapshot_id}\n")

    # Step 8: Create LoRA fine-tuning job on top of the finetuned model
    print("Step 8: Creating LoRA fine-tuning job...")
    print(f"   Base Model: {finetuned_model_id} (the previously finetuned model)")
    print("   Method: LoRA fine-tuning (low-rank adaptation)")
    print("   This adapts the finetuned model to ML engineering specifics")
    
    lora_ft_experiments = [{
        "base_model_id": finetuned_model_id,  # Use the finetuned model as base
        "lora": True,  # LoRA fine-tuning
        "batch_size": 1,
        "learning_rate_multiplier": 0.00002,
        "n_epochs": 3,
    }]
    
    lora_ft_job = api(
        "/api/v1/public/finetuning/create",
        method="POST",
        headers={"Content-Type": "application/json"},
        json={
            "snapshot_id": lora_ft_snapshot_id,
            "name": "LoRA Fine-tuning - ML Engineering",
            "experiments": lora_ft_experiments
        }
    )
    lora_ft_job_id = lora_ft_job["job_id"]
    print(f"   ✓ Job ID: {lora_ft_job_id}\n")

    # Step 9: Wait for LoRA fine-tuning to complete
    print("Step 9: Waiting for LoRA fine-tuning to complete...")
    print("   LoRA fine-tuning is typically faster than full fine-tuning...")
    lora_ft_result = wait_for_finetuning_job(lora_ft_job_id)
    
    # Extract the final model ID
    final_model_id = None
    for exp in lora_ft_result["experiments"]:
        if exp.get("status") == "completed" and exp.get("model_id"):
            final_model_id = exp["model_id"]
            break

    print("\n" + "="*60)
    print("✓ Continuous Fine-tuning Complete!")
    print("="*60)
    print(f"\nSummary:")
    print(f"  Project ID: {project_id}")
    print(f"\nFull Fine-tuning:")
    print(f"  Dataset: {full_ft_dataset_id} ({full_ft_dataset.get('datapoints_count', 0)} datapoints)")
    print(f"  Snapshot: {full_ft_snapshot_id}")
    print(f"  Job: {full_ft_job_id}")
    print(f"  Finetuned Model: {finetuned_model_id}")
    print(f"\nLoRA Fine-tuning:")
    print(f"  Dataset: {lora_ft_dataset_id} ({lora_ft_dataset.get('datapoints_count', 0)} datapoints)")
    print(f"  Snapshot: {lora_ft_snapshot_id}")
    print(f"  Job: {lora_ft_job_id}")
    if final_model_id:
        print(f"  Final Model: {final_model_id}")
    print(f"\nThe final model has been:")
    print(f"  1. Fully fine-tuned on general software engineering topics")
    print(f"  2. LoRA fine-tuned on ML engineering specifics")
    print(f"  This demonstrates continuous fine-tuning workflow!\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"\n✗ Error: {err}")
        import traceback
        traceback.print_exc()
        exit(1)

