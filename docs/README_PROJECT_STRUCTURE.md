# SpecFlow Project Navigation Guide

Quick navigation guide to key project components, models, and evidence artifacts.

---

## 🧭 Directory Quick Reference

| Objective | Target Path | Key Files / Subdirectories |
| :--- | :--- | :--- |
| **Chatbot & NLU Pipeline** | `app/rasa/` | [`config.yml`](file:///Users/ploy/Desktop/mini_project/SpecFlow/app/rasa/config.yml), [`domain.yml`](file:///Users/ploy/Desktop/mini_project/SpecFlow/app/rasa/domain.yml), [`thai_tokenizer.py`](file:///Users/ploy/Desktop/mini_project/SpecFlow/app/rasa/thai_tokenizer.py) |
| **Dialogue Rules & Stories** | `app/rasa/data/` | [`rules.yml`](file:///Users/ploy/Desktop/mini_project/SpecFlow/app/rasa/data/rules.yml), [`stories.yml`](file:///Users/ploy/Desktop/mini_project/SpecFlow/app/rasa/data/stories.yml) |
| **Development Dataset (800)** | `app/rasa/data/` | [`nlu.yml`](file:///Users/ploy/Desktop/mini_project/SpecFlow/app/rasa/data/nlu.yml) (800 examples, 15 intents, 187 entity spans) |
| **Holdout Dataset (200)** | `docs/dataset-engineering/holdout/` | [`locked-holdout-v1.yml`](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/dataset-engineering/holdout/locked-holdout-v1.yml) (200 examples) |
| **Recommendation Engine** | `app/services/recommendation/` | [`spec_recommender.py`](file:///Users/ploy/Desktop/mini_project/SpecFlow/app/services/recommendation/spec_recommender.py), [`upgrade_advisor.py`](file:///Users/ploy/Desktop/mini_project/SpecFlow/app/services/recommendation/upgrade_advisor.py), [`hardware_db.json`](file:///Users/ploy/Desktop/mini_project/SpecFlow/app/services/recommendation/hardware_db.json) |
| **Custom Action Server** | `app/rasa/actions/` | [`actions.py`](file:///Users/ploy/Desktop/mini_project/SpecFlow/app/rasa/actions/actions.py), [`flex.py`](file:///Users/ploy/Desktop/mini_project/SpecFlow/app/rasa/actions/flex.py) |
| **LINE Connector & Webhook** | `app/rasa/` | [`line_channel.py`](file:///Users/ploy/Desktop/mini_project/SpecFlow/app/rasa/line_channel.py), [`credentials.yml`](file:///Users/ploy/Desktop/mini_project/SpecFlow/app/rasa/credentials.yml) |
| **Final Trained Model** | `final_models/run-20260825-001846/` | `20260825-001851-woolen-billet.tar.gz` (SHA: `86a76534...`) |
| **Baseline 5-Fold CV Results** | `docs/dataset-engineering/cross-validation/baseline/` | [`oof-predictions.csv`](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/dataset-engineering/cross-validation/baseline/results/oof-predictions.csv), [`cv-summary-metrics.json`](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/dataset-engineering/cross-validation/baseline/results/cv-summary-metrics.json) |
| **Entity Baseline Evidence** | `docs/dataset-engineering/entity-evaluation/baseline/` | [`entity-baseline-evidence.md`](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/dataset-engineering/entity-evaluation/baseline/entity-baseline-evidence.md) |
| **Final Holdout Test Results** | `docs/final-readiness/final-holdout-evaluation/run-20260825-013923/` | [`final-holdout-evaluation.md`](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/final-holdout-evaluation/run-20260825-013923/final-holdout-evaluation.md), [`holdout-predictions.csv`](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/final-holdout-evaluation/run-20260825-013923/holdout-predictions.csv) |
| **System E2E Verification** | `docs/final-readiness/system-e2e-evidence/run-20260825-014623/` | [`system-e2e-evidence.md`](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/system-e2e-evidence/run-20260825-014623/system-e2e-evidence.md) (16/16 PASS) |
| **Master Thesis Facts** | `docs/final-readiness/master-final-values/` | [`chapter-3-facts.md`](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/master-final-values/chapter-3-facts.md), [`chapter-4-facts.md`](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/master-final-values/chapter-4-facts.md), [`chapter-5-facts.md`](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/master-final-values/chapter-5-facts.md), [`report-safe-claims.md`](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/master-final-values/report-safe-claims.md) |

---

## 📖 Key Documentation Files
- **[PROJECT_FILES.md](file:///Users/ploy/Desktop/mini_project/SpecFlow/PROJECT_FILES.md)**: Full Thai-language reference of all files, their purpose, and lock status.
- **[docs/PROJECT_CLEANUP_PLAN.md](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/PROJECT_CLEANUP_PLAN.md)**: Decision matrix of preserved vs cleaned artifacts.
- **[docs/PROJECT_CLEANUP_REPORT.md](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/PROJECT_CLEANUP_REPORT.md)**: Detailed report of the post-holdout cleanup execution.
