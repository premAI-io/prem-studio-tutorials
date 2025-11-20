# Adapt Nemotron Safety Guard Dataset to Messages Format

**Tags:**
- **Platform Sections**: `dataset`
- **Complexity**: `intermediate`
- **Domain**: `safety`

## Setup Environment

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

## Outcome

By the end of this tutorial, you will:
- Download the Nemotron Safety Guard Dataset v3 from Hugging Face
- Convert the dataset to the single-turn messages format
- Understand the structure of safety guard model training data
- Generate a JSONL file ready for fine-tuning models

## Steps

### Step 1: Download the Dataset

Download the Nemotron Safety Guard Dataset v3 from Hugging Face. The dataset contains approximately 386,661 samples across 9 languages with safety labels for both prompts and responses.

**Dataset:** [nvidia/Nemotron-Safety-Guard-Dataset-v3](https://huggingface.co/datasets/nvidia/Nemotron-Safety-Guard-Dataset-v3)

You can download it using:
- Hugging Face `datasets` library (Python)
- Direct download from Hugging Face
- Hugging Face CLI

### Step 2: Understand the Dataset Structure

The original dataset contains the following fields:
- `id`: Unique identifier for the sample
- `prompt`: The user's input message
- `response`: The assistant's response (may be null for prompt-only samples)
- `prompt_label`: Safety label for the prompt ("safe" or "unsafe")
- `response_label`: Safety label for the response (may be null)
- `violated_categories`: Comma-separated list of violated safety categories
- `language`: ISO 639-1 language code
- `prompt`: May contain "REDACTED" for sensitive content

### Step 3: Convert to Messages Format

Convert each dataset entry to the messages format with templates:

- **instruction**: Safety policy and categories template (user prompt template)
- **messages**: Array of message objects with `role` ("user" or "assistant") and `content`
- **response_instruction**: Format specification for assistant output (JSON format)

For single-turn conversations:
- If `response` is null or empty: Include only the user message in `messages`
- If `response` exists: Include both user and assistant messages in `messages`

### Step 4: Handle Special Cases

- **REDACTED prompts**: Skip entries where prompt is "REDACTED" (these require external dataset reconstruction)
- **Null responses**: Create single-turn conversations with only user messages
- **Empty strings**: Treat empty strings as null values

### Step 5: Save as JSONL

Write each converted entry as a single line in JSONL format, ensuring proper UTF-8 encoding for multilingual content.

## Dataset Format

### Input Format (Nemotron Safety Guard Dataset v3)

```json
{
  "id": "1ad4134e38e44d92b3c7776b6d28213a",
  "prompt": "User's input message",
  "response": "Assistant's response or null",
  "prompt_label": "safe",
  "response_label": "unsafe",
  "violated_categories": "S1: Violence, S10: Harassment",
  "language": "en"
}
```

### Output Format (Messages Format)

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Task: Check if there is unsafe content...\n\n<BEGIN UNSAFE CONTENT CATEGORIES>...\n<END UNSAFE CONTENT CATEGORIES>\n\n<BEGIN CONVERSATION>\nuser: {{ actual prompt from dataset }}\nagent: {{ actual response from dataset }}\n<END CONVERSATION>\n\nProvide your safety assessment..."
    },
    {
      "role": "assistant",
      "content": "{\"User Safety\": \"safe\", \"Response Safety\": \"safe\"}"
    }
  ]
}
```

For entries without a response (prompt-only):
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Task: Check if there is unsafe content...\n\n<BEGIN CONVERSATION>\nuser: {{ actual prompt from dataset }}\n<END CONVERSATION>\n\nProvide your safety assessment..."
    },
    {
      "role": "assistant",
      "content": "{\"User Safety\": \"unsafe\", \"Safety Categories\": \"S1: Violence\"}"
    }
  ]
}
```

Where:
- **user message**: Contains the full formatted prompt with instruction, safety categories, conversation, and response format instructions
- **assistant message**: JSON object with:
  - `User Safety`: "safe" or "unsafe" (required, from `prompt_label`)
  - `Response Safety`: "safe" or "unsafe" (optional, only if response exists, from `response_label`)
  - `Safety Categories`: comma-separated list (optional, only if unsafe, from `violated_categories`)

## Running the Script

See `script.py` for complete implementation.

```bash
# Make sure your virtual environment is activated
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# Run the script
python script.py
```



[Nemotron Safety Guard Dataset v3](https://huggingface.co/datasets/nvidia/Nemotron-Safety-Guard-Dataset-v3) - Source dataset



