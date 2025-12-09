/**
 * Dataset Quality Labeling
 * Automatically label datapoints in a dataset based on quality criteria.
 */


// Base URL for Prem Studio API - change this to point to a different environment if needed
const BASE_URL = "https://studio.premai.io";

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

  // Step 1: Dataset ID (static value - replace with your actual dataset ID)
  console.log("Step 1: Dataset Selection");
  const datasetId = "your-dataset-id-here"; // Replace with your actual dataset ID

  console.log(`   Using dataset ID: ${datasetId}`);

  // Verify dataset exists
  console.log("   Verifying dataset...");
  let dataset: any;
  try {
    dataset = await getDatasetInfo(datasetId);
    console.log(`   ✓ Dataset found: ${dataset.name || "N/A"}`);
    console.log(`   ✓ Datapoints: ${dataset.datapoints_count || 0}`);
  } catch (e: any) {
    console.log(`\n✗ Error: Could not access dataset. ${e.message}`);
    console.log("   Please update the datasetId variable in the script with your actual dataset ID.");
    process.exit(1);
  }

  if ((dataset.datapoints_count || 0) === 0) {
    console.log("\n✗ Error: Dataset has no datapoints to label.");
    process.exit(1);
  }

  console.log();

  // Step 2: Create label definitions
  console.log("Step 2: Create Label Definitions");
  const qualityLabels = defineQualityLabels();

  console.log(`\n   Summary of labels:`);
  for (const [labelName, description] of Object.entries(qualityLabels)) {
    console.log(`     - ${labelName}: ${description.substring(0, 50)}...`);
  }
  console.log();

  // Step 3: Create labels
  console.log("Step 3: Creating Labels");
  try {
    const createResult = await createLabels(datasetId, qualityLabels);
    console.log(`   ✓ ${createResult.message || "Labels created successfully"}`);
  } catch (e: any) {
    console.log(`\n✗ Error creating labels: ${e.message}`);
    process.exit(1);
  }

  // Step 4: Start auto-labeling
  console.log("\nStep 4: Starting Auto-Labeling");
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
  console.log(`\nDataset: ${datasetId}`);
  console.log(`Quality labels applied: ${Object.keys(qualityLabels).join(", ")}\n`);
}

main().catch((err) => {
  console.error("\n✗ Error:", err.message);
  process.exit(1);
});

