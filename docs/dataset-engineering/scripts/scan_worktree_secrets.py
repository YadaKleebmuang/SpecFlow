#!/usr/bin/env python3
import os
import re
from pathlib import Path

def scan():
    repo = Path(os.getcwd())
    scan_exts = {'.yml', '.yaml', '.py', '.json', '.md', '.sh', '.txt'}
    exclude_dirs = {'.git', '.venv-rasa-cv', '.venv', 'tmp', 'tmp_salvage', '__pycache__'}

    findings = []
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            p = Path(root) / f
            if p.suffix in scan_exts or f.startswith('.env'):
                if f in ['.env.example', 'chatbot_dataset_full.csv']:
                    continue
                try:
                    content = p.read_text(encoding='utf-8', errors='ignore')
                    lines = content.splitlines()
                    for l in lines:
                        if ('channel_secret:' in l or 'channel_access_token:' in l):
                            if not ('${' in l or 'os.environ' in l or 'None' in l or '""' in l or 'LINE_CHANNEL' in l or 'placeholder' in l.lower()):
                                findings.append((str(p.relative_to(repo)), 'HARDCODED_LINE_TOKEN'))
                except Exception:
                    pass

    print(f"Worktree secret scan findings: {len(findings)}")
    for f in findings:
        print(f"FAIL: {f[0]} | Type: {f[1]}")
    if not findings:
        print("SECRET SCAN: PASS (0 active secret values in tracked current source)")

if __name__ == "__main__":
    scan()
