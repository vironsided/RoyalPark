"""
Converts azericard-technical-spec.md -> azericard-technical-spec.pdf
Uses markdown -> styled HTML -> Edge/Chrome headless --print-to-pdf
Run:  python generate_pdf.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import markdown

SRC = Path(__file__).with_name("azericard-technical-spec.md")
HTML_TMP = Path(__file__).with_name("_spec_temp.html")
DST = Path(__file__).with_name("azericard-technical-spec.pdf")

CSS = """
<style>
  @page { margin: 20mm 18mm 20mm 18mm; }
  body {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #2d2d2d;
    max-width: 100%;
  }
  h1 {
    color: #1a3a52;
    font-size: 22pt;
    border-bottom: 3px solid #3a6582;
    padding-bottom: 8px;
    margin-top: 0;
  }
  h2 {
    color: #2c5570;
    font-size: 15pt;
    border-bottom: 1px solid #d0d8e0;
    padding-bottom: 4px;
    margin-top: 28px;
  }
  h3 {
    color: #3a6582;
    font-size: 12pt;
    margin-top: 18px;
  }
  table {
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0 16px 0;
    font-size: 10pt;
  }
  th {
    background-color: #3a6582;
    color: #fff;
    padding: 7px 10px;
    text-align: left;
    font-weight: 600;
  }
  td {
    padding: 6px 10px;
    border-bottom: 1px solid #e2e8f0;
    vertical-align: top;
  }
  tr:nth-child(even) td { background-color: #f8fafb; }
  pre {
    background: #f4f6f8;
    border: 1px solid #e0e4e8;
    border-radius: 4px;
    padding: 10px 14px;
    font-size: 9pt;
    font-family: 'Consolas', 'Courier New', monospace;
    line-height: 1.4;
    overflow-x: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
  }
  code {
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 9.5pt;
    background: #eef1f5;
    padding: 1px 4px;
    border-radius: 3px;
  }
  pre code { background: none; padding: 0; }
  strong { color: #1a3a52; }
  hr { border: none; border-top: 2px solid #d0d8e0; margin: 24px 0; }
  ul, ol { padding-left: 22px; }
  li { margin-bottom: 3px; }
  p { margin: 6px 0; }
  blockquote {
    border-left: 4px solid #3a6582;
    margin: 12px 0;
    padding: 8px 16px;
    background: #f0f4f8;
    color: #3a5068;
  }
</style>
"""


def find_browser() -> str | None:
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    for name in ("msedge", "chrome", "google-chrome"):
        found = shutil.which(name)
        if found:
            return found
    return None


def build():
    md_text = SRC.read_text(encoding="utf-8")
    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "codehilite", "toc"],
        extension_configs={"codehilite": {"guess_lang": False, "css_class": "highlight"}},
    )

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>RoyalPark — AzeriCard Technical Specification</title>
{CSS}
</head>
<body>
{html_body}
</body>
</html>"""

    HTML_TMP.write_text(full_html, encoding="utf-8")
    print(f"HTML generated -> {HTML_TMP}")

    browser = find_browser()
    if not browser:
        print("ERROR: Could not find Edge or Chrome. Open the HTML file in a browser and print to PDF manually.")
        sys.exit(1)

    print(f"Using browser: {browser}")
    cmd = [
        browser,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        f"--print-to-pdf={DST}",
        "--print-to-pdf-no-header",
        str(HTML_TMP.resolve().as_uri()),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if DST.exists() and DST.stat().st_size > 0:
        HTML_TMP.unlink(missing_ok=True)
        print(f"PDF saved -> {DST}  ({DST.stat().st_size // 1024} KB)")
    else:
        print(f"PDF generation may have failed. stderr: {result.stderr}")
        print(f"HTML file kept at: {HTML_TMP} — you can open it in a browser and print to PDF.")


if __name__ == "__main__":
    build()
