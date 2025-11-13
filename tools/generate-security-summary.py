#!/usr/bin/env python3
"""
generate-security-summary.py
Reads standard JSON reports produced by the pipeline and creates:
 - security-summary.md   (markdown summary)
 - security-dashboard.html (simple HTML dashboard)
 - *.pretty.json copies for readability
"""

import json, os, glob, datetime, html, sys

WORKDIR = os.getcwd()
REPORT_FILES = {
    "semgrep": "semgrep-report.json",
    "gitleaks": "gitleaks-report.json",
    "osv": "osv-report.json",
    "sbom": "sbom.json",
    "grype": "grype-report.json",
    "trivy_fs": "trivy-fs-report.json",
    "checkov": "checkov-report.json",
    "grype_frontend": "grype-frontend.json",
    "grype_backend": "grype-backend.json",
    "trivy_frontend": "trivy-frontend.json",
    "trivy_backend": "trivy-backend.json",
    "sbom_frontend": "sbom-frontend.json",
    "sbom_backend": "sbom-backend.json"
}

def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

def write_pretty(path):
    data = load_json(path)
    if data is None:
        return
    out = path + ".pretty.json"
    try:
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def count_semgrep(j):
    if not j: return 0, 0
    findings = j.get("results", [])
    total = len(findings)
    blocking = 0
    for r in findings:
        sev = r.get("extra", {}).get("severity", "").upper()
        if sev in ("HIGH","CRITICAL","ERROR"):
            blocking += 1
    return total, blocking

def count_gitleaks(j):
    if not j: return 0
    return len(j) if isinstance(j, list) else (len(j.keys()) if isinstance(j, dict) else 0)

def scan_for_severity(data, field_names=("Severity","severity","level")):
    # generic walker: returns count of CRITICAL
    if not data: return 0
    s = json.dumps(data)
    return s.lower().count("critical")

def main():
    summary_lines = []
    html_sections = []
    now = datetime.datetime.utcnow().isoformat() + "Z"
    total_critical = 0

    summary_lines.append(f"# Security Summary\n\nGenerated: {now}\n\n")

    for key, fname in REPORT_FILES.items():
        if not os.path.exists(fname):
            continue
        summary_lines.append(f"## {fname}\n")
        data = load_json(fname)
        write_pretty(fname)
        # basic heuristics per tool
        if key == "semgrep":
            total, blocking = count_semgrep(data)
            summary_lines.append(f"- Semgrep findings: {total} (blocking/high: {blocking})\n")
            total_critical += blocking
        elif key == "gitleaks":
            n = count_gitleaks(data)
            summary_lines.append(f"- Gitleaks findings (secrets): {n}\n")
            if n > 0:
                total_critical += n
        elif key.startswith("grype") or key.startswith("trivy") or key=="grype":
            c = scan_for_severity(data)
            summary_lines.append(f"- Vulnerabilities (approximate critical count via text search): {c}\n")
            total_critical += c
        elif key == "osv":
            c = scan_for_severity(data)
            summary_lines.append(f"- OSV scanner critical-like matches: {c}\n")
            total_critical += c
        elif key == "checkov":
            # checkov JSON usually contains 'results' with 'failed_checks'
            failed = 0
            try:
                results = data.get("results", {})
                failed = len(results.get("failed_checks", []))
            except Exception:
                failed = 0
            summary_lines.append(f"- Checkov failed checks: {failed}\n")
            total_critical += failed
        else:
            # generic fallback
            c = scan_for_severity(data)
            summary_lines.append(f"- Generic critical-like matches: {c}\n")
            total_critical += c

        # add link section for HTML to point to pretty JSON
        pretty = fname + ".pretty.json"
        if os.path.exists(pretty):
            link = html.escape(pretty)
        else:
            link = html.escape(fname)
        html_sections.append((fname, link))

    summary_lines.append("\n---\n")
    summary_lines.append(f"**Total approximate critical findings:** {total_critical}\n\n")

    # Write markdown
    with open("security-summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))

    # Write small HTML dashboard
    with open("security-dashboard.html", "w", encoding="utf-8") as f:
        f.write("<!doctype html>\n<html>\n<head>\n<meta charset='utf-8'>\n<title>Security Dashboard</title>\n<style>body{font-family:Segoe UI,Arial; margin:20px} h1{color:#333} table{border-collapse:collapse;width:100%} th,td{border:1px solid #ddd;padding:8px} th{background:#f4f4f4}</style>\n</head>\n<body>\n")
        f.write("<h1>Security Dashboard</h1>\n")
        f.write(f"<p>Generated: {html.escape(now)}</p>\n")
        f.write("<h2>Summary</h2>\n")
        f.write(f"<p>Total approximate CRITICAL findings: <strong>{total_critical}</strong></p>\n")
        f.write("<h2>Reports</h2>\n")
        f.write("<table><thead><tr><th>Report file</th><th>Preview</th></tr></thead><tbody>\n")
        for fname, link in html_sections:
            f.write(f"<tr><td>{html.escape(fname)}</td><td><a href=\"{html.escape(link)}\">Open</a></td></tr>\n")
        f.write("</tbody></table>\n")
        f.write("<p>Notes: this is a lightweight dashboard for quick triage. Use the pretty JSON files (or load into a SARIF viewer) for full details.</p>\n")
        f.write("</body></html>\n")

    print("Generated security-summary.md and security-dashboard.html (and pretty JSONs where possible).")

if __name__ == "__main__":
    main()
