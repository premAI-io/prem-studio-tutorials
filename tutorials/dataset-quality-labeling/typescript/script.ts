/**
 * Dataset Quality Labeling
 * Automatically label datapoints in a dataset based on quality criteria.
 */

import * as fs from "fs";
import * as path from "path";

// Base URL for Prem Studio API - change this to point to a different environment if needed
const BASE_URL = "https://studio.premai.io";

// Path to sample dataset - using Bun's file path resolution
const SAMPLE_DATASET_PATH = path.resolve(
  import.meta.dir,
  "..",
  "resources",
  "sample_dataset.jsonl"
);

const API_KEY = process.env.API_KEY;

if (!API_KEY) {
  console.error("Error: API_KEY environment variable is required");
  process.exit(1);
}

async function api(endpoint: string, method: string = "GET", options: RequestInit = {}) {
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

function defineQualityLabels(): Record<string, string> {
  console.log("\n=== Define Quality Labels ===\n");

  // Static quality labels configuration
  const qualityLabels: Record<string, string> = {
    excellent:
      "Datapoints with exceptional quality: comprehensive, accurate, well-structured responses that demonstrate deep understanding and provide valuable insights. No errors or ambiguities.",
    good: "Datapoints with solid quality: accurate and useful responses that address the query adequately. Minor improvements possible but overall reliable and informative.",
    fair: "Datapoints with acceptable quality: responses that partially address the query but may lack depth, clarity, or completeness. Some inaccuracies or gaps present.",
    poor: "Datapoints with low quality: responses that fail to adequately address the query, contain significant errors, are poorly structured, or provide minimal value.",
  };

  console.log("   Quality labels defined:");
  for (const [labelName, description] of Object.entries(qualityLabels)) {
    console.log(`     - ${labelName}: ${description.substring(0, 60)}...`);
  }

  return qualityLabels;
}

async function createProject(projectName: string, goal: string): Promise<string> {
  const result = await api("/api/v1/public/projects/create", "POST", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: projectName, goal }),
  });
  return result.project_id;
}

async function uploadDatasetFromJsonl(
  projectId: string,
  datasetName: string,
  filePath: string
): Promise<string> {
  console.log(`   Uploading ${datasetName} from ${path.basename(filePath)}...`);

  const fileContent = fs.readFileSync(filePath);
  const blob = new Blob([fileContent], { type: "application/json" });

  const formData = new FormData();
  formData.append("file", blob, path.basename(filePath));
  formData.append("project_id", projectId);
  formData.append("name", datasetName);

  const result = await api("/api/v1/public/datasets/create-from-jsonl", "POST", {
    body: formData,
  });

  return result.dataset_id;
}

async function getDatasetInfo(datasetId: string): Promise<any> {
  const dataset = await api(`/api/v1/public/datasets/${datasetId}`);
  return dataset;
}

async function createLabels(
  datasetId: string,
  qualityLabels: Record<string, string>
): Promise<any> {
  console.log(`\n=== Creating Label Definitions ===\n`);

  // Prepare label_definitions array for API
  const labelDefinitions = Object.entries(qualityLabels).map(([name, description]) => ({
    name,
    description,
  }));

  // Call create-labels endpoint
  console.log("   Creating label definitions...");
  const result = await api(
    `/api/v1/public/datasets/${datasetId}/create-labels`,
    "POST",
    {
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ label_definitions: labelDefinitions }),
    }
  );

  return result;
}

async function startAutoLabeling(datasetId: string): Promise<any> {
  console.log(`\n=== Starting Auto-Labeling ===\n`);

  // Call start-auto-labeling endpoint
  console.log("   Starting auto-labeling process...");
  const result = await api(
    `/api/v1/public/datasets/${datasetId}/start-auto-labeling`,
    "POST",
    {
      headers: { "Content-Type": "application/json" },
    }
  );

  return result;
}

async function main() {
  console.log("\n=== Dataset Quality Labeling ===\n");

  // Step 1: Create project
  console.log("Step 1: Creating Project");
  let projectId: string;
  try {
    projectId = await createProject(
      "Quality Labeling Project",
      "Label dataset datapoints based on quality criteria"
    );
    console.log(`   ✓ Project created: ${projectId}\n`);
  } catch (e: any) {
    console.log(`\n✗ Error creating project: ${e.message}`);
    process.exit(1);
  }

  // Step 2: Upload sample dataset
  console.log("Step 2: Uploading Sample Dataset");
  if (!fs.existsSync(SAMPLE_DATASET_PATH)) {
    console.log(`\n✗ Error: Sample dataset not found at ${SAMPLE_DATASET_PATH}`);
    process.exit(1);
  }

  let datasetId: string;
  try {
    datasetId = await uploadDatasetFromJsonl(
      projectId,
      "Quality Labeling Sample Dataset",
      SAMPLE_DATASET_PATH
    );
    console.log(`   ✓ Dataset created: ${datasetId}`);

    // Wait a moment for dataset to be ready
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // Verify dataset
    const dataset = await getDatasetInfo(datasetId);
    console.log(`   ✓ Datapoints: ${dataset.datapoints_count || 0}\n`);
  } catch (e: any) {
    console.log(`\n✗ Error uploading dataset: ${e.message}`);
    process.exit(1);
  }

  // Step 3: Define quality labels
  console.log("Step 3: Define Quality Labels");
  const qualityLabels = defineQualityLabels();

  console.log(`\n   Summary of labels:`);
  for (const [labelName, description] of Object.entries(qualityLabels)) {
    console.log(`     - ${labelName}: ${description.substring(0, 50)}...`);
  }
  console.log();

  // Step 4: Create labels
  console.log("Step 4: Creating Label Definitions");
  try {
    const createResult = await createLabels(datasetId, qualityLabels);
    console.log(`   ✓ ${createResult.message || "Labels created successfully"}`);
  } catch (e: any) {
    console.log(`\n✗ Error creating labels: ${e.message}`);
    process.exit(1);
  }

  // Step 5: Start auto-labeling
  console.log("\nStep 5: Starting Auto-Labeling");
  try {
    const labelingResult = await startAutoLabeling(datasetId);
    console.log(
      `   ✓ ${labelingResult.message || "Auto-labeling started successfully"}`
    );
    console.log("   The labeling process is running in the background.");
  } catch (e: any) {
    console.log(`\n✗ Error starting auto-labeling: ${e.message}`);
    process.exit(1);
  }

  console.log("\n✓ Done!");
  console.log(`\nProject: ${projectId}`);
  console.log(`Dataset: ${datasetId}`);
  console.log(`Quality labels applied: ${Object.keys(qualityLabels).join(", ")}\n`);
}

main().catch((err) => {
  console.error("\n✗ Error:", err.message);
  process.exit(1);
});

