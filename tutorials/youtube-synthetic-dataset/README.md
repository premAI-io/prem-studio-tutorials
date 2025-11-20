# Fine-Tune with YouTube Synthetic Dataset

**Tags:**
- **Platform Sections**: `dataset`, `finetuning`
- **Complexity**: `intermediate`
- **Domain**: `finance`

## Prerequisites

- Prem API key exported as `API_KEY`
- Basic understanding of synthetic data generation
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
- Process YouTube videos to generate synthetic training data
- Use question/answer templates to extract structured JSON from unstructured video content
- Extract specific entities like stock tickers, investment tips, and risks
- Fine-tune a model capable of extracting structured investment insights from video transcripts

## Steps

### Step 1: Define YouTube Sources

Identify the YouTube videos you want to analyze. In this tutorial, we use 5 curated financial videos, but you can modify the scripts to use your own list.

### Step 2: Create Project

Create a new project in Prem Studio to house your datasets and models.

**API Endpoint:** [`POST /api/v1/public/projects/create`](https://docs.premai.io/api-reference/projects/post-projects-create)

### Step 3: Generate Synthetic Dataset

Generate synthetic Q&A pairs from the video transcripts. We use a specific template to instruct the model to extract:
- **Stock Tickers**: (e.g., AAPL, TSLA)
- **Investment Tips**: Actionable advice
- **Risks**: Warnings and cautionary statements
- **Video Topic**: Brief summary

**API Endpoint:** [`POST /api/v1/public/datasets/create-synthetic`](https://docs.premai.io/api-reference/datasets/post-datasets-create-synthetic)

### Step 4: Create Snapshot

Create a versioned snapshot of your dataset to use for training. We'll use an 80/20 train/test split.

**API Endpoint:** [`POST /api/v1/public/snapshots/create`](https://docs.premai.io/api-reference/snapshots/post-snapshots-create)

### Step 5: Get Recommendations & Fine-tune

Prem Studio analyzes your snapshot and recommends the best models and hyperparameters (LoRA configuration) for your specific task. We'll launch a training job using these recommendations.

**API Endpoints:**
- [`POST /api/v1/public/recommendations/generate`](https://docs.premai.io/api-reference/recommendations/post-recommendations-generate)
- [`POST /api/v1/public/finetuning/create`](https://docs.premai.io/api-reference/finetuning/post-finetuning-create)

## Code Snippets

### TypeScript

See `typescript/script.ts` for the complete implementation.

**To run the TypeScript script:**

```bash
# Export your API key
export API_KEY=your-api-key-here

# Navigate to the typescript directory
cd typescript

# Run the script
npm start
# or
bun run script.ts
```

### Python

See `python/script.py` for the complete implementation.

**To run the Python script:**

```bash
# Export your API key
export API_KEY=your-api-key-here

# Navigate to the python directory
cd python

# Make sure your virtual environment is activated
source venv/bin/activate

# Run the script
python script.py
```

## Resources

- [templates.json](resources/templates.json) - Templates for extracting financial insights from video transcripts

## Next Steps

- Evaluate your fine-tuned model against the test set
- Try different video genres (e.g., technical tutorials, news) and adjust the extraction templates
- Deploy your model to an inference endpoint

