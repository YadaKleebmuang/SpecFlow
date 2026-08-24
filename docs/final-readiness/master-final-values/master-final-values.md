# SpecFlow — Master Final Values Summary
## Authoritative Single Source of Truth for Thesis Chapters 3–5

## Master Values Table
| Dimension / Parameter | Authoritative Final Value | Evidence Source |
| :--- | :--- | :--- |
| **Project Name** | SpecFlow | Physical Repository |
| **System Domain** | Thai Conversational PC Spec Recommender | Architecture / Domain |
| **Primary Channel** | LINE Official Account | `line_channel.py` / `credentials.yml` |
| **Python Version** | `3.9.6` | Runtime Environment |
| **Rasa Version** | `3.6.21` | Runtime Environment |
| **rasa-sdk Version** | `3.6.2` | Runtime Environment |
| **PyThaiNLP Version** | `5.3.4` | Runtime Environment |
| **Development Dataset Rows** | `800` examples (15 intents) | `app/rasa/data/nlu.yml` (`37b05d1f44de...`) |
| **Development Entity Spans** | `187` spans (4 types) | `entity-baseline-evidence.md` |
| **Holdout Dataset Rows** | `200` examples (15 intents) | `locked-holdout-v1.yml` (`61d0c3c237d7...`) |
| **Holdout Evaluation Count** | `1` (Single authorized evaluation) | `final-holdout-evaluation-manifest.json` |
| **Development CV Accuracy (OOF)** | `0.91250000` (91.25%, 730/800) | `oof-predictions.csv` |
| **Development CV Macro F1 (OOF)** | `0.91355855` (91.36%) | `oof-predictions.csv` |
| **Development CV 5-Fold Mean Accuracy** | `0.91250000 ± 0.01397542` | `cv-summary-metrics.json` |
| **Development CV 5-Fold Mean Macro F1** | `0.90846876 ± 0.02069854` | `cv-summary-metrics.json` |
| **Development Entity Macro F1** | `0.4568 ± 0.0761` (Token-level DIET) | `entity-aggregate-metrics.json` |
| **Final Model Path** | `final_models/run-20260825-001846/20260825-001851-woolen-billet.tar.gz` | Physical Model Artifact |
| **Final Model SHA-256** | `86a76534116c8298b39aaa8ddbaddc257d0fb8276da905da68675f7fdeff6dd7` | `final-model-training-manifest.json` |
| **Final Model Training Time** | `3594.66` seconds (59.9 min) | `final-model-training-manifest.json` |
| **Runtime Verification Cases** | `8 / 8 PASS` | `final-model-runtime-verification-manifest.json` |
| **Holdout Test Correct** | `141` | `holdout-predictions.csv` |
| **Holdout Test Errors** | `59` | `holdout-errors.csv` |
| **Final Test Accuracy** | `0.70500000` (70.50%) | `holdout-intent-metrics.json` |
| **Final Test Macro Precision** | `0.78831203` (78.83%) | `holdout-intent-metrics.json` |
| **Final Test Macro Recall** | `0.71515891` (71.52%) | `holdout-intent-metrics.json` |
| **Final Test Macro F1-Score** | `0.72564964` (72.56%) | `holdout-intent-metrics.json` |
| **Final Test Weighted Precision** | `0.75312253` (75.31%) | `holdout-intent-metrics.json` |
| **Final Test Weighted Recall** | `0.70500000` (70.50%) | `holdout-intent-metrics.json` |
| **Final Test Weighted F1-Score** | `0.70027716` (70.03%) | `holdout-intent-metrics.json` |
| **Holdout Fallback Count / Rate** | `10` / `5.00%` | `holdout-intent-metrics.json` |
| **Holdout Entity Scope** | `budget` entity only (`F1: 0.0800`) | `holdout-entity-evidence.json` |
| **System Functional Cases** | `16 / 16 PASS` | `system-e2e-evidence-manifest.json` |
| **Hardware Catalog Records** | `64` records (8 categories) | `hardware_db.json` (`341659f6384e...`) |
| **LINE E2E Verification Level** | `BACKEND E2E VERIFIED` (Live not proven) | `integration-test-results.json` |
| **Tracked Active Secrets** | `0` (Environment variable loading) | `security-evidence.json` |
| **Credential Rotation Status** | `REQUIRED (Outstanding action)` | `security-evidence.json` |
| **Analytics Database** | SQLite `user_searches` (Metric fields only) | `data/analytics.db` |

## Master Evidence Files
- **[master-final-values.json](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/master-final-values/master-final-values.json)**
- **[chapter-3-facts.md](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/master-final-values/chapter-3-facts.md)**
- **[chapter-4-facts.md](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/master-final-values/chapter-4-facts.md)**
- **[chapter-5-facts.md](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/master-final-values/chapter-5-facts.md)**
- **[report-safe-claims.md](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/master-final-values/report-safe-claims.md)**
- **[master-final-values-manifest.json](file:///Users/ploy/Desktop/mini_project/SpecFlow/docs/final-readiness/master-final-values/master-final-values-manifest.json)**
