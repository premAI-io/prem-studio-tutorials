/**
 * Generate Synthetic Dataset from YouTube Videos
 * Create synthetic Q&A pairs for extracting investment insights from financial videos.
 */

import * as fs from "fs";
import * as path from "path";

// Base URL for Prem Studio API
const BASE_URL = "https://studio.premai.io";

const API_KEY = process.env.API_KEY;

// Load templates from JSON file
const TEMPLATES_PATH = path.join(__dirname, "..", "resources", "templates.json");
const TEMPLATES = JSON.parse(fs.readFileSync(TEMPLATES_PATH, "utf-8"));

// Define YouTube videos to analyze
const YOUTUBE_URLS = [
  "https://www.youtube.com/watch?v=JH-k5f4Yclc",
  "https://www.youtube.com/watch?v=YEWhxcpMS1c",
  "https://www.youtube.com/watch?v=cb8up3HVXis",
  "https://www.youtube.com/watch?v=26xatIiMv88",
  "https://www.youtube.com/watch?v=-Da3gUdzCvs"
];

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

async function createSyntheticDataset(
  projectId: string,
  datasetName: string,
  templateKey: string
) {
  console.log(`   Creating ${datasetName}...`);

  const template = TEMPLATES[templateKey];
  const questionFormat = template.question_format;
  const answerFormat = template.answer_format;
  const rules = template.rules;

  const formData = new FormData();
  formData.append("project_id", projectId);
  formData.append("name", datasetName);
  formData.append("pairs_to_generate", "50");
  formData.append("pair_type", "qa");
  formData.append("temperature", "0.3");
  formData.append("question_format", questionFormat);
  formData.append("answer_format", answerFormat);
  
  // Add rules
  rules.forEach((rule: string) => {
    formData.append("rules[]", rule);
  });

  // Add YouTube URLs
  YOUTUBE_URLS.forEach((url: string, index: number) => {
    formData.append(`youtube_urls[${index}]`, url);
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
  console.log("\n=== YouTube Synthetic Dataset Workflow ===\n");

  // Create project
  console.log("1. Creating project...");
  const project = await api("/api/v1/public/projects/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: "Stock Analysis Project",
      goal: "Extract investment insights from financial videos",
    }),
  });
  const projectId = project.project_id;
  console.log(`   ✓ Project: ${projectId}\n`);

  // Generate synthetic dataset
  console.log("2. Generating synthetic dataset from YouTube...");
  console.log(`   URLs: ${YOUTUBE_URLS.length} financial videos`);
  
  const datasetId = await createSyntheticDataset(
    projectId,
    "Financial YouTube Dataset",
    "financial_analysis"
  );
  
  console.log(`   ✓ Dataset: ${datasetId}`);
  console.log("   Waiting for generation (may take 5-10 minutes)...");
  const dataset = await waitForDataset(datasetId);
  console.log(`   ✓ Ready: ${dataset.datapoints_count} datapoints\n`);

  // Create snapshot
  console.log("3. Creating snapshot...");
  const snapshot = await api("/api/v1/public/snapshots/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset_id: datasetId, split_percentage: 80 }),
  });
  const snapshotId = snapshot.snapshot_id;
  console.log(`   ✓ Snapshot: ${snapshotId}\n`);

  // Generate recommendations
  console.log("4. Generating recommendations...");
  await api("/api/v1/public/recommendations/generate", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ snapshot_id: snapshotId }),
  });

  let recs;
  while (true) {
    await sleep(5000);
    recs = await api(`/api/v1/public/recommendations/${snapshotId}`);
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
  console.log("5. Creating fine-tuning job...");
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
      snapshot_id: snapshotId,
      name: "YouTube Model",
      experiments,
    }),
  });
  const jobId = res2.job_id;
  console.log(`   ✓ Job: ${jobId}\n`);

  // Monitor (5 minutes max)
  console.log("6. Monitoring job...");
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
  console.log(`\nGenerated dataset: ${datasetId}`);
  console.log(`Fine-tuning job: ${jobId}\n`);
}

main().catch((err) => {
  console.error("\n✗ Error:", err.message);
  process.exit(1);
});

