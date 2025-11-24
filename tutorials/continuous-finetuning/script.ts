/**
 * Continuous Fine-tuning Tutorial
 * Demonstrates full fine-tuning followed by LoRA fine-tuning on the finetuned model.
 */

import * as fs from "fs";
import * as path from "path";

// Base URL for Prem Studio API - change this to point to a different environment if needed
const BASE_URL = "https://studio.premai.io";

const API_KEY = process.env.API_KEY;

// Base model for fine-tuning (using a common finetunable model)
// You can check available models at https://studio.premai.io/public/models
const BASE_MODEL_ID = "meta-llama/Llama-3.2-3B-Instruct";

// Dataset paths
const SCRIPT_DIR = __dirname;
const FULL_FT_DATASET_PATH = path.join(SCRIPT_DIR, "resources", "full_ft_dataset.jsonl");
const LORA_FT_DATASET_PATH = path.join(SCRIPT_DIR, "resources", "lora_ft_dataset.jsonl");

if (!API_KEY) {
  console.error("Error: API_KEY environment variable is required");
  process.exit(1);
}

async function api(endpoint: string, method: string = "GET", options: RequestInit = {}) {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method,
    headers: {
      Authorization: `Bearer ${API_KEY}`,
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    const errorMsg = err.error || JSON.stringify(err);
    throw new Error(`${response.status}: ${errorMsg}`);
  }

  return response.json();
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function uploadDatasetFromJsonl(
  projectId: string,
  datasetName: string,
  jsonlPath: string
): Promise<string> {
  console.log(`   Uploading ${datasetName}...`);

  const formData = new FormData();
  formData.append("project_id", projectId);
  formData.append("name", datasetName);
  
  // Use Bun's file() function as shown in docs: https://docs.premai.io/api-reference/walkthroughs/jsonl-workflow
  // @ts-ignore - Bun global available in Bun runtime
  const jsonlFile = typeof Bun !== "undefined" ? Bun.file(jsonlPath) : new Blob([fs.readFileSync(jsonlPath)], { type: "application/json" });
  formData.append("file", jsonlFile, jsonlPath);

  const response = await fetch(`${BASE_URL}/api/v1/public/datasets/create-from-jsonl`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${API_KEY}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    const errorMsg = err.error || JSON.stringify(err);
    throw new Error(`${response.status}: ${errorMsg}`);
  }

  const result = await response.json();
  return result.dataset_id;
}

async function waitForDataset(datasetId: string) {
  let checks = 0;
  while (true) {
    await sleep(5000);
    const dataset = await api(`/api/v1/public/datasets/${datasetId}`);
    if (checks % 6 === 0) {
      console.log(`   Status: ${dataset.status}, ${dataset.datapoints_count || 0} datapoints`);
    }
    checks++;
    if (dataset.status !== "processing") {
      return dataset;
    }
  }
}

async function waitForFinetuningJob(jobId: string, maxIterations: number = 120) {
  console.log("   Monitoring job progress...");
  for (let i = 0; i < maxIterations; i++) {
    await sleep(10000);
    const job = await api(`/api/v1/public/finetuning/${jobId}`);
    console.log(`   Status: ${job.status}`);
    job.experiments.forEach((exp: any) => {
      const status = exp.status || "unknown";
      const modelId = exp.model_id || "";
      const expNum = exp.experiment_number || "";
      console.log(`     - Exp #${expNum}: ${status} ${modelId}`);
    });

    if (!["processing", "queued"].includes(job.status)) {
      return job;
    }

    if (i % 6 === 0 && i > 0) {
      console.log(`   Still processing... (checked ${i + 1} times, ~${Math.floor((i + 1) * 10 / 60)} minutes)`);
    }
  }

  console.log("   ⚠ Maximum wait time reached. Job may still be processing.");
  return await api(`/api/v1/public/finetuning/${jobId}`);
}

async function main() {
  console.log("\n=== Continuous Fine-tuning Tutorial ===\n");
  console.log("This tutorial demonstrates:");
  console.log("1. Full fine-tuning on a general software engineering dataset");
  console.log("2. LoRA fine-tuning on top of the finetuned model using ML engineering dataset\n");

  // Step 1: Create project
  console.log("Step 1: Creating project...");
  const project = await api("/api/v1/public/projects/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: "Continuous Fine-tuning Project",
      goal: "Demonstrate continuous fine-tuning: full FT followed by LoRA FT",
    }),
  });
  const projectId = project.project_id;
  console.log(`   ✓ Project: ${projectId}\n`);

  // Step 2: Upload first dataset (for full fine-tuning)
  console.log("Step 2: Uploading dataset for full fine-tuning...");
  console.log(`   Dataset: General Software Engineering (80 Q&A pairs)`);
  const fullFtDatasetId = await uploadDatasetFromJsonl(
    projectId,
    "Software Engineering Dataset (Full FT)",
    FULL_FT_DATASET_PATH
  );
  console.log(`   ✓ Dataset ID: ${fullFtDatasetId}`);
  console.log("   Waiting for dataset processing...");
  const fullFtDataset = await waitForDataset(fullFtDatasetId);
  console.log(`   ✓ Ready: ${fullFtDataset.datapoints_count || 0} datapoints\n`);

  // Step 3: Create snapshot for full fine-tuning
  console.log("Step 3: Creating snapshot for full fine-tuning...");
  const fullFtSnapshot = await api("/api/v1/public/snapshots/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset_id: fullFtDatasetId, split_percentage: 80 }),
  });
  const fullFtSnapshotId = fullFtSnapshot.snapshot_id;
  console.log(`   ✓ Snapshot: ${fullFtSnapshotId}\n`);

  // Step 4: Create full fine-tuning job (skip recommendations, use base model directly)
  console.log("Step 4: Creating full fine-tuning job...");
  console.log(`   Base Model: ${BASE_MODEL_ID}`);
  console.log("   Method: Full fine-tuning (all parameters)");

  const fullFtExperiments = [
    {
      base_model_id: BASE_MODEL_ID,
      lora: false, // Full fine-tuning
      batch_size: 1,
      learning_rate_multiplier: 0.00002,
      n_epochs: 3,
    },
  ];

  const fullFtJob = await api("/api/v1/public/finetuning/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      snapshot_id: fullFtSnapshotId,
      name: "Full Fine-tuning - Software Engineering",
      experiments: fullFtExperiments,
    }),
  });
  const fullFtJobId = fullFtJob.job_id;
  console.log(`   ✓ Job ID: ${fullFtJobId}\n`);

  // Step 5: Wait for full fine-tuning to complete
  console.log("Step 5: Waiting for full fine-tuning to complete...");
  console.log("   This may take 30-60 minutes depending on dataset size and model...");
  const fullFtResult = await waitForFinetuningJob(fullFtJobId);

  if (fullFtResult.status !== "completed") {
    console.log(`\n✗ Full fine-tuning job failed or incomplete. Status: ${fullFtResult.status}`);
    console.log("   Cannot proceed with LoRA fine-tuning.");
    process.exit(1);
  }

  // Extract the finetuned model ID
  let finetunedModelId: string | null = null;
  for (const exp of fullFtResult.experiments) {
    if (exp.status === "succeeded" && exp.model_id) {
      finetunedModelId = exp.model_id;
      break;
    }
  }

  if (!finetunedModelId) {
    console.log("\n✗ Error: Could not find finetuned model ID from completed job.");
    process.exit(1);
  }

  console.log(`   ✓ Full fine-tuning completed!`);
  console.log(`   ✓ Finetuned Model ID: ${finetunedModelId}\n`);

  // Step 6: Upload second dataset (for LoRA fine-tuning)
  console.log("Step 6: Uploading dataset for LoRA fine-tuning...");
  console.log(`   Dataset: Machine Learning Engineering (80 Q&A pairs)`);
  console.log("   This dataset deep dives into ML engineering topics");
  const loraFtDatasetId = await uploadDatasetFromJsonl(
    projectId,
    "ML Engineering Dataset (LoRA FT)",
    LORA_FT_DATASET_PATH
  );
  console.log(`   ✓ Dataset ID: ${loraFtDatasetId}`);
  console.log("   Waiting for dataset processing...");
  const loraFtDataset = await waitForDataset(loraFtDatasetId);
  console.log(`   ✓ Ready: ${loraFtDataset.datapoints_count || 0} datapoints\n`);

  // Step 7: Create snapshot for LoRA fine-tuning
  console.log("Step 7: Creating snapshot for LoRA fine-tuning...");
  const loraFtSnapshot = await api("/api/v1/public/snapshots/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset_id: loraFtDatasetId, split_percentage: 80 }),
  });
  const loraFtSnapshotId = loraFtSnapshot.snapshot_id;
  console.log(`   ✓ Snapshot: ${loraFtSnapshotId}\n`);

  // Step 8: Create LoRA fine-tuning job on top of the finetuned model
  console.log("Step 8: Creating LoRA fine-tuning job...");
  console.log(`   Base Model: ${finetunedModelId} (the previously finetuned model)`);
  console.log("   Method: LoRA fine-tuning (low-rank adaptation)");
  console.log("   This adapts the finetuned model to ML engineering specifics");

  const loraFtExperiments = [
    {
      base_model_id: finetunedModelId, // Use the finetuned model as base
      lora: true, // LoRA fine-tuning
      batch_size: 1,
      learning_rate_multiplier: 0.00002,
      n_epochs: 3,
    },
  ];

  const loraFtJob = await api("/api/v1/public/finetuning/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      snapshot_id: loraFtSnapshotId,
      name: "LoRA Fine-tuning - ML Engineering",
      experiments: loraFtExperiments,
    }),
  });
  const loraFtJobId = loraFtJob.job_id;
  console.log(`   ✓ Job ID: ${loraFtJobId}\n`);

  // Step 9: Wait for LoRA fine-tuning to complete
  console.log("Step 9: Waiting for LoRA fine-tuning to complete...");
  console.log("   LoRA fine-tuning is typically faster than full fine-tuning...");
  const loraFtResult = await waitForFinetuningJob(loraFtJobId);

  // Extract the final model ID
  let finalModelId: string | null = null;
  for (const exp of loraFtResult.experiments) {
    if (exp.status === "succeeded" && exp.model_id) {
      finalModelId = exp.model_id;
      break;
    }
  }

  console.log("\n" + "=".repeat(60));
  console.log("✓ Continuous Fine-tuning Complete!");
  console.log("=".repeat(60));
  console.log(`\nSummary:`);
  console.log(`  Project ID: ${projectId}`);
  console.log(`\nFull Fine-tuning:`);
  console.log(`  Dataset: ${fullFtDatasetId} (${fullFtDataset.datapoints_count || 0} datapoints)`);
  console.log(`  Snapshot: ${fullFtSnapshotId}`);
  console.log(`  Job: ${fullFtJobId}`);
  console.log(`  Finetuned Model: ${finetunedModelId}`);
  console.log(`\nLoRA Fine-tuning:`);
  console.log(`  Dataset: ${loraFtDatasetId} (${loraFtDataset.datapoints_count || 0} datapoints)`);
  console.log(`  Snapshot: ${loraFtSnapshotId}`);
  console.log(`  Job: ${loraFtJobId}`);
  if (finalModelId) {
    console.log(`  Final Model: ${finalModelId}`);
  }
  console.log(`\nThe final model has been:`);
  console.log(`  1. Fully fine-tuned on general software engineering topics`);
  console.log(`  2. LoRA fine-tuned on ML engineering specifics`);
  console.log(`  This demonstrates continuous fine-tuning workflow!\n`);
}

main().catch((err) => {
  console.error("\n✗ Error:", err.message);
  process.exit(1);
});

