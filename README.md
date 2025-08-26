# Growth Marketing Audit MVP

This is a simple starter kit that generates a **PDF marketing audit** from just a company URL.

## Setup

1. Install Python 3.10+
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Copy `sample.env` to `.env` and add your OpenAI key.

## Usage

```bash
python audit_mvp.py --url https://example.com --out audit.pdf
```

Optional arguments:
- `--max-chars 5000` → limit scraped text
- `--model gpt-4o-mini` → use cheaper/faster models
- `--logo path/to/logo.png` → add your branding

## Files

- `audit_mvp.py` – main script
- `rubric.json` – grading rubric (edit to customize)
- `requirements.txt` – dependencies
- `sample.env` – env template
- `logo_placeholder.png` – swap with your logo

## Output

Generates a PDF with grades (A-F), reasoning, and quick wins for:
- Brand
- Content
- Website
- Marketing
