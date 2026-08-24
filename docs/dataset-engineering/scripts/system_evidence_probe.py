#!/usr/bin/env python3
import ast
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import yaml

def get_file_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def probe():
    repo = Path(os.getcwd())
    out = {}
    
    # 1. Config
    cfg_p = repo / "app/rasa/config.yml"
    out["config_sha"] = get_file_sha256(cfg_p)
    with open(cfg_p) as f:
        out["config_data"] = yaml.safe_load(f)
        
    # 2. Domain
    dom_p = repo / "app/rasa/domain.yml"
    out["domain_sha"] = get_file_sha256(dom_p)
    with open(dom_p) as f:
        out["domain_data"] = yaml.safe_load(f)
        
    # 3. Hardware DB
    hw_p = repo / "app/services/recommendation/hardware_db.json"
    out["hw_sha"] = get_file_sha256(hw_p)
    with open(hw_p) as f:
        out["hw_data"] = json.load(f)
        
    # 4. Actions
    act_p = repo / "app/rasa/actions/actions.py"
    out["act_sha"] = get_file_sha256(act_p)
    with open(act_p) as f:
        out["act_src"] = f.read()
        
    # 5. Recommendation services
    spec_rec_p = repo / "app/services/recommendation/spec_recommender.py"
    out["spec_rec_sha"] = get_file_sha256(spec_rec_p)
    with open(spec_rec_p) as f:
        out["spec_rec_src"] = f.read()
        
    upg_adv_p = repo / "app/services/recommendation/upgrade_advisor.py"
    out["upg_adv_sha"] = get_file_sha256(upg_adv_p)
    with open(upg_adv_p) as f:
        out["upg_adv_src"] = f.read()
        
    # 6. NLP services
    prep_p = repo / "app/services/nlp/preprocessing.py"
    out["prep_sha"] = get_file_sha256(prep_p)
    with open(prep_p) as f:
        out["prep_src"] = f.read()
        
    thai_tok_p = repo / "app/rasa/thai_tokenizer.py"
    out["thai_tok_sha"] = get_file_sha256(thai_tok_p)
    with open(thai_tok_p) as f:
        out["thai_tok_src"] = f.read()
        
    typo_p = repo / "app/services/nlp/typo_dict.json"
    out["typo_sha"] = get_file_sha256(typo_p) if typo_p.exists() else None
    
    # 7. Line channel & Flex
    line_ch_p = repo / "app/rasa/line_channel.py"
    out["line_ch_sha"] = get_file_sha256(line_ch_p) if line_ch_p.exists() else None
    if line_ch_p.exists():
        with open(line_ch_p) as f:
            out["line_ch_src"] = f.read()
            
    flex_p = repo / "app/rasa/actions/flex.py"
    out["flex_sha"] = get_file_sha256(flex_p) if flex_p.exists() else None
    if flex_p.exists():
        with open(flex_p) as f:
            out["flex_src"] = f.read()
            
    # 8. SQLite
    db_p = repo / "data/analytics.db"
    out["db_exists"] = db_p.exists()
    if db_p.exists():
        out["db_sha"] = get_file_sha256(db_p)
        conn = sqlite3.connect(db_p)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        out["tables"] = {}
        for t in tables:
            tname = t[0]
            cur.execute(f"PRAGMA table_info({tname});")
            out["tables"][tname] = cur.fetchall()
        conn.close()
        
    # 9. Development NLU Entity counts
    dev_p = repo / "app/rasa/data/nlu.yml"
    with open(dev_p) as f:
        dev_yaml = yaml.safe_load(f)
    entities_found = []
    for item in dev_yaml.get("nlu", []):
        raw_exs = item.get("examples", "")
        matches = re.findall(r'\[(.*?)\]\((.*?)\)', raw_exs)
        for val, ent in matches:
            entities_found.append((ent, val))
    out["entity_counts"] = {}
    for ent, val in entities_found:
        out["entity_counts"][ent] = out["entity_counts"].get(ent, 0) + 1
    out["total_entities"] = len(entities_found)
    
    # 10. Existing tests
    test_files = list((repo / "tests").glob("*.py"))
    out["tests"] = {}
    for tf in test_files:
        with open(tf) as f:
            out["tests"][tf.name] = {
                "sha": get_file_sha256(tf),
                "lines": len(f.readlines())
            }
            
    print("PROBE COMPLETE")
    with open(repo / "tmp_salvage/system_probe_summary.json", "w") as f:
        # filter strings for safe dump
        clean_out = {k: v for k, v in out.items() if not k.endswith("_src")}
        json.dump(clean_out, f, indent=2)

if __name__ == "__main__":
    probe()
