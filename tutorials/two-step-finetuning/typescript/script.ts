
import * as fs from "fs";
import * as path from "path";

// Base URL for Prem Studio API
const BASE_URL = "https://studio.premai.io";
const API_KEY = process.env.API_KEY;

const TARGET_MODELS = ["qwen3-0.6b", "granite-4.0-h-1b", "gemma3-1b"];

// Resource paths
const RESOURCES_DIR = path.join(__dirname, "..", "resources");
const ENGLISH_DATASET_PATH = path.join(RESOURCES_DIR, "english_dataset.jsonl");
const TARGET_LANG_DATASET_PATH = path.join(RESOURCES_DIR, "target_language_dataset.jsonl");

function checkFiles() {
  if (!fs.existsSync(ENGLISH_DATASET_PATH)) {
    console.error(`Error: ${ENGLISH_DATASET_PATH} not found.`);
    console.error("Please generate it using the Nemotron tutorial (see README).");
    process.exit(1);
  }
  if (!fs.existsSync(TARGET_LANG_DATASET_PATH)) {
    console.error(`Error: ${TARGET_LANG_DATASET_PATH} not found.`);
    console.error("Please generate it using the Nemotron tutorial (see README).");
    process.exit(1);
  }
}

async function api(endpoint: string, method: string = "GET", options: RequestInit = {}) {
  if (!API_KEY) {
    console.error("Error: API_KEY environment variable is required");
    process.exit(1);
  }

  const { headers: extraHeaders, ...restOptions } = options;
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...restOptions,
    method,
    headers: {
      Authorization: `Bearer ${API_KEY}`,
      ...(extraHeaders || {}),
    },
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

async function uploadDatasetFromJsonl(projectId: string, datasetName: string, filePath: string) {
  console.log(`   Uploading ${datasetName} from ${path.basename(filePath)}...`);
  
  const fileContent = fs.readFileSync(filePath);
  const blob = new Blob([fileContent], { type: "application/json" });
  
  const formData = new FormData();
  formData.append("file", blob, path.basename(filePath));
  formData.append("project_id", projectId);
  formData.append("name", datasetName);

  // Note: standard fetch with FormData automatically sets Content-Type to multipart/form-data with boundary
  // We should NOT set Content-Type manually in headers
  const result = await api("/api/v1/public/datasets/create-from-jsonl", "POST", {
    body: formData,
  });

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

async function waitForFinetuningJob(jobId: string) {
  console.log("   Monitoring job progress...");
  let checks = 0;
  while (true) {
    await sleep(10000);
    const job = await api(`/api/v1/public/finetuning/${jobId}`);
    
    if (checks % 6 === 0) {
      console.log(`   Job Status: ${job.status}`);
      for (const exp of job.experiments || []) {
        console.log(`     - Exp #${exp.experiment_number || '?'}: ${exp.status || 'unknown'} -> ${exp.model_id || 'pending'}`);
      }
    }
    
    if (job.status !== "processing" && job.status !== "queued") {
      return job;
    }
    checks++;
  }
}

async function main() {
  checkFiles();
  console.log("\n=== Two-Step Fine-Tuning Tutorial ===\n");

  // --- GROUP 1: FULL FINE-TUNING ---
  console.log("\n=== GROUP 1: Full Fine-Tuning (English) ===\n");

  // 1. Create Project
  console.log("1. Creating Project 1...");
  const p1 = await api("/api/v1/public/projects/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: "Step 1: Full FT (English)",
      goal: "Full fine-tuning on English safety dataset",
    }),
  });
  const p1Id = p1.project_id;
  console.log(`   ✓ Project ID: ${p1Id}`);

  // 2. Upload Dataset
  console.log("2. Uploading English Dataset...");
  const d1Id = await uploadDatasetFromJsonl(p1Id, "English Safety Dataset", ENGLISH_DATASET_PATH);
  await waitForDataset(d1Id);
  console.log(`   ✓ Dataset ID: ${d1Id}`);

  // 3. Create Snapshot
  console.log("3. Creating Snapshot (95-5 split)...");
  const s1 = await api("/api/v1/public/snapshots/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      dataset_id: d1Id,
      split_percentage: 95,
    }),
  });
  const s1Id = s1.snapshot_id;
  console.log(`   ✓ Snapshot ID: ${s1Id}`);

  // 4. Recommendations
  console.log("4. Generating Recommendations...");
  await api("/api/v1/public/recommendations/generate", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ snapshot_id: s1Id }),
  });

  let recs;
  while (true) {
    await sleep(2000);
    recs = await api(`/api/v1/public/recommendations/${s1Id}`);
    if (recs.status !== "processing") {
      break;
    }
  }

  // 5. Select Models
  console.log("5. Selecting Models...");
  const selectedExperiments: any[] = [];
  
  // 'recommended_models' contains the list of all finetunable models, with the recommended hyperparameters for each model.
  const recModels = recs.recommended_models || [];
  
  if (recModels.length > 0) {
    for (const modelRec of recModels) {
      const baseId = modelRec.base_model_id || "";
      
      let matched = false;
      for (const target of TARGET_MODELS) {
        if (baseId.includes(target)) {
          matched = true;
          break;
        }
      }

      if (matched) {
        // Use full_hyperparameters for this step (Full FT)
        const params = modelRec.full_hyperparameters || {};
        
        selectedExperiments.push({
          base_model_id: baseId,
          lora: false, // Ensure Full FT
          n_epochs: 3, // Override epochs as requested
          batch_size: params.batch_size || 1,
          learning_rate_multiplier: params.learning_rate_multiplier || 0.00002
        });
        console.log(`   Selected: ${baseId} (Batch: ${params.batch_size}, LR: ${params.learning_rate_multiplier})`);
      }
    }
  }

  // Fallback
  if (selectedExperiments.length === 0) {
    console.log("   Warning: No matching models found in recommendations. Using hardcoded config.");
    for (const target of TARGET_MODELS) {
      selectedExperiments.push({
        base_model_id: target,
        lora: false,
        n_epochs: 3,
        learning_rate_multiplier: 0.00002,
        batch_size: 1,
      });
    }
  }

  // 6. Run Experiments
  console.log(`6. Starting Full FT Experiments (${selectedExperiments.length} models)...`);
  const job1 = await api("/api/v1/public/finetuning/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      snapshot_id: s1Id,
      name: "Full FT Job",
      experiments: selectedExperiments,
    }),
  });
  const job1Id = job1.job_id;
  console.log(`   ✓ Job ID: ${job1Id}`);

  const job1Result = await waitForFinetuningJob(job1Id);

  const finetunedModels: any[] = [];
  for (const exp of job1Result.experiments || []) {
    if (exp.status === "succeeded") {
      finetunedModels.push({
        id: exp.model_id,
        base: exp.base_model_id,
      });
    }
  }

  console.log(`   ✓ Completed. Got ${finetunedModels.length} finetuned models.`);
  if (finetunedModels.length === 0) {
    console.error("Error: No models were successfully finetuned.");
    process.exit(1);
  }

  // --- GROUP 2: LoRA FINE-TUNING ---
  console.log("\n=== GROUP 2: LoRA Fine-Tuning (Target Language) ===\n");

  // 1. Create New Project
  console.log("1. Creating Project 2...");
  const p2 = await api("/api/v1/public/projects/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: "Step 2: LoRA FT (Target Lang)",
      goal: "LoRA fine-tuning on top of previously finetuned models",
    }),
  });
  const p2Id = p2.project_id;
  console.log(`   ✓ Project ID: ${p2Id}`);

  // 2. Upload Dataset
  console.log("2. Uploading Target Language Dataset...");
  const d2Id = await uploadDatasetFromJsonl(p2Id, "Target Lang Dataset", TARGET_LANG_DATASET_PATH);
  await waitForDataset(d2Id);
  console.log(`   ✓ Dataset ID: ${d2Id}`);

  // 3. Create Snapshot
  console.log("3. Creating Snapshot (95-5 split)...");
  const s2 = await api("/api/v1/public/snapshots/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      dataset_id: d2Id,
      split_percentage: 95,
    }),
  });
  const s2Id = s2.snapshot_id;
  console.log(`   ✓ Snapshot ID: ${s2Id}`);

  // 4. Recommendations
  console.log("4. Generating Recommendations...");
  await api("/api/v1/public/recommendations/generate", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ snapshot_id: s2Id }),
  });
  
  let recs2;
  while (true) {
    await sleep(2000);
    recs2 = await api(`/api/v1/public/recommendations/${s2Id}`);
    if (recs2.status !== "processing") {
      break;
    }
  }

  // 5. Construct Experiments
  console.log("5. Configuring LoRA Experiments on previous models...");
  const loraExperiments: any[] = [];

  const defaultLoraParams = {
    batch_size: 1,
    learning_rate_multiplier: 0.0002,
  };

  const recModels2 = recs2.recommended_models || [];

  // Try to find a baseline from the first recommended model
  if (recModels2.length > 0) {
    const firstRec = recModels2[0];
    const p = firstRec.lora_hyperparameters || {};
    defaultLoraParams.batch_size = p.batch_size || 1;
    defaultLoraParams.learning_rate_multiplier = p.learning_rate_multiplier || 0.0002;
  }

  for (const ftModel of finetunedModels) {
    // Try to match specific architecture params
    let currentParams = { ...defaultLoraParams };
    
    for (const rec of recModels2) {
      const baseModelId = rec.base_model_id;
      if (baseModelId && ftModel.base === baseModelId) {
        const p = rec.lora_hyperparameters || {};
        if (p.batch_size) currentParams.batch_size = p.batch_size;
        if (p.learning_rate_multiplier) currentParams.learning_rate_multiplier = p.learning_rate_multiplier;
        break;
      }
    }

    loraExperiments.push({
      base_model_id: ftModel.id,
      lora: true,
      n_epochs: 2,
      batch_size: currentParams.batch_size,
      learning_rate_multiplier: currentParams.learning_rate_multiplier
    });
    console.log(`   Configured LoRA for: ${ftModel.id} (Batch: ${currentParams.batch_size}, LR: ${currentParams.learning_rate_multiplier})`);
  }

  // 6. Start Experiments
  console.log("6. Starting LoRA Experiments...");
  const job2 = await api("/api/v1/public/finetuning/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      snapshot_id: s2Id,
      name: "LoRA FT Job",
      experiments: loraExperiments,
    }),
  });
  const job2Id = job2.job_id;
  console.log(`   ✓ Job ID: ${job2Id}`);

  const job2Result = await waitForFinetuningJob(job2Id);

  console.log("\n=== Two-Step Fine-Tuning Complete! ===");
  console.log("Final Models:");
  for (const exp of job2Result.experiments || []) {
    if (exp.status === "succeeded") {
      console.log(` - ${exp.model_id}`);
    }
  }

  console.log("\nFor evaluation, please refer to the Guarding BYOE tutorial.");
}

main().catch((err) => {
  console.error("\n✗ Error:", err.message);
  process.exit(1);
});

