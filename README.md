# Prem Studio Tutorials

Hands-on tutorials showing how to build, fine-tune, evaluate, and automate workflows in Prem Studio—featuring code examples in Python, TypeScript, and Jupyter notebooks.

## Tutorial Format

Each tutorial README includes:

1. **Prerequisites** - Required knowledge or setup
2. **Setup Environment** - Environment setup instructions for Python and TypeScript
3. **Outcome** - What you'll achieve
4. **Steps** - Detailed walkthrough
5. **Code Snippets** - TypeScript and Python examples with instructions on how to run the experiments
6. **Resources** - Sample files and datasets
7. **Next Steps** - Related tutorials and learning paths

## Tags

Tutorials are tagged with:

- **Platform Sections**: `dataset`, `finetuning`, `evaluation`, `inference`
- **Complexity**: `beginner`, `intermediate`, `advanced`
- **Domain**: `safety`, `finance`, `medicine`, `education`, etc.

Tags appear at the top of each tutorial README.

## Repository Structure

Each tutorial is organized in its own directory under `/tutorials/`, following this structure:

```
/tutorials/
    /<tutorial-name>/
        README.md          # Tutorial documentation
        python/            # Python implementation
            script.py
            requirements.txt
            notebook.ipynb
        typescript/        # TypeScript implementation
            script.ts
            package.json
        resources/         # Shared resources
            dataset.jsonl  # Optional: sample dataset in JSONL format
            qa_templates.json
            ...
```

Note: Not all tutorials provide both Python and TypeScript implementations.

## Contributing

We welcome contributions! To add a new tutorial:

1. **Copy the template**: Use `/tutorials/_template/` as a starting point
2. **Follow the structure**: Ensure all required files are included in the appropriate `python` or `typescript` subfolders
3. **Add tags**: Include platform sections, complexity, and domain tags
4. **Submit a PR**: Open a pull request with your tutorial

See `/tutorials/_template/README.md` for detailed guidelines.
