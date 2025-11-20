# Fine-Tune with PDF Synthetic Dataset

**Tags:**
- **Platform Sections**: `dataset`, `finetuning`
- **Complexity**: `intermediate`
- **Domain**: `finance`, `documents`

## Prerequisites

- Prem API key exported as `API_KEY`
- Basic understanding of document parsing and synthetic data generation
- Python 3.8+ or Node.js 18+ installed
- Sample PDF documents (e.g., invoices) placed in the script directory

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
- Upload PDF documents to generate synthetic training data
- Use question/answer templates to enforce strict JSON output schema
- Extract specific fields like Date, Total Amount, Currency, Business Name, and Location
- Fine-tune a model capable of structured data extraction from unstructured documents

## Steps

### Step 1: Prepare PDF Documents

Gather the PDF documents you want to process. This tutorial uses example filenames (`invoice_1.pdf`, `invoice_2.pdf`, etc.), which you should place in the same directory as your script or update the file paths in the code.

### Step 2: Create Project

Create a new project in Prem Studio to organize your datasets and models.

**API Endpoint:** [`POST /api/v1/public/projects/create`](https://docs.premai.io/api-reference/projects/post-projects-create)

### Step 3: Generate Synthetic Dataset

Upload your PDFs and generate synthetic Q&A pairs. We use a template that instructs the model to extract data into a specific JSON schema containing fields like:
- **DateTime**: Transaction date and time
- **Total Amount**: Numeric value
- **Currency**: Currency code
- **Business Name**: Vendor or business name
- **Business Location**: City/State/Country

**API Endpoint:** [`POST /api/v1/public/datasets/create-synthetic`](https://docs.premai.io/api-reference/datasets/post-datasets-create-synthetic)

### Step 4: Create Snapshot

Create a snapshot of your generated dataset to freeze the data version for training.

**API Endpoint:** [`POST /api/v1/public/snapshots/create`](https://docs.premai.io/api-reference/snapshots/post-snapshots-create)

### Step 5: Get Recommendations & Fine-tune

Prem Studio analyzes the snapshot to recommend optimal fine-tuning configurations. Launch a training job based on these recommendations.

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

- [templates.json](resources/templates.json) - Templates for extracting structured data from invoice PDFs

## Next Steps

- Test the model with new invoice layouts
- Expand the JSON schema to capture line items or tax details
- Integrate OCR pre-processing if working with scanned images wrapped in PDFs

