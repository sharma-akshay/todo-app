#!/usr/bin/env python3
import json, os, sys
from datetime import datetime

REPORT_FILES = {
    "Gitleaks": "gitleaks-report.json",
    "Semgrep": "semgrep-report.json",
    "OSV Scanner": "osv-report.json",
    "SBOM (Syft)": "sbom.json",
    "Grype": "grype-report.json",
    "Trivy FS": "trivy-fs-report.json",
    "Checkov": "checkov-report.json"
}

def load_json(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def count_semgrep(findings):
    if not findings or "results" not in findings:
        return []
    data = []
    for i in findings["results"]:
        sev = i.get("extra", {}).get("severity", "UNKNOWN")
        msg = i.get("extra", {}).get("message", "")
        file = i.get("path", "")
        data.append((sev, msg, file))
    return data

def count_gitleaks(data):
    leaks = data.get("leaks", []) if data else []
    return [(l.get("ruleID"), l.get("description")) for l in leaks]

def count_grype(data):
    vulns = []
    if not data: 
        return vulns
    for match in data.get("matches", []):
        sev = match["vulnerability"]["severity"]
        vid = match["vulnerability"]["id"]
        pkg = match["artifact"]["name"]
        vulns.append((sev, vid, pkg))
    return vulns

def count_trivy(data):
    vulns = []
    if not data:
        return vulns
    for result in data.get("Results", []):
        for v in result.get("Vulnerabilities", []) or []:
            vulns.append((v.get("Severity"), v.get("VulnerabilityID"), result.get("Target")))
    return vulns

def count_osv(data):
    vulns = []
    if not data:
        return vulns
    for r in data.get("results", []):
        for p in r.get("packages", []):
            for v in p.get("vulnerabilities", []):
                vulns.append((v.get("severity", "UNKNOWN"), v.get("id"), p.get("package", {}).get("name")))
    return vulns

def count_checkov(data):
    vulns = []
    if not data:
        return vulns
    for res in data:
        for f in res.get("failures", []):
            vulns.append(("HIGH", f.get("check_id"), f.get("file_path")))
    return vulns

def generate_markdown(summary):
    md = []
    md.append(f"# 🔐 Security Scan Summary")
    md.append(f"Generated on **{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**\n")
    md.append("---\n")

    for tool, items in summary.items():
        md.append(f"## 🛡 {tool}")
        if not items:
            md.append("✔ **No issues found.**\n")
            continue

        table = ["| Severity | ID/Message | File/Package |",
                 "|---------|------------|--------------|"]
        for sev, a, b in items:
            table.append(f"| {sev} | {a} | {b} |")
        md.extend(table)
        md.append("\n")

    return "\n".join(md)

def main():
    summary = {}

    for tool, filename in REPORT_FILES.items():
        print(f"Processing {filename} ...")
        data = load_json(filename)
        if tool == "Semgrep":
            summary[tool] = count_semgrep(data)
        elif tool == "Gitleaks":
            summary[tool] = count_gitleaks(data)
        elif tool == "Grype":
            summary[tool] = count_grype(data)
        elif tool == "Trivy FS":
            summary[tool] = count_trivy(data)
        elif tool == "OSV Scanner":
            summary[tool] = count_osv(data)
        elif tool == "Checkov":
            summary[tool] = count_checkov(data)
        else:
            summary[tool] = []

    md = generate_markdown(summary)

    # Save file
    with open("security-summary.md", "w") as f:
        f.write(md)

    # Print in Jenkins log
    print("\n===== SECURITY SUMMARY =====\n")
    print(md)
    print("\n============================\n")

if __name__ == "__main__":
    main()
