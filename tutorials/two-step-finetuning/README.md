# Two-Step Fine-Tuning: Full FT then LoRA

**Tags:**
- **Platform Sections**: `finetuning`, `dataset`
- **Complexity**: `advanced`
- **Domain**: `safety`, `multilingual`

## Prerequisites

- Prem API key exported as `API_KEY`
- Python 3.8+ or Node.js 18+ installed
- Datasets generated using the [Nemotron Safety Dataset Adaptation](../nemotron-safety-dataset-adaptation/README.md) tutorial

## Setup Environment

### Python

```bash
cd tutorials/two-step-finetuning/python
python -m venv venv
source venv/bin/activate
pip install requests
```

### TypeScript

```bash
cd tutorials/two-step-finetuning/typescript
bun install
```

## Outcome

By the end of this tutorial, you will:
- Perform a **full fine-tuning** on base models (`qwen3-0.6b`, `granite-4.0-h-1b`, `gemma3-1b`) using a large English safety dataset.
- Perform a **LoRA fine-tuning** on top of the previously fine-tuned models using a smaller, language-specific dataset.
- Chain multiple fine-tuning jobs to progressively improve model performance on specific tasks/languages.

## Steps

### Preparation: Generate Datasets

Before running the script, you need to generate the datasets using the [Nemotron Safety Dataset Adaptation](../nemotron-safety-dataset-adaptation/README.md) tutorial.

1. **English Dataset (10k samples)**:
   ```bash
   # Python
   python tutorials/nemotron-safety-dataset-adaptation/python/script.py --language en --limit 10000 --output english_dataset.jsonl
   
   # OR TypeScript
   bun tutorials/nemotron-safety-dataset-adaptation/typescript/script.ts --language en --limit 10000
   ```
   Move `english_dataset.jsonl` to `tutorials/two-step-finetuning/resources/`.

2. **Target Language Dataset (5k samples)**:
   Replace `XYZ` with your target language code (e.g., `fr`, `de`, `es`).
   ```bash
   # Python
   python tutorials/nemotron-safety-dataset-adaptation/python/script.py --language XYZ --limit 5000 --output target_language_dataset.jsonl
   
   # OR TypeScript
   bun tutorials/nemotron-safety-dataset-adaptation/typescript/script.ts --language XYZ --limit 5000
   ```
   Move `target_language_dataset.jsonl` to `tutorials/two-step-finetuning/resources/`.

### Step 1: Full Fine-Tuning
- Create a new project.
- Upload the English dataset (10k).
- Create a snapshot (95/5 split).
- Generate recommendations and filter for `qwen3-0.6b`, `granite-4.0-h-1b`, `gemma3-1b`.
- Launch full fine-tuning jobs (3 epochs).
- Evaluation: See [Guarding BYOE](../guarding-byoe/README.md) for evaluation steps.

### Step 2: LoRA Fine-Tuning
- Create a new project (or use existing).
- Upload the target language dataset (5k).
- Create a snapshot.
- Generate recommendations based on the *previously fine-tuned models*.
- Launch LoRA fine-tuning jobs (2 epochs).
- Evaluation: Compare results using the [Guarding BYOE](../guarding-byoe/README.md) methodology.

## Code Snippets

### TypeScript

See `typescript/script.ts`.

```bash
export API_KEY=your-api-key
cd tutorials/two-step-finetuning/typescript
bun script.ts
```

### Python

See `python/script.py`.

```bash
export API_KEY=your-api-key
cd tutorials/two-step-finetuning/python
source venv/bin/activate
python script.py
```

