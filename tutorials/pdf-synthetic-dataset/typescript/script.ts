/**
 * Generate Synthetic Dataset from PDF Documents
 * Create synthetic Q&A pairs for extracting structured data from invoice PDFs.
 */

import * as fs from "fs";
import * as path from "path";

// Base URL for Prem Studio API
const BASE_URL = "https://studio.premai.io";

const API_KEY = process.env.API_KEY;

// Load templates from JSON file
const RESOURCES_DIR = path.join(__dirname, "..", "resources");
const TEMPLATES_PATH = path.join(RESOURCES_DIR, "templates.json");
const TEMPLATES = JSON.parse(fs.readFileSync(TEMPLATES_PATH, "utf-8"));

// Define invoice PDF files to process from resources directory
// We'll scan the directory for .pdf files
let PDF_FILES: string[] = [];
try {
  if (fs.existsSync(RESOURCES_DIR)) {
    PDF_FILES = fs.readdirSync(RESOURCES_DIR)
      .filter(file => file.toLowerCase().endsWith('.pdf'))
      .map(file => path.join(RESOURCES_DIR, file));
  }
} catch (e) {
  console.error(`Error reading resources directory: ${e}`);
}

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

  // Check if we have files
  if (PDF_FILES.length === 0) {
    console.error(`   Error: No PDF files found in ${RESOURCES_DIR}.`);
    return null;
  }
  
  console.log(`   Found ${PDF_FILES.length} PDF files.`);

  const formData = new FormData();
  formData.append("project_id", projectId);
  formData.append("name", datasetName);
  // Set pairs_to_generate to the number of files to ensure 1 pair per file
  formData.append("pairs_to_generate", PDF_FILES.length.toString());
  formData.append("pair_type", "qa");
  formData.append("temperature", "0");
  formData.append("question_format", questionFormat);
  formData.append("answer_format", answerFormat);
  
  // Add rules
  rules.forEach((rule: string) => {
    formData.append("rules[]", rule);
  });

  // Upload PDF files
  let filesFound = false;
  PDF_FILES.forEach((pdfPath: string) => {
    // In Node with Bun/fetch, we need to construct a Blob/File.
    try {
      if (fs.existsSync(pdfPath)) {
        const fileContent = fs.readFileSync(pdfPath);
        const blob = new Blob([fileContent], { type: 'application/pdf' });
        formData.append('files[]', blob, path.basename(pdfPath));
        filesFound = true;
      } else {
        console.log(`   Warning: File ${pdfPath} not found. Skipping.`);
      }
    } catch (e) {
      console.log(`   Warning: Could not process ${pdfPath}.`);
    }
  });

  if (!filesFound) {
    console.error("   Error: No valid PDF files found to upload.");
    return null;
  }

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
  console.log("\n=== PDF Synthetic Dataset Workflow ===\n");

  // Create project
  console.log("1. Creating project...");
  const project = await api("/api/v1/public/projects/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: "Invoice Extraction Project",
      goal: "Extract structured data from receipts",
    }),
  });
  const projectId = project.project_id;
  console.log(`   ✓ Project: ${projectId}\n`);

  // Generate synthetic dataset
  console.log("2. Generating synthetic dataset from PDFs...");
  console.log(`   Source: ${RESOURCES_DIR}`);
  
  const datasetId = await createSyntheticDataset(
    projectId,
    "Invoice Receipts Dataset",
    "invoice_extraction"
  );
  
  if (!datasetId) {
    process.exit(1);
  }
  
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
  const recommendedCount = recs.recommended_models?.length || 0;
  console.log(`   Recommended experiments: ${recs.recommended_experiments.length}, Total models: ${recommendedCount}`);
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
      name: "Invoice Extraction Model",
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
