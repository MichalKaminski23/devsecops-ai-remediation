import json
import os
import re
import sys
from collections import defaultdict
from google import genai
from google.genai import types
from dotenv import load_dotenv

REPORT_FILE = "semgrep-report.json"
PR_SUMMARY_FILE = "pr_summary.md"

load_dotenv()


def strip_markdown_fences(text: str) -> str:
    """Usuwa znaczniki bloków kodu Markdown (```python ... ```), jeśli model je doda."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*\n", "", cleaned)
    cleaned = re.sub(r"\n```\s*$", "", cleaned)
    return cleaned.strip() + "\n"


def load_findings(report_path: str) -> dict:
    if not os.path.exists(report_path):
        print(f"[INFO] Brak pliku raportu: {report_path}")
        return {}

    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    findings_by_file = defaultdict(list)
    for item in data.get("results", []):
        file_path = item.get("path")
        findings_by_file[file_path].append(
            {
                "rule_id": item.get("check_id"),
                "severity": item.get("extra", {}).get("severity", "WARNING"),
                "message": item.get("extra", {}).get("message", ""),
                "line_start": item.get("start", {}).get("line"),
                "line_end": item.get("end", {}).get("line"),
            }
        )

    return findings_by_file


def remediate_file(client: genai.Client, file_path: str, findings: list) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        original_code = f.read()

    findings_text = json.dumps(findings, indent=2, ensure_ascii=False)

    system_instruction = (
        "Jesteś starszym inżynierem AppSec (Application Security). "
        "Twoim zadaniem jest usunięcie podatności bezpieczeństwa wskazanych przez skaner SAST "
        "z zachowaniem 100% dotychczasowej logiki biznesowej aplikacji. "
        "Zwróć WYŁĄCZNIE kompletny, poprawiony kod źródłowy pliku — bez żadnych wyjaśnień, "
        "komentarzy wstępnych ani znaczników Markdown."
    )

    user_prompt = (
        f"Plik: {file_path}\n\n"
        f"Wykryte podatności (raport Semgrep):\n{findings_text}\n\n"
        f"Aktualny kod pliku:\n{original_code}"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1,  # Niska temperatura zapewnia deterministyczny, bezpieczny kod
        ),
    )

    fixed_code = strip_markdown_fences(response.text)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(fixed_code)

    return findings_text


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] Brak zmiennej środowiskowej GEMINI_API_KEY.")
        sys.exit(1)

    findings_by_file = load_findings(REPORT_FILE)
    if not findings_by_file:
        print("[OK] Nie wykryto żadnych podatności. Pipeline kończy pracę.")
        sys.exit(0)

    client = genai.Client(api_key=api_key)
    summary_lines = [
        "## Automatyczna remediacja podatności (AI DevSecOps Bot)\n",
        "Skaner **Semgrep** wykrył podatności w kodzie. Poniżej znajduje się podsumowanie zmian wygenerowanych automatycznie do weryfikacji przez zespół (*Human-in-the-Loop*):\n",
    ]

    for file_path, findings in findings_by_file.items():
        print(f"[AI] Analiza i naprawa pliku: {file_path} (liczba alertów: {len(findings)})")
        remediate_file(client, file_path, findings)

        summary_lines.append(f"### Plik: `{file_path}`")
        for f_item in findings:
            summary_lines.append(
                f"- **[{f_item['severity']}]** `{f_item['rule_id']}` (linia {f_item['line_start']}): {f_item['message']}"
            )
        summary_lines.append("")

    summary_lines.append(
        "> **Uwaga bezpieczeństwa:** Kod wygenerowany przez model LLM wymaga przeglądu (Code Review) oraz przejścia testów automatycznych przed włączeniem do gałęzi `main`."
    )

    with open(PR_SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))

    print("[DONE] Zakończono generowanie poprawek oraz opisu Pull Requesta.")


if __name__ == "__main__":
    main()
