# Chapter 5 Facts Sheet — Discussion, Limitations & Future Work
## Source of Truth for Thesis Chapter 5 Discussion

## 1. Supported Discussion Findings
- **Generalization Gap**: Final Holdout test performance (Accuracy: 70.50%, Macro F1: 72.56%) was lower than Development 5-Fold cross-validation (Accuracy: 91.25%, Macro F1: 90.85%). This reveals a true out-of-sample generalization gap when exposed to unseen phrasing variations and salt noise in the independent test set.
- **Intent Strength Variations**:
  - High-performing intents on Holdout: `inform_current_specs` (Recall 1.0000, F1 0.8947), `upgrade_pc` (Recall 0.9310, F1 0.7013), `ask_ram_info` (F1 0.9091), `ask_ssd_hdd_diff` (F1 0.9091), `greet` (F1 0.9091).
  - Challenging intents on Holdout: `ask_gpu_info` (F1 0.4444), `inform_budget` (F1 0.5294), `optimize_performance` (Recall 0.4400), `inform_future_upgrade` (Recall 0.4286).
- **Fallback Classifier Utility**: FallbackClassifier successfully captured 10 low-confidence Holdout utterances (5.00%), preventing incorrect action routing and delivering user guidance.
- **Entity Extraction vs Intent Classification**: Entity extraction showed lower performance than intent classification across both Development (Macro F1 0.4568) and Holdout (`budget` F1 0.0800), attributable to token-level segmentation challenges in complex Thai technical compounding.
- **Dialogue & System Reliability**: Despite NLU variation, conversational multi-turn forms (`build_pc_form`, `upgrade_pc_form`) and slot-filling mechanisms successfully handled user dialogues and triggered hardware recommendation algorithms without failure in all runtime/functional tests.

## 2. Limitations
- **Token-Level Entity Representation**: Rasa evaluates DIET entities at the sub-word/token level rather than exact whole-phrase span matching.
- **Holdout Entity Annotation Scope**: The independent Holdout set contained evaluable entity annotations only for the `budget` entity (15 spans); entity generalization for `component_type`, `usage`, and `future_upgrade` was not separately measured on Holdout.
- **Offline Backend Verification**: Live external delivery through the LINE platform was not tested in this offline environment (evaluated as Backend E2E verified).
- **Credential Rotation Status**: Production security action (manual secret rotation in LINE Developers Console) remains outstanding.

## 3. Recommended Future Work
- **NLU Data Expansion**: Broaden training examples for overlapping intents (`inform_future_upgrade` vs `upgrade_pc`, `optimize_performance`).
- **Compound Entity Normalization**: Introduce specialized Thai hardware dictionary tokenization and character-level entity post-processing.
- **Complete Test Set Entity Tagging**: Fully annotate all 4 entity types across independent evaluation sets.
- **Live Production Telemetry**: Deploy in a staging LINE Official Account with live webhook monitoring and analytics tracking.
