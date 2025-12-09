# Dataset Quality Labeling

**Tags:**
- **Platform Sections**: `dataset`, `labeling`
- **Complexity**: `intermediate`
- **Domain**: `data-quality`, `dataset-management`

## Prerequisites

- Prem API key exported as `API_KEY`
- Basic understanding of dataset quality assessment
- Python 3.8+ or Node.js 18+ installed

## Setup Environment

### Python

```bash
# Navigate to the Python directory from the repository root
cd tutorials/dataset-quality-labeling/python

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
cd tutorials/dataset-quality-labeling/typescript

# Install dependencies using bun
bun install
```

## Outcome

By the end of this tutorial, you will:
- Use predefined quality labels tailored to your dataset type
- Automatically label datapoints in your dataset based on quality levels
- Understand how to use the labeling endpoint to enrich your datasets
- Filter and manage datasets based on quality labels

## Steps

### Step 1: Create Project

Create a new project in Prem Studio to organize your datasets and labeling workflow.

**API Endpoint:** [`POST /api/v1/public/projects/create`](https://docs.premai.io/api-reference/projects/post-projects-create)

### Step 2: Upload Sample Dataset

The script automatically uploads the sample dataset from `resources/sample_dataset.jsonl`. This dataset contains technical Q&A pairs that will be labeled based on quality criteria.

**API Endpoint:** [`POST /api/v1/public/datasets/create-from-jsonl`](https://docs.premai.io/api-reference/datasets/post-datasets-create-from-jsonl)

### Step 3: Quality Labels Configuration

The script uses predefined quality labels that are tailored for technical Q&A datasets. The labels are:
- **excellent**: Comprehensive, accurate, well-structured responses with deep understanding
- **good**: Solid quality responses that adequately address queries
- **fair**: Acceptable quality but may lack depth or completeness
- **poor**: Low quality responses with significant errors or minimal value

These labels are statically defined in the script and are appropriate for assessing the quality of technical documentation and Q&A datapoints.

### Step 4: Create Label Definitions

Create the label definitions in your dataset. This step defines what each quality label means and prepares the dataset for auto-labeling.

**API Endpoint:** [`POST /api/v1/public/datasets/{dataset_id}/create-labels`](https://docs.premai.io/api-reference/datasets/post-datasets-create-labels)

### Step 5: Start Auto-Labeling

Start the automatic labeling process. The system will assess each datapoint and assign the appropriate quality label based on the predefined criteria.

**API Endpoint:** [`POST /api/v1/public/datasets/{dataset_id}/start-auto-labeling`](https://docs.premai.io/api-reference/datasets/post-datasets-start-auto-labeling)

### Step 6: Verify Labels

Check the labeled dataset to verify that datapoints have been correctly assigned quality labels. You can filter and analyze your dataset based on these quality levels.

## Code Snippets

### TypeScript

See `typescript/script.ts` for the complete implementation.

**To run the TypeScript script:**

```bash
# Export your API key
export API_KEY=your-api-key-here

# Navigate to the TypeScript directory from the repository root
cd tutorials/dataset-quality-labeling/typescript

# Run the script
bun script.ts
```

### Python

See `python/script.py` for the complete implementation.

**To run the Python script:**

```bash
# Export your API key
export API_KEY=your-api-key-here

# Navigate to the Python directory from the repository root
cd tutorials/dataset-quality-labeling/python

# Make sure your virtual environment is activated
source venv/bin/activate

# Run the script
python script.py
```

## Resources

- [sample_dataset.jsonl](resources/sample_dataset.jsonl) - Sample dataset for testing the labeling functionality

## Next Steps

- Filter datasets by quality labels to create high-quality training sets
- Use quality labels to improve dataset curation workflows
- Integrate quality labeling into your data pipeline for continuous quality assessment
- Combine quality labeling with fine-tuning to train models on filtered high-quality data

