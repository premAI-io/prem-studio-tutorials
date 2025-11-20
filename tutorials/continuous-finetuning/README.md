# Continuous Fine-Tuning with Traces

**Tags:**
- **Platform Sections**: `evaluation`, `finetuning`, `dataset`
- **Complexity**: `advanced`
- **Domain**: `safety`

## Prerequisites

- **Completed** the [Web Synthetic Safety Dataset](../web-synthetic-safety-dataset/README.md) tutorial
- **A deployed fine-tuned model** from that tutorial
- **Project ID** where the model and dataset reside
- Prem API key exported as `API_KEY`
- Python 3.8+ or Node.js 18+ installed

## Setup Environment

### Python

```bash
# Navigate to the Python directory from the repository root
cd tutorials/continuous-finetuning/python

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### TypeScript

```bash
# Navigate to the TypeScript directory from the repository root
cd tutorials/continuous-finetuning/typescript

# Install dependencies using bun
bun install
```

## Outcome

By the end of this tutorial, you will:
- Establish an automated evaluation pipeline using a judge model
- Create traces in Prem Studio to track model performance
- Automatically expand your training dataset with corrected examples
- Launch a new fine-tuning job that incorporates learnings from previous errors

## Steps

### Step 1: Identify Your Model

You need the **Project ID** and the **Model Alias** (or ID) of your fine-tuned model. You can find these in the Prem Studio dashboard.

### Step 2: Generate Responses

Generate responses from your fine-tuned model using test prompts matching your domain.

**API Endpoint:** [`POST /api/v1/chat/completions`](https://docs.premai.io/api-reference/chat-completions/post-chatcompletions)

### Step 3: Evaluate Responses

Use a judge model (Claude 4.5 Sonnet) to score the safety classification (0-1) and provide feedback.

**API Endpoint:** [`POST /api/v1/chat/completions`](https://docs.premai.io/api-reference/chat-completions/post-chatcompletions)

### Step 4: Create Traces

Log the interaction as a "Trace" in Prem Studio, attaching the score and feedback.

**API Endpoint:** [`POST /api/v1/traces`](https://docs.premai.io/api-reference/traces/post-traces)

### Step 5: Add Traces to Dataset

Add these traces to your original dataset. Prem Studio handles the logic: high-quality traces are added as-is; low-quality traces are corrected before addition.

**API Endpoint:** [`POST /api/v1/traces/{trace_id}/addToDataset`](https://docs.premai.io/api-reference/traces/post-traces-trace-id-addtodataset)

### Step 6: Create Snapshot

Create a new snapshot of the augmented dataset.

**API Endpoint:** [`POST /api/v1/public/snapshots/create`](https://docs.premai.io/api-reference/snapshots/post-snapshots-create)

### Step 7: Get Recommendations & Fine-tune

Analyze the new snapshot and launch a fine-tuning job.

**API Endpoints:**
- [`POST /api/v1/public/recommendations/generate`](https://docs.premai.io/api-reference/recommendations/post-recommendations-generate)
- [`POST /api/v1/public/finetuning/create`](https://docs.premai.io/api-reference/finetuning/post-finetuning-create)

## Code Snippets

### TypeScript

See `typescript/script.ts` for the complete implementation.

**To run the TypeScript script:**

```bash
# Navigate to the TypeScript directory from the repository root
cd tutorials/continuous-finetuning/typescript

# Replace placeholders with your actual values
bun script.ts --project-id <YOUR_PROJECT_ID> --model-alias <YOUR_MODEL_ALIAS>
```

### Python

See `python/script.py` for the complete implementation.

**To run the Python script:**

```bash
# Navigate to the Python directory from the repository root
cd tutorials/continuous-finetuning/python

# Replace placeholders with your actual values
python script.py --project-id <YOUR_PROJECT_ID> --model-alias <YOUR_MODEL_ALIAS>
```

## Resources

- [test_examples.json](resources/test_examples.json) - Sample prompts for testing safety classification

## Next Steps

- Monitor the new fine-tuning job in the Prem Studio dashboard
- Repeat this cycle periodically with new, challenging prompts to continuously refine your model
- Customize the `judge_prompt` in the script to enforce stricter or different evaluation criteria
