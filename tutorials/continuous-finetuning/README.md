# Continuous Fine-Tuning with Traces

**Tags:**
- **Platform Sections**: `evaluation`, `finetuning`, `dataset`
- **Complexity**: `advanced`
- **Domain**: `safety`

## Overview

Continuously improve your model's performance by establishing a feedback loop:
1.  **Test** the fine-tuned model with domain-specific prompts
2.  **Evaluate** responses using a judge model (Claude 4.5 Sonnet)
3.  **Trace** the interactions, capturing inputs, outputs, scores, and feedback
4.  **Augment** your dataset with these traces (improving weak responses automatically)
5.  **Retrain** the model on the improved dataset

This tutorial builds directly upon the [Web Synthetic Safety Dataset](../web-synthetic-safety-dataset/README.md) tutorial. It assumes you have a safety guard model that you want to improve.

## Prerequisites

- **Completed** the [Web Synthetic Safety Dataset](../web-synthetic-safety-dataset/README.md) tutorial
- **A deployed fine-tuned model** from that tutorial
- **Project ID** where the model and dataset reside
- Prem API key exported as `API_KEY`
- Python 3.8+ or Node.js 18+ installed

## Setup Environment

### Python

```bash
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
# Install dependencies using npm
npm install

# Or using bun (if available)
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

### Step 2: Run the Continuous Fine-Tuning Script

The script performs the full cycle: generation -> evaluation -> tracing -> dataset update -> retraining.

**TypeScript:**
```bash
# Replace placeholders with your actual values
bun run script.ts --project-id <YOUR_PROJECT_ID> --model-alias <YOUR_MODEL_ALIAS>
```

**Python:**
```bash
# Replace placeholders with your actual values
python script.py --project-id <YOUR_PROJECT_ID> --model-alias <YOUR_MODEL_ALIAS>
```

### Step 3: Script Logic Explained

1.  **Generate Responses**: The script sends test prompts (from `resources/test_examples.json`) to your model. These prompts follow the exact format defined in the safety dataset tutorial.
2.  **Evaluate with Judge**: It asks a judge model (Claude 4.5 Sonnet) to score the safety classification (0-1) and provide feedback.
3.  **Create Traces**: It logs the interaction as a "Trace" in Prem Studio, attaching the score and feedback.
4.  **Add to Dataset**: It adds these traces to your original dataset. Prem Studio handles the logic: high-quality traces are added as-is; low-quality traces are corrected before addition.
5.  **Create Snapshot**: A new snapshot of the augmented dataset is created.
6.  **Retrain**: A new fine-tuning job is launched using the new snapshot.

## Code Snippets

### TypeScript

See `typescript/script.ts` for the complete implementation.

### Python

See `python/script.py` for the complete implementation.

## Resources

- [test_examples.json](resources/test_examples.json) - Sample prompts for testing safety classification

## Next Steps

- Monitor the new fine-tuning job in the Prem Studio dashboard
- Repeat this cycle periodically with new, challenging prompts to continuously refine your model
- Customize the `judge_prompt` in the script to enforce stricter or different evaluation criteria
