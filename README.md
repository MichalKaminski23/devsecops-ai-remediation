# DevSecOps AI Auto-Remediation

This student project demonstrates an AI-assisted security pipeline for a
deliberately vulnerable Flask application.

The pipeline:

1. Scans the repository for leaked secrets with Gitleaks.
2. Audits Python dependencies with `pip-audit`.
3. Runs Semgrep SAST rules.
4. Sends findings and source code to Gemini for triage and remediation.
5. Validates the AI response and generated code.
6. Runs security regression tests.
7. Re-scans the remediated code with Semgrep.
8. Creates a Pull Request with the proposed changes and pipeline metrics.

## Project structure

```text
app/       Vulnerable Flask demo application
scripts/   AI remediation script
tests/     Security regression tests
.github/   GitHub Actions workflow
```

The vulnerabilities in `app/app.py` are intentional and exist only for
demonstration purposes. Do not deploy the application in its initial state.

## Local setup

Requirements:

- Python 3.13
- A Gemini API key

Create and activate a virtual environment in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r app\requirements.txt
pip install -r scripts\requirements.txt
```

Copy `.env.example` to `.env` and add your key:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Run the remediation script locally after creating a Semgrep report:

```powershell
semgrep scan `
  --config "p/python" `
  --config "p/owasp-top-ten" `
  --json `
  --output semgrep-report.json `
  app

python scripts\ai_remediation.py
```

## Run tests and dependency audit

```powershell
pytest -q
pip-audit -r app\requirements.txt
```

## GitHub Actions

The workflow is located at
`.github/workflows/devsecops-ai-remediation-pipeline.yml`.

It runs after a push to a non-`main` branch when application, script,
dependency, or workflow files change. Add `GEMINI_API_KEY` as a repository
secret under **Settings > Secrets and variables > Actions**.

After a successful remediation, the workflow creates a dedicated branch and
opens a Pull Request against `main`. Every generated change still requires
human review before merging.

## Security limitations

LLM-generated code is not trusted automatically. The project therefore uses
structured AI responses, syntax validation, regression tests, and a final
Semgrep scan. These controls reduce risk but do not replace manual code review.
