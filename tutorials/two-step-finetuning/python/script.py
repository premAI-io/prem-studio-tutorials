#!/usr/bin/env python3
"""
Two-Step Fine-Tuning Tutorial
Step 1: Full fine-tuning of base models (Qwen, Granite, Gemma) on English dataset
Step 2: LoRA fine-tuning of the output models on Target Language dataset
"""

import os
import json
import time
import requests
import sys
from pathlib import Path

# Base URL for Prem Studio API
BASE_URL = "https://studio.premai.io"

API_KEY = os.getenv("API_KEY")

# Target models for first step (aliases provided by user)
TARGET_MODELS = ["qwen3-0.6b", "granite-4.0-h-1b", "gemma3-1b"]

# Resources paths
SCRIPT_DIR = Path(__file__).parent.absolute()
RESOURCES_DIR = SCRIPT_DIR.parent / "resources"
ENGLISH_DATASET_PATH = RESOURCES_DIR / "english_dataset.jsonl"
TARGET_LANG_DATASET_PATH = RESOURCES_DIR / "target_language_dataset.jsonl"

def check_files():
    if not ENGLISH_DATASET_PATH.exists():
        print(f"Error: {ENGLISH_DATASET_PATH} not found.")
        print("Please generate it using the Nemotron tutorial (see README).")
        sys.exit(1)
    if not TARGET_LANG_DATASET_PATH.exists():
        print(f"Error: {TARGET_LANG_DATASET_PATH} not found.")
        print("Please generate it using the Nemotron tutorial (see README).")
        sys.exit(1)

def api(endpoint: str, method: str = "GET", **kwargs):
    """Helper function for API calls"""
    if not API_KEY:
        print("Error: API_KEY environment variable is required")
        sys.exit(1)
        
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

def upload_dataset_from_jsonl(project_id: str, dataset_name: str, jsonl_path: Path):
    """Upload a dataset from a JSONL file"""
    print(f"   Uploading {dataset_name} from {jsonl_path}...")
    
    with open(jsonl_path, "rb") as f:
        files = {"file": (jsonl_path.name, f, "application/json")}
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

def wait_for_finetuning_job(job_id: str):
    """Wait for fine-tuning job to complete"""
    print("   Monitoring job progress...")
    checks = 0
    while True:
        time.sleep(10)
        job = api(f"/api/v1/public/finetuning/{job_id}")
        
        if checks % 6 == 0:
            print(f"   Job Status: {job['status']}")
            for exp in job.get("experiments", []):
                status = exp.get('status', 'unknown')
                model_id = exp.get('model_id', 'pending')
                exp_num = exp.get('experiment_number', '?')
                print(f"     - Exp #{exp_num}: {status} -> {model_id}")
        
        if job["status"] not in ["processing", "queued"]:
            return job
        checks += 1

def main():
    check_files()
    print("\n=== Two-Step Fine-Tuning Tutorial ===\n")

    # --- GROUP 1: FULL FINE-TUNING ---
    print("\n=== GROUP 1: Full Fine-Tuning (English) ===\n")

    # 1. Create Project
    print("1. Creating Project 1...")
    p1 = api("/api/v1/public/projects/create", "POST", json={
        "name": "Step 1: Full FT (English)",
        "goal": "Full fine-tuning on English safety dataset"
    })
    p1_id = p1["project_id"]
    print(f"   ✓ Project ID: {p1_id}")

    # 2. Upload Dataset
    print("2. Uploading English Dataset...")
    d1_id = upload_dataset_from_jsonl(p1_id, "English Safety Dataset", ENGLISH_DATASET_PATH)
    wait_for_dataset(d1_id)
    print(f"   ✓ Dataset ID: {d1_id}")

    # 3. Create Snapshot
    print("3. Creating Snapshot (95-5 split)...")
    s1 = api("/api/v1/public/snapshots/create", "POST", json={
        "dataset_id": d1_id,
        "split_percentage": 95
    })
    s1_id = s1["snapshot_id"]
    print(f"   ✓ Snapshot ID: {s1_id}")

    # 4. Recommendations
    print("4. Generating Recommendations...")
    api("/api/v1/public/recommendations/generate", "POST", json={"snapshot_id": s1_id})
    
    while True:
        time.sleep(2)
        recs = api(f"/api/v1/public/recommendations/{s1_id}")
        if recs["status"] != "processing":
            break
            
    # 5. Select Models
    print("5. Selecting Models...")
    selected_experiments = []
    
    # We prefer 'recommended_models' which has specific params for full/lora
    # If not present, fallback to 'recommended_experiments' (legacy) or defaults
    rec_models = recs.get("recommended_models", [])
    
    if rec_models:
        for model_rec in rec_models:
            base_id = model_rec.get("base_model_id", "")
            
            # Check if this model matches one of our targets
            matched = False
            for target in TARGET_MODELS:
                if target in base_id:
                    matched = True
                    break
            
            if matched:
                # Use full_hyperparameters for this step (Full FT)
                params = model_rec.get("full_hyperparameters", {})
                
                exp_config = {
                    "base_model_id": base_id,
                    "lora": False, # Ensure Full FT
                    "n_epochs": 3, # Override epochs as requested in tutorial
                    "batch_size": params.get("batch_size", 1),
                    "learning_rate_multiplier": params.get("learning_rate_multiplier", 0.00002)
                }
                
                selected_experiments.append(exp_config)
                print(f"   Selected: {base_id} (Batch: {exp_config['batch_size']}, LR: {exp_config['learning_rate_multiplier']})")

    # Fallback if no models matched or structure wasn't as expected (legacy support)
    if not selected_experiments:
        print("   Warning: No matching models found in recommendations. Using defaults.")
        for target in TARGET_MODELS:
             selected_experiments.append({
                 "base_model_id": target,
                 "lora": False,
                 "n_epochs": 3,
                 "learning_rate_multiplier": 0.00002, 
                 "batch_size": 1
             })

    # 6. Run Experiments
    print(f"6. Starting Full FT Experiments ({len(selected_experiments)} models)...")
    job1 = api("/api/v1/public/finetuning/create", "POST", json={
        "snapshot_id": s1_id,
        "name": "Full FT Job",
        "experiments": selected_experiments
    })
    job1_id = job1["job_id"]
    print(f"   ✓ Job ID: {job1_id}")

    job1_result = wait_for_finetuning_job(job1_id)
    
    finetuned_models = []
    for exp in job1_result.get("experiments", []):
        if exp.get("status") == "completed":
            finetuned_models.append({
                "id": exp.get("model_id"),
                "base": exp.get("base_model_id")
            })
            
    print(f"   ✓ Completed. Got {len(finetuned_models)} finetuned models.")
    if not finetuned_models:
        print("Error: No models were successfully finetuned.")
        sys.exit(1)


    # --- GROUP 2: LoRA FINE-TUNING ---
    print("\n=== GROUP 2: LoRA Fine-Tuning (Target Language) ===\n")

    # 1. Create New Project
    print("1. Creating Project 2...")
    p2 = api("/api/v1/public/projects/create", "POST", json={
        "name": "Step 2: LoRA FT (Target Lang)",
        "goal": "LoRA fine-tuning on top of previously finetuned models"
    })
    p2_id = p2["project_id"]
    print(f"   ✓ Project ID: {p2_id}")

    # 2. Upload Dataset
    print("2. Uploading Target Language Dataset...")
    d2_id = upload_dataset_from_jsonl(p2_id, "Target Lang Dataset", TARGET_LANG_DATASET_PATH)
    wait_for_dataset(d2_id)
    print(f"   ✓ Dataset ID: {d2_id}")

    # 3. Create Snapshot
    print("3. Creating Snapshot (95-5 split)...")
    s2 = api("/api/v1/public/snapshots/create", "POST", json={
        "dataset_id": d2_id,
        "split_percentage": 95
    })
    s2_id = s2["snapshot_id"]
    print(f"   ✓ Snapshot ID: {s2_id}")

    # 4. Recommendations (Optional, but requested)
    print("4. Generating Recommendations...")
    api("/api/v1/public/recommendations/generate", "POST", json={"snapshot_id": s2_id})
    while True:
        time.sleep(2)
        recs2 = api(f"/api/v1/public/recommendations/{s2_id}")
        if recs2["status"] != "processing":
            break
            
    # 5. Construct Experiments using previous models
    print("5. Configuring LoRA Experiments on previous models...")
    lora_experiments = []
    
    # We need to use the previously finetuned models as base.
    # We need appropriate hyperparameters for LoRA.
    # Since the new recommendations are for the *base* models available in the platform, 
    # and not our custom finetuned ones, we will take the generic LoRA params 
    # from the recommendations of the *original* base models (if available) or use general recommendation.
    
    # Default params if recommendation lookup fails
    default_lora_params = {
        "batch_size": 1,
        "learning_rate_multiplier": 0.0002, 
    }
    
    # Try to find a reference set of params from the new recommendations
    rec_models_2 = recs2.get("recommended_models", [])
    
    if rec_models_2:
        # Just grab the first recommended LoRA params as a baseline
        # Ideally we'd match the base model architecture, but for tutorial simplicity we take the first valid one
        first_rec = rec_models_2[0]
        lora_params = first_rec.get("lora_hyperparameters", {})
        if lora_params:
            default_lora_params["batch_size"] = lora_params.get("batch_size", 1)
            default_lora_params["learning_rate_multiplier"] = lora_params.get("learning_rate_multiplier", 0.0002)

    for ft_model in finetuned_models:
        # We can try to match the *original* base model to get specific params if possible
        # but the `finetuned_models` list stores {id, base}. `base` is what we matched earlier.
        
        # Look for specific params for this base architecture in current recommendations
        current_params = default_lora_params.copy()
        
        for rec in rec_models_2:
            if rec.get("base_model_id") and ft_model["base"] in rec.get("base_model_id"):
                 p = rec.get("lora_hyperparameters", {})
                 if p:
                     current_params["batch_size"] = p.get("batch_size", 1)
                     current_params["learning_rate_multiplier"] = p.get("learning_rate_multiplier", 0.0002)
                 break
        
        exp_config = {
            "base_model_id": ft_model["id"],
            "lora": True,
            "n_epochs": 2, # Enforce 2 epochs as requested
            "batch_size": current_params["batch_size"],
            "learning_rate_multiplier": current_params["learning_rate_multiplier"]
        }
        
        lora_experiments.append(exp_config)
        print(f"   Configured LoRA for: {ft_model['id']} (Batch: {exp_config['batch_size']}, LR: {exp_config['learning_rate_multiplier']})")

    # 6. Start Experiments
    print(f"6. Starting LoRA Experiments...")
    job2 = api("/api/v1/public/finetuning/create", "POST", json={
        "snapshot_id": s2_id,
        "name": "LoRA FT Job",
        "experiments": lora_experiments
    })
    job2_id = job2["job_id"]
    print(f"   ✓ Job ID: {job2_id}")

    job2_result = wait_for_finetuning_job(job2_id)
    
    print("\n=== Two-Step Fine-Tuning Complete! ===")
    print("Final Models:")
    for exp in job2_result.get("experiments", []):
        if exp.get("status") == "completed":
            print(f" - {exp.get('model_id')}")

    print("\nFor evaluation, please refer to the Guarding BYOE tutorial.")

if __name__ == "__main__":
    main()

