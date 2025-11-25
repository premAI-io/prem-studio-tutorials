/**
 * [Tutorial Title]
 * [Brief description]
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

async function main() {
  console.log("\n=== [Tutorial Title] ===\n");

  // Step 1: [Description]
  console.log("1. [Step description]...");
  // TODO: Add implementation
  console.log("   ✓ Complete\n");

  // Step 2: [Description]
  console.log("2. [Step description]...");
  // TODO: Add implementation
  console.log("   ✓ Complete\n");

  console.log("\n✓ Done!\n");
}

main().catch((err) => {
  console.error("\n✗ Error:", err.message);
  process.exit(1);
});

