# Prem Studio Tutorials

Hands-on tutorials showing how to build, fine-tune, evaluate, and automate workflows in Prem Studio—featuring code examples in Python, TypeScript, and Jupyter notebooks.

## Repository Structure

Each tutorial is organized in its own directory under `/tutorials/`, following this structure:

```
/tutorials/
    /<tutorial-name>/
        README.md          # Tutorial documentation
        script.py          # Python implementation
        script.ts          # TypeScript implementation
        notebook.ipynb     # Jupyter notebook
        resources/         # Supporting files
            dataset.jsonl  # Optional: sample dataset in JSONL format
            qa_templates.json  # Optional: QA templates for synthetic dataset generation
            ...
```

## Tutorial Format

Each tutorial README includes:

1. **Prerequisites** - Required knowledge or setup
2. **Outcome** - What you'll achieve
3. **Steps** - Detailed walkthrough with API endpoints
4. **Code Snippets** - TypeScript and Python examples
5. **Resources** - Sample files and datasets
6. **Next Steps** - Related tutorials and learning paths

## Tags

Tutorials are tagged with:

- **Platform Sections**: `dataset`, `finetuning`, `evaluation`, `inference`
- **Complexity**: `beginner`, `intermediate`, `advanced`
- **Domain**: `safety`, `finance`, `medicine`, `education`, etc.

Tags appear at the top of each tutorial README.

## Contributing

We welcome contributions! To add a new tutorial:

1. **Copy the template**: Use `/tutorials/_template/` as a starting point
2. **Follow the structure**: Ensure all required files are included
3. **Add tags**: Include platform sections, complexity, and domain tags
4. **Submit a PR**: Open a pull request with your tutorial

See `/tutorials/_template/README.md` for detailed guidelines.
