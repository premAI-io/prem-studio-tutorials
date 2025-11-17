/**
 * Generate Safety Classification Dataset from Web Sources
 * Create synthetic Q&A pairs for both response and user prompt safety classification
 * using Llama Guard 3 templates.
 */

import * as fs from "fs";
import * as path from "path";

const API_KEY = process.env.API_KEY;

// Load templates from JSON file
const TEMPLATES_PATH = path.join(__dirname, "resources", "qa_templates.json");
const TEMPLATES = JSON.parse(fs.readFileSync(TEMPLATES_PATH, "utf-8"));

// Define web sources (10 pages from Anthropic HH-RLHF dataset)
const WEB_URLS = Array.from({ length: 10 }, (_, i) =>
  `https://huggingface.co/datasets/Anthropic/hh-rlhf/viewer/default/train?p=${i + 1}`
);

if (!API_KEY) {
  console.error("Error: API_KEY environment variable is required");
  process.exit(1);
}

async function api(endpoint: string, method: string = "GET", options: RequestInit = {}) {
  const response = await fetch(`https://studio.premai.io${endpoint}`, {
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

async function createResponseSafetyDataset(projectId: string) {
  console.log("   Creating response safety dataset...");

  const template = TEMPLATES.response_safety;
  const questionFormat = template.question_format;
  const answerFormat = template.answer_format;

  const formData = new FormData();
  formData.append("project_id", projectId);
  formData.append("name", "Response Safety Classification Dataset");
  formData.append("pairs_to_generate", "50");
  formData.append("pair_type", "qa");
  formData.append("temperature", "0.3");

  template.rules.forEach((rule: string) => {
    formData.append("rules[]", rule);
  });

  formData.append("question_format", questionFormat);
  formData.append("answer_format", answerFormat);

  // Add web URLs
  WEB_URLS.forEach((url, index) => {
    formData.append(`web_urls[${index}]`, url);
  });

  const res = await api("/api/v1/public/datasets/create-synthetic", "POST", {
    body: formData,
  });
  return res.dataset_id;
}

async function createUserPromptSafetyDataset(projectId: string) {
  console.log("   Creating user prompt safety dataset...");

  const template = TEMPLATES.user_prompt_safety;
  const questionFormat = template.question_format;
  const answerFormat = template.answer_format;

  const formData = new FormData();
  formData.append("project_id", projectId);
  formData.append("name", "User Prompt Safety Classification Dataset");
  formData.append("pairs_to_generate", "50");
  formData.append("pair_type", "qa");
  formData.append("temperature", "0.3");

  template.rules.forEach((rule: string) => {
    formData.append("rules[]", rule);
  });

  formData.append("question_format", questionFormat);
  formData.append("answer_format", answerFormat);

  // Add web URLs
  WEB_URLS.forEach((url, index) => {
    formData.append(`web_urls[${index}]`, url);
  });

  const res = await api("/api/v1/public/datasets/create-synthetic", "POST", {
    body: formData,
  });
  return res.dataset_id;
}

async function waitForDataset(datasetId: string) {
  let checks = 0;
  while (true) {
    await sleep(5000);
    const dataset = await api(`/api/v1/public/datasets/${datasetId}`);
    if (checks % 6 === 0) {
      console.log(`   Status: ${dataset.status}, ${dataset.datapoints_count} datapoints`);
    }
    checks++;
    if (dataset.status !== "processing") {
      return dataset;
    }
  }
}

async function main() {
  console.log("\n=== Web Synthetic Safety Dataset Workflow ===\n");

  // Create project
  console.log("1. Creating project...");
  const res = await api("/api/v1/public/projects/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: "Safety Classification Project",
      goal: "Generate safety classification datasets for content moderation",
    }),
  });
  const projectId = res.project_id;
  console.log(`   ✓ Project: ${projectId}\n`);

  // Generate response safety dataset
  console.log("2. Generating response safety dataset...");
  console.log(`   URLs: ${WEB_URLS.length} web sources`);
  const responseDatasetId = await createResponseSafetyDataset(projectId);
  console.log(`   ✓ Dataset: ${responseDatasetId}`);
  console.log("   Waiting for generation (may take 5-10 minutes)...");
  const responseDataset = await waitForDataset(responseDatasetId);
  console.log(`   ✓ Ready: ${responseDataset.datapoints_count} datapoints\n`);

  // Generate user prompt safety dataset
  console.log("3. Generating user prompt safety dataset...");
  console.log(`   URLs: ${WEB_URLS.length} web sources`);
  const userDatasetId = await createUserPromptSafetyDataset(projectId);
  console.log(`   ✓ Dataset: ${userDatasetId}`);
  console.log("   Waiting for generation (may take 5-10 minutes)...");
  const userDataset = await waitForDataset(userDatasetId);
  console.log(`   ✓ Ready: ${userDataset.datapoints_count} datapoints\n`);

  // Create snapshots
  console.log("4. Creating snapshots...");
  const responseSnapshot = await api("/api/v1/public/snapshots/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset_id: responseDatasetId, split_percentage: 80 }),
  });
  const responseSnapshotId = responseSnapshot.snapshot_id;
  console.log(`   ✓ Response Safety Snapshot: ${responseSnapshotId}`);

  const userSnapshot = await api("/api/v1/public/snapshots/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset_id: userDatasetId, split_percentage: 80 }),
  });
  const userSnapshotId = userSnapshot.snapshot_id;
  console.log(`   ✓ User Prompt Safety Snapshot: ${userSnapshotId}\n`);

  // Generate recommendations
  console.log("5. Generating recommendations...");
  await api("/api/v1/public/recommendations/generate", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ snapshot_id: responseSnapshotId }),
  });

  let recs;
  while (true) {
    await sleep(5000);
    recs = await api(`/api/v1/public/recommendations/${responseSnapshotId}`);
    if (recs.status !== "processing") {
      break;
    }
  }

  console.log("   ✓ Recommended experiments:");
  const recommendedCount = recs.recommended_experiments.filter((e: any) => e.recommended).length;
  console.log(`   Total experiments: ${recs.recommended_experiments.length}, Recommended: ${recommendedCount}`);
  recs.recommended_experiments.forEach((e: any) => {
    if (e.recommended) {
      console.log(`     - ${e.base_model_id} (LoRA: ${e.lora})`);
    }
  });
  console.log();

  // Create fine-tuning job
  console.log("6. Creating fine-tuning job...");
  const experiments = recs.recommended_experiments
    .filter((e: any) => e.recommended)
    .map((exp: any) => {
      const { recommended, reason_for_recommendation, ...rest } = exp;
      return rest;
    });

  if (experiments.length === 0) {
    console.log("\n✗ Error: No recommended experiments found. Cannot create finetuning job.");
    process.exit(1);
  }

  const res2 = await api("/api/v1/public/finetuning/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      snapshot_id: responseSnapshotId,
      name: "Response Safety Model",
      experiments,
    }),
  });
  const jobId = res2.job_id;
  console.log(`   ✓ Job: ${jobId}\n`);

  // Monitor (5 minutes max)
  console.log("7. Monitoring job...");
  for (let i = 0; i < 30; i++) {
    await sleep(10000);
    const job = await api(`/api/v1/public/finetuning/${jobId}`);
    console.log(`   Status: ${job.status}`);
    job.experiments.forEach((e: any) => {
      console.log(`     - Exp #${e.experiment_number}: ${e.status} ${e.model_id || ""}`);
    });
    if (job.status !== "processing") {
      break;
    }
  }

  console.log("\n✓ Done!");
  console.log(`\nGenerated datasets:`);
  console.log(`  - Response Safety: ${responseDatasetId} (${responseDataset.datapoints_count} datapoints)`);
  console.log(`  - User Prompt Safety: ${userDatasetId} (${userDataset.datapoints_count} datapoints)`);
  console.log(`\nFine-tuning job: ${jobId}\n`);
}

main().catch((err) => {
  console.error("\n✗ Error:", err.message);
  process.exit(1);
});

