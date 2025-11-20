# Continuous Fine-tuning Tutorial

**Tags:** `finetuning` | `advanced` | `mlops`

## Overview

This tutorial demonstrates **continuous fine-tuning**, a powerful technique where you first perform full fine-tuning on a base model, then apply LoRA (Low-Rank Adaptation) fine-tuning on top of the previously finetuned model. This approach allows you to:

1. **Broadly adapt** a model to a general domain (full fine-tuning)
2. **Specialize further** into a specific sub-domain (LoRA fine-tuning)

This workflow is particularly useful when you want to:
- Build domain expertise incrementally
- Fine-tune on related but distinct datasets sequentially
- Optimize compute resources (full FT once, then efficient LoRA adaptations)
- Maintain model flexibility while adding specialized knowledge

## Prerequisites

- Prem API key exported as `API_KEY`
- Understanding of fine-tuning concepts (full fine-tuning vs LoRA)
- Python 3.8+ or Node.js 18+ installed
- Basic familiarity with machine learning workflows

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
pip install requests
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
- Understand continuous fine-tuning workflow
- Perform full fine-tuning on a general software engineering dataset
- Apply LoRA fine-tuning on top of the finetuned model using an ML engineering dataset
- See how models can be incrementally specialized through sequential fine-tuning
- Learn to chain fine-tuning jobs using model IDs from previous jobs

## Tutorial Flow

This tutorial uses two related datasets:

1. **General Software Engineering Dataset** (80 Q&A pairs)
   - Covers broad software engineering topics: version control, APIs, databases, architecture patterns, etc.
   - Used for **full fine-tuning** to establish general domain knowledge

2. **Machine Learning Engineering Dataset** (80 Q&A pairs)
   - Deep dive into ML-specific topics: MLOps, model versioning, feature engineering, production deployment, etc.
   - Used for **LoRA fine-tuning** to specialize the model further

The datasets are designed to be related but distinct: the first establishes general software engineering knowledge, while the second specializes into ML engineering as a sub-domain.

## Steps

### Step 1: Create Project

Create a new project for continuous fine-tuning.

**API Endpoint:** [`POST /api/v1/public/projects/create`](https://docs.premai.io/api-reference/projects/post-projects-create)

### Step 2: Upload Full Fine-tuning Dataset

Upload the general software engineering dataset that will be used for full fine-tuning.

**API Endpoint:** [`POST /api/v1/public/datasets/create-from-jsonl`](https://docs.premai.io/api-reference/datasets/post-datasets-create-from-jsonl)

### Step 3: Create Snapshot for Full Fine-tuning

Create a snapshot from the uploaded dataset with an 80/20 train/validation split.

**API Endpoint:** [`POST /api/v1/public/snapshots/create`](https://docs.premai.io/api-reference/snapshots/post-snapshots-create)

### Step 4: Create Full Fine-tuning Job

Create a full fine-tuning job using a base model. This tutorial uses `meta-llama/Llama-3.2-3B-Instruct` as the base model, but you can check available finetunable models at [https://studio.premai.io/public/models](https://studio.premai.io/public/models).

**API Endpoint:** [`POST /api/v1/public/finetuning/create`](https://docs.premai.io/api-reference/finetuning/post-finetuning-create)

**Note:** This tutorial skips the recommendations step and directly specifies the model and fine-tuning method.

### Step 5: Wait for Full Fine-tuning to Complete

Monitor the fine-tuning job until completion. This typically takes 30-60 minutes depending on dataset size and model.

**API Endpoint:** [`GET /api/v1/public/finetuning/{job_id}`](https://docs.premai.io/api-reference/finetuning/get-finetuning-job-id)

### Step 6: Upload LoRA Fine-tuning Dataset

Upload the ML engineering dataset that will be used for LoRA fine-tuning on top of the finetuned model.

**API Endpoint:** [`POST /api/v1/public/datasets/create-from-jsonl`](https://docs.premai.io/api-reference/datasets/post-datasets-create-from-jsonl)

### Step 7: Create Snapshot for LoRA Fine-tuning

Create a snapshot from the ML engineering dataset.

**API Endpoint:** [`POST /api/v1/public/snapshots/create`](https://docs.premai.io/api-reference/snapshots/post-snapshots-create)

### Step 8: Create LoRA Fine-tuning Job

Create a LoRA fine-tuning job using the **finetuned model ID** from Step 5 as the base model. This is the key to continuous fine-tuning: using the output of one fine-tuning job as the input to the next.

**API Endpoint:** [`POST /api/v1/public/finetuning/create`](https://docs.premai.io/api-reference/finetuning/post-finetuning-create)

### Step 9: Wait for LoRA Fine-tuning to Complete

Monitor the LoRA fine-tuning job. LoRA fine-tuning is typically faster than full fine-tuning.

**API Endpoint:** [`GET /api/v1/public/finetuning/{job_id}`](https://docs.premai.io/api-reference/finetuning/get-finetuning-job-id)

## API Endpoints

| Endpoint | Documentation |
|----------|---------------|
| `POST /api/v1/public/projects/create` | [Projects API](https://docs.premai.io/api-reference/projects/post-projects-create) |
| `POST /api/v1/public/datasets/create-from-jsonl` | [Datasets API](https://docs.premai.io/api-reference/datasets/post-datasets-create-from-jsonl) |
| `GET /api/v1/public/datasets/{dataset_id}` | [Get Dataset API](https://docs.premai.io/api-reference/datasets/get-datasets-dataset-id) |
| `POST /api/v1/public/snapshots/create` | [Snapshots API](https://docs.premai.io/api-reference/snapshots/post-snapshots-create) |
| `POST /api/v1/public/finetuning/create` | [Fine-tuning API](https://docs.premai.io/api-reference/finetuning/post-finetuning-create) |
| `GET /api/v1/public/finetuning/{job_id}` | [Get Fine-tuning Job API](https://docs.premai.io/api-reference/finetuning/get-finetuning-job-id) |

## Code Snippets

### TypeScript

See `script.ts` for complete implementation.

**To run the TypeScript script:**

```bash
# Export your API key
export API_KEY=your-api-key-here

# Run the script using bun (recommended)
bun script.ts

# Or using Node.js with ts-node
npx ts-node script.ts

# Or using Node.js with tsx
npx tsx script.ts
```

### Python

See `script.py` for complete implementation.

**To run the Python script:**

```bash
# Export your API key
export API_KEY=your-api-key-here

# Make sure your virtual environment is activated
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# Run the script
python script.py
```

## Resources

- [full_ft_dataset.jsonl](resources/full_ft_dataset.jsonl) - General software engineering dataset (80 Q&A pairs)
- [lora_ft_dataset.jsonl](resources/lora_ft_dataset.jsonl) - ML engineering dataset (80 Q&A pairs)

## Key Concepts

### Full Fine-tuning vs LoRA Fine-tuning

- **Full Fine-tuning**: Updates all model parameters. More computationally expensive but allows complete adaptation to a domain.
- **LoRA Fine-tuning**: Updates only a small subset of parameters using low-rank matrices. More efficient, faster, and requires less memory while still achieving strong performance.

### Continuous Fine-tuning Strategy

The continuous fine-tuning approach demonstrated here:
1. Uses full fine-tuning to establish broad domain knowledge
2. Uses LoRA fine-tuning to add specialized knowledge efficiently
3. Chains models: output of one fine-tuning job becomes input to the next

This strategy is particularly effective when:
- You have related but distinct datasets
- You want to incrementally build domain expertise
- You need to balance adaptation quality with computational efficiency

## Next Steps

- Experiment with different base models from the [available models list](https://studio.premai.io/public/models)
- Try different dataset combinations to see how continuous fine-tuning affects model performance
- Evaluate your final model on test sets from both datasets
- Explore additional LoRA fine-tuning iterations for even more specialization
- Learn about [model evaluation and deployment](https://docs.premai.io) to put your continuously finetuned model into production

## Troubleshooting

- **Job fails**: Check the job status and error messages via the API. Ensure your datasets are properly formatted.
- **Model ID not found**: Make sure the full fine-tuning job completed successfully before proceeding to LoRA fine-tuning.
- **Long wait times**: Full fine-tuning can take 30-60 minutes. LoRA fine-tuning is typically faster (10-30 minutes).
- **Dataset upload issues**: Ensure your JSONL files are properly formatted with `question` and `answer` fields.

