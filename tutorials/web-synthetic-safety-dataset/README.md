# Generate Safety Classification Dataset from Web Sources

**Tags:**
- **Platform Sections**: `dataset`, `finetuning`
- **Complexity**: `intermediate`
- **Domain**: `safety`

## Prerequisites

- Prem API key exported as `API_KEY`
- Basic understanding of content moderation and safety classification
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
- Generate synthetic Q&A pairs for safety classification from web sources
- Create datasets for both user prompt and response safety classification
- Use Llama Guard 3 templates to structure your training data
- Fine-tune a model for content moderation tasks

## Steps

### Step 1: Set Web Source URLs

Define the web sources you want to analyze. This example uses 10 pages from the Anthropic HH-RLHF dataset.

### Step 2: Create Project

Create a new project for safety classification.

**API Endpoint:** [`POST /api/v1/public/projects/create`](https://docs.premai.io/api-reference/projects/post-projects-create)

### Step 3: Generate Response Safety Dataset

Generate synthetic Q&A pairs for classifying agent responses as safe/unsafe.

**API Endpoint:** [`POST /api/v1/public/datasets/create-synthetic`](https://docs.premai.io/api-reference/datasets/post-datasets-create-synthetic)

### Step 4: Generate User Prompt Safety Dataset

Generate synthetic Q&A pairs for classifying user prompts as safe/unsafe.

**API Endpoint:** [`POST /api/v1/public/datasets/create-synthetic`](https://docs.premai.io/api-reference/datasets/post-datasets-create-synthetic)

### Step 5: Create Snapshots and Fine-tune

Create snapshots from your datasets and launch fine-tuning jobs.

**API Endpoints:**
- [`POST /api/v1/public/snapshots/create`](https://docs.premai.io/api-reference/snapshots/post-snapshots-create)
- [`POST /api/v1/public/recommendations/generate`](https://docs.premai.io/api-reference/recommendations/post-recommendations-generate)
- [`POST /api/v1/public/finetuning/create`](https://docs.premai.io/api-reference/finetuning/post-finetuning-create)

## API Endpoints

| Endpoint | Documentation |
|----------|---------------|
| `POST /api/v1/public/projects/create` | [Projects API](https://docs.premai.io/api-reference/projects/post-projects-create) |
| `POST /api/v1/public/datasets/create-synthetic` | [Synthetic Dataset API](https://docs.premai.io/api-reference/datasets/post-datasets-create-synthetic) |
| `GET /api/v1/public/datasets/{dataset_id}` | [Get Dataset API](https://docs.premai.io/api-reference/datasets/get-datasets-dataset-id) |
| `POST /api/v1/public/snapshots/create` | [Snapshots API](https://docs.premai.io/api-reference/snapshots/post-snapshots-create) |
| `POST /api/v1/public/recommendations/generate` | [Recommendations API](https://docs.premai.io/api-reference/recommendations/post-recommendations-generate) |
| `GET /api/v1/public/recommendations/{snapshot_id}` | [Get Recommendations API](https://docs.premai.io/api-reference/recommendations/get-recommendations-snapshot-id) |
| `POST /api/v1/public/finetuning/create` | [Fine-tuning API](https://docs.premai.io/api-reference/finetuning/post-finetuning-create) |
| `GET /api/v1/public/finetuning/{job_id}` | [Get Fine-tuning Job API](https://docs.premai.io/api-reference/finetuning/get-finetuning-job-id) |

## Code Snippets

### TypeScript

See `script.ts` for complete implementation with both response and user prompt classification.

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

See `script.py` for complete implementation with both response and user prompt classification.

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

- [qa_templates.json](resources/qa_templates.json) - QA templates for both response and user prompt safety classification

## Next Steps

- [Continuous Fine-Tuning](../continuous-finetuning/README.md) - Automatically improve your model using traces and feedback
- Evaluate your model's performance on safety classification tasks
- Deploy your safety classifier for production use
- Explore other safety categories and expand your dataset
