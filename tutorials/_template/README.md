# [Tutorial Title]

**Tags:**
- **Platform Sections**: `[platform-section]`
- **Complexity**: `[complexity]`
- **Domain**: `[domain]`

## Prerequisites

- [ ] Prerequisite 1
- [ ] Prerequisite 2

## Setup Environment

### Python

If the tutorial includes a `requirements.txt` file:

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

If no `requirements.txt` is present, install dependencies manually:
```bash
pip install requests
```

### TypeScript

If the tutorial includes a `package.json` file:

```bash
# Install dependencies using npm
npm install

# Or using bun (if available)
bun install
```

## Outcome

By the end of this tutorial, you will:
- Outcome 1
- Outcome 2

## Steps

### Step 1: [Step Title]

Description of what this step accomplishes.

**API Endpoint:** [`POST /api/v1/public/[endpoint]`](https://docs.premai.io/api-reference/[endpoint])

### Step 2: [Step Title]

Description of what this step accomplishes.

**API Endpoint:** [`POST /api/v1/public/[endpoint]`](https://docs.premai.io/api-reference/[endpoint])

## API Endpoints

| Endpoint | Documentation |
|----------|---------------|
| `POST /api/v1/public/projects/create` | [Projects API](https://docs.premai.io/api-reference/projects/post-projects-create) |
| `POST /api/v1/public/datasets/create` | [Datasets API](https://docs.premai.io/api-reference/datasets/post-datasets-create-from-jsonl) |

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

- [dataset.jsonl](resources/dataset.jsonl) - Sample dataset (if applicable)
- [qa_templates.json](resources/qa_templates.json) - QA templates (if applicable)

## Next Steps

- [Related tutorial 1](link)
- [Related tutorial 2](link)
- [Documentation](link)

