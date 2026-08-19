import os
import re
import sys
import json
import yaml
import hashlib
import random
import shutil
import subprocess
import datetime
import statistics
from collections import defaultdict

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

NLU_PATH = os.path.join(PROJECT_ROOT, 'app', 'rasa', 'data', 'nlu.yml')
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'app', 'rasa', 'config.yml')
DOMAIN_PATH = os.path.join(PROJECT_ROOT, 'app', 'rasa', 'domain.yml')
OUT_DIR = os.path.join(PROJECT_ROOT, 'app', 'rasa', 'results', 'cross_validation_v2')
VENV_RASA = os.path.join(PROJECT_ROOT, 'venv', 'Scripts', 'rasa.exe')

def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def parse_nlu_blocks(path):
    intents = {}
    current_intent = None
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line_str = line.strip()
            if line_str.startswith('- intent:'):
                current_intent = line_str.replace('- intent:', '').strip()
                intents[current_intent] = []
            elif line_str.startswith('- ') and current_intent:
                ex = line_str[2:].strip()
                if ex:
                    intents[current_intent].append(ex)
    return intents

def write_nlu_yaml(path, intents_dict):
    data = {"version": "3.1", "nlu": []}
    for intent, examples in intents_dict.items():
        data["nlu"].append({
            "intent": intent,
            "examples": "\n".join([f"- {ex}" for ex in examples]) + "\n"
        })
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

def get_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:10]

def main():
    print("=" * 80)
    print("[SpecFlow] Starting Formal 5-Fold Stratified Cross-Validation v2")
    print("=" * 80)

    import pythainlp
    import rasa

    py_version = sys.version.split()[0]
    rasa_version = rasa.__version__
    pythai_version = pythainlp.__version__
    seed = 42

    os.makedirs(OUT_DIR, exist_ok=True)

    nlu_intents = parse_nlu_blocks(NLU_PATH)
    all_intents = sorted(list(nlu_intents.keys()))

    # Stratified 5-Fold Splitter grouped by unique text items (Zero Text Overlap Guaranteed)
    folds_train = [defaultdict(list) for _ in range(5)]
    folds_val = [defaultdict(list) for _ in range(5)]

    for intent in all_intents:
        # Group identical texts together so they never leak across train/val
        text_counts = defaultdict(int)
        for ex in nlu_intents[intent]:
            text_counts[ex] += 1
        
        unique_examples = sorted(list(text_counts.keys()))
        rng = random.Random(seed)
        rng.shuffle(unique_examples)
        
        for idx, u_ex in enumerate(unique_examples):
            fold_idx = idx % 5
            copies = [u_ex] * text_counts[u_ex]
            folds_val[fold_idx][intent].extend(copies)
            for f in range(5):
                if f != fold_idx:
                    folds_train[f][intent].extend(copies)

    # Build fold_manifest.json
    manifest_folds = []
    for f in range(5):
        train_count = sum(len(v) for v in folds_train[f].values())
        val_count = sum(len(v) for v in folds_val[f].values())
        val_hashes = [get_hash(ex) for intent in folds_val[f] for ex in folds_val[f][intent]]
        
        manifest_folds.append({
            "fold": f + 1,
            "train_samples": train_count,
            "val_samples": val_count,
            "train_intent_distribution": {k: len(v) for k, v in folds_train[f].items()},
            "val_intent_distribution": {k: len(v) for k, v in folds_val[f].items()},
            "val_sample_hashes": val_hashes
        })

    manifest = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "python_version": py_version,
        "rasa_version": rasa_version,
        "pythainlp_version": pythai_version,
        "random_seed": seed,
        "total_training_dataset_samples": sum(len(v) for v in nlu_intents.values()),
        "folds": manifest_folds
    }

    manifest_path = os.path.join(OUT_DIR, 'fold_manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"[OK] Saved Fold Manifest: {manifest_path}")

    # Per-fold Training & Evaluation Loop
    fold_intent_metrics_list = []
    fold_entity_metrics_list = []

    for f in range(5):
        fold_num = f + 1
        print(f"\n" + "-" * 60)
        print(f"Training & Evaluating Fold {fold_num} / 5")
        print("-" * 60)

        tmp_dir = os.path.join(OUT_DIR, f"tmp_fold_{fold_num}")
        train_yml = os.path.join(tmp_dir, "train.yml")
        val_yml = os.path.join(tmp_dir, "val.yml")
        models_dir = os.path.join(tmp_dir, "models")
        eval_dir = os.path.join(tmp_dir, "eval")

        write_nlu_yaml(train_yml, folds_train[f])
        write_nlu_yaml(val_yml, folds_val[f])

        # Verify zero text overlap
        train_texts = set(ex for intent in folds_train[f] for ex in folds_train[f][intent])
        val_texts = set(ex for intent in folds_val[f] for ex in folds_val[f][intent])
        overlap = train_texts.intersection(val_texts)
        if overlap:
            raise ValueError(f"Fold {fold_num} has train/val text overlap: {overlap}")

        print(f"   [1/2] Training Fold {fold_num} model (Train count: {sum(len(v) for v in folds_train[f].values())})...")
        cmd_train = [
            VENV_RASA, "train", "nlu",
            "--config", CONFIG_PATH,
            "--nlu", train_yml,
            "--out", models_dir
        ]
        res_train = subprocess.run(cmd_train, cwd=os.path.join(PROJECT_ROOT, "app", "rasa"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
        if res_train.returncode != 0:
            print(f"[ERR] Training Fold {fold_num} failed:")
            print(res_train.stdout)
            sys.exit(1)

        model_files = [os.path.join(models_dir, m) for m in os.listdir(models_dir) if m.endswith('.tar.gz')]
        if not model_files:
            raise FileNotFoundError(f"No model archive generated for Fold {fold_num}")
        latest_model = sorted(model_files)[-1]
        print(f"   Model generated: {os.path.basename(latest_model)}")

        print(f"   [2/2] Evaluating Fold {fold_num} model on validation subset (Val count: {sum(len(v) for v in folds_val[f].values())})...")
        cmd_test = [
            VENV_RASA, "test", "nlu",
            "--model", latest_model,
            "--nlu", val_yml,
            "--out", eval_dir
        ]
        res_test = subprocess.run(cmd_test, cwd=os.path.join(PROJECT_ROOT, "app", "rasa"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
        if res_test.returncode != 0:
            print(f"[ERR] Evaluation Fold {fold_num} failed:")
            print(res_test.stdout)
            sys.exit(1)

        # Parse intent report
        intent_report_path = os.path.join(eval_dir, "intent_report.json")
        with open(intent_report_path, "r", encoding="utf-8") as rf:
            intent_data = json.load(rf)

        acc = intent_data.get("accuracy", 0.0)
        macro_p = intent_data.get("macro avg", {}).get("precision", 0.0)
        macro_r = intent_data.get("macro avg", {}).get("recall", 0.0)
        macro_f1 = intent_data.get("macro avg", {}).get("f1-score", 0.0)
        weight_p = intent_data.get("weighted avg", {}).get("precision", 0.0)
        weight_r = intent_data.get("weighted avg", {}).get("recall", 0.0)
        weight_f1 = intent_data.get("weighted avg", {}).get("f1-score", 0.0)
        support = intent_data.get("macro avg", {}).get("support", 0)

        intent_metrics = {
            "fold": fold_num,
            "train_samples": sum(len(v) for v in folds_train[f].values()),
            "val_samples": sum(len(v) for v in folds_val[f].values()),
            "accuracy": acc,
            "macro_precision": macro_p,
            "macro_recall": macro_r,
            "macro_f1": macro_f1,
            "weighted_precision": weight_p,
            "weighted_recall": weight_r,
            "weighted_f1": weight_f1,
            "support": support,
            "intent_breakdown": {k: v for k, v in intent_data.items() if k not in ["accuracy", "macro avg", "weighted avg", "micro avg"]}
        }

        intent_metric_path = os.path.join(OUT_DIR, f"fold_{fold_num}_intent_metrics.json")
        with open(intent_metric_path, "w", encoding="utf-8") as jf:
            json.dump(intent_metrics, jf, ensure_ascii=False, indent=2)

        # Parse entity report
        entity_report_path = os.path.join(eval_dir, "DIETClassifier_report.json")
        with open(entity_report_path, "r", encoding="utf-8") as ef:
            entity_data = json.load(ef)

        ent_acc = entity_data.get("accuracy", entity_data.get("micro avg", {}).get("f1-score", 0.0))
        ent_macro_p = entity_data.get("macro avg", {}).get("precision", 0.0)
        ent_macro_r = entity_data.get("macro avg", {}).get("recall", 0.0)
        ent_macro_f1 = entity_data.get("macro avg", {}).get("f1-score", 0.0)
        ent_weight_f1 = entity_data.get("weighted avg", {}).get("f1-score", 0.0)
        ent_support = entity_data.get("macro avg", {}).get("support", 0)

        entity_metrics = {
            "fold": fold_num,
            "entity_support": ent_support,
            "accuracy": ent_acc,
            "macro_precision": ent_macro_p,
            "macro_recall": ent_macro_r,
            "macro_f1": ent_macro_f1,
            "weighted_f1": ent_weight_f1,
            "entity_breakdown": {k: v for k, v in entity_data.items() if k not in ["accuracy", "macro avg", "weighted avg", "micro avg"]}
        }

        entity_metric_path = os.path.join(OUT_DIR, f"fold_{fold_num}_entity_metrics.json")
        with open(entity_metric_path, "w", encoding="utf-8") as jf:
            json.dump(entity_metrics, jf, ensure_ascii=False, indent=2)

        fold_intent_metrics_list.append(intent_metrics)
        fold_entity_metrics_list.append(entity_metrics)

        print(f"   Fold {fold_num} Intent Acc: {acc:.4f} | Macro F1: {macro_f1:.4f} | Entity Macro F1: {ent_macro_f1:.4f}")

    # Compute Statistical Mean & Sample SD across 5 folds
    print("\n" + "=" * 80)
    print("Computing Mean and Sample Standard Deviation Across 5 Folds")
    print("=" * 80)

    def calc_stats(values):
        m = statistics.mean(values)
        sd = statistics.stdev(values) if len(values) > 1 else 0.0
        return {
            "mean": round(m, 4),
            "sd": round(sd, 4),
            "str_4dec": f"{m:.4f} ± {sd:.4f}",
            "str_pct": f"{m*100:.2f}% ± {sd*100:.2f}%"
        }

    intent_acc_vals = [m["accuracy"] for m in fold_intent_metrics_list]
    intent_mp_vals = [m["macro_precision"] for m in fold_intent_metrics_list]
    intent_mr_vals = [m["macro_recall"] for m in fold_intent_metrics_list]
    intent_mf1_vals = [m["macro_f1"] for m in fold_intent_metrics_list]
    intent_wf1_vals = [m["weighted_f1"] for m in fold_intent_metrics_list]

    ent_acc_vals = [m["accuracy"] for m in fold_entity_metrics_list]
    ent_mp_vals = [m["macro_precision"] for m in fold_entity_metrics_list]
    ent_mr_vals = [m["macro_recall"] for m in fold_entity_metrics_list]
    ent_mf1_vals = [m["macro_f1"] for m in fold_entity_metrics_list]
    ent_wf1_vals = [m["weighted_f1"] for m in fold_entity_metrics_list]

    # Compute per-intent stats across 5 folds
    per_intent_stats = {}
    for intent in all_intents:
        p_list, r_list, f1_list, supp_list = [], [], [], []
        for m in fold_intent_metrics_list:
            b = m["intent_breakdown"].get(intent, {})
            p_list.append(b.get("precision", 0.0))
            r_list.append(b.get("recall", 0.0))
            f1_list.append(b.get("f1-score", 0.0))
            supp_list.append(b.get("support", 0))

        per_intent_stats[intent] = {
            "precision": calc_stats(p_list),
            "recall": calc_stats(r_list),
            "f1": calc_stats(f1_list),
            "total_support": sum(supp_list)
        }

    # Compute per-entity stats across 5 folds
    all_entities = set()
    for m in fold_entity_metrics_list:
        all_entities.update(m["entity_breakdown"].keys())
    all_entities = sorted(list(all_entities))

    per_entity_stats = {}
    for entity in all_entities:
        p_list, r_list, f1_list, supp_list = [], [], [], []
        for m in fold_entity_metrics_list:
            b = m["entity_breakdown"].get(entity, {})
            p_list.append(b.get("precision", 0.0))
            r_list.append(b.get("recall", 0.0))
            f1_list.append(b.get("f1-score", 0.0))
            supp_list.append(b.get("support", 0))

        per_entity_stats[entity] = {
            "precision": calc_stats(p_list),
            "recall": calc_stats(r_list),
            "f1": calc_stats(f1_list),
            "total_support": sum(supp_list)
        }

    summary = {
        "intent_overall": {
            "accuracy": calc_stats(intent_acc_vals),
            "macro_precision": calc_stats(intent_mp_vals),
            "macro_recall": calc_stats(intent_mr_vals),
            "macro_f1": calc_stats(intent_mf1_vals),
            "weighted_f1": calc_stats(intent_wf1_vals)
        },
        "entity_overall": {
            "accuracy": calc_stats(ent_acc_vals),
            "macro_precision": calc_stats(ent_mp_vals),
            "macro_recall": calc_stats(ent_mr_vals),
            "macro_f1": calc_stats(ent_mf1_vals),
            "weighted_f1": calc_stats(ent_wf1_vals)
        },
        "per_intent_stats": per_intent_stats,
        "per_entity_stats": per_entity_stats
    }

    summary_path = os.path.join(OUT_DIR, "cross_validation_summary_v2.json")
    with open(summary_path, "w", encoding="utf-8") as sf:
        json.dump(summary, sf, ensure_ascii=False, indent=2)

    print(f"[OK] Saved summary JSON: {summary_path}")
    print(f"Intent Accuracy:  {summary['intent_overall']['accuracy']['str_4dec']} ({summary['intent_overall']['accuracy']['str_pct']})")
    print(f"Intent Macro F1:  {summary['intent_overall']['macro_f1']['str_4dec']} ({summary['intent_overall']['macro_f1']['str_pct']})")
    print(f"Entity Macro F1:  {summary['entity_overall']['macro_f1']['str_4dec']} ({summary['entity_overall']['macro_f1']['str_pct']})")
    print("=" * 80)

if __name__ == "__main__":
    main()
