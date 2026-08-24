# SpecFlow Report-Safe Claims Reference Guide
## Single Source of Truth for Thesis Writing (Chapters 3, 4, and 5)

## 1. Approved Claims (Fully Supported by Physical Evidence)
- **Development Dataset**: Contains 800 examples across 15 intents with an intentionally unequal distribution reflecting the designed intent domain.
- **Holdout Dataset**: Unseen evaluation set containing 200 examples across 15 intents with zero duplicate overlap with Development.
- **Baseline 5-Fold Cross-Validation**: Achieved OOF Accuracy of **0.9125** (91.25%) and OOF Macro F1 of **0.9136** (91.36%) across the 800 Development examples.
- **Final Model Training**: Trained once on 100% of Development 800 (59.9 minutes, 0 errors, SHA: `86a76534...`).
- **Final Holdout Intent Performance**: Achieved Accuracy of **0.7050** (70.50%) and Macro F1 of **0.7256** (72.56%) on the locked 200-example Holdout set (141 correct, 59 errors).
- **Runtime Verification**: Passed 8/8 test cases verifying model loading, multi-turn forms, Action Server integration, and recommendation generation.
- **System Verification**: Passed 16/16 functional cases verifying full backend architecture, database lookups, fallback routing, and non-sensitive analytics.
- **Hardware Database**: Contains 64 physical component records across 8 categories (CPU: 14, GPU: 12, Motherboard: 10, RAM: 8, Storage: 5, PSU: 6, Case: 5, Cooler: 4).

## 2. Qualified Claims (Must Include Required Engineering Nuance)
- **Entity Extraction Evaluation**: Must be explicitly described as **token-level DIET evaluation** across sub-words/syllables, not span-level F1.
- **Holdout Entity Performance**: The Holdout entity metrics (`Precision: 0.1000`, `Recall: 0.0667`, `F1: 0.0800`) reflect **only the 15 `budget` entity annotations** present in the evaluable Holdout evidence.
- **LINE Integration**: Must be classified as **Backend E2E Verified, Live LINE Platform Delivery Not Proven** (connector and signature logic verified locally; live external webhook calls not executed).
- **Recommendation Engine**: Budget optimization is **budget-aware with tolerance warning**, not guaranteed to strictly equal or fall below the target budget.
- **Security Posture**: Repository is sanitized (0 tracked active secrets, env var loading), but credential rotation in the LINE Console is marked as **Production Security Action Outstanding**.
- **Analytics Storage**: Stores structured usage metrics (`usage_type`, `budget_requested`, `allocated_total_price`); does not store full conversational transcripts.

## 3. Forbidden / Unsupported Claims (Strictly Prohibited)
- **DO NOT claim**: Final Model Accuracy is 91.25% (91.25% is the Development 5-Fold CV baseline, not final Holdout).
- **DO NOT claim**: Final Holdout Macro F1 is ~90% (Final Holdout Macro F1 is 72.56%).
- **DO NOT claim**: The Development dataset is "balanced" (Distribution is intentionally non-uniform).
- **DO NOT claim**: Holdout fallback utterances were "Out-of-Distribution (OOD)" (Correct statement: FallbackClassifier triggered on 10 Holdout utterances per configured confidence threshold).
- **DO NOT claim**: Final Entity F1 of 0.08 represents all 4 entity types (It represents only `budget`).
- **DO NOT claim**: Live LINE end-to-end messaging was verified in production.
- **DO NOT claim**: ResponseSelector handles general FAQ intents (FAQs are handled via Custom Actions).
- **DO NOT claim**: Credential rotation is complete without external administrative verification.
