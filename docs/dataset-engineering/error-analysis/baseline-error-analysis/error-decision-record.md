# Development NLU Error Decision Record
## SpecFlow Baseline Stratified 5-Fold Cross-Validation Decision

## 1. Decision Scope
This document formally records the governance decision for the SpecFlow NLU development phase following the completion of the semantic error analysis on the 70 Baseline Out-of-Fold (OOF) misclassifications.
The decision evaluates whether physical changes to the locked **Development 800 dataset** (`app/rasa/data/nlu.yml`) or the **NLU pipeline configuration** (`app/rasa/config.yml`) are warranted before proceeding to the Final Configuration Freeze and Final Model Training.

## 2. Evidence Reviewed
- **Development Dataset**: `app/rasa/data/nlu.yml` (SHA: `37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d`)
- **Authoritative OOF Predictions**: `docs/dataset-engineering/cross-validation/baseline/results/oof-predictions.csv` (SHA: `b66e9e0eeda35ac7b45ac6b8ddcfaad0976cd770a38b7007428db0b73586cf47`)
- **Authoritative Error Inventory**: `docs/dataset-engineering/cross-validation/baseline/results/error-inventory.csv` (SHA: `b0f0bdcef0b044dec3f8df7ffa96e59cfb19a23d5b9d9d61f728e661523228e6`)
- **Error Analysis Detailed Record**: `docs/dataset-engineering/error-analysis/baseline-error-analysis/error-analysis-detailed.csv` (SHA: `57b216395c8c2ed95a94c566613bb25bb6bbf43eaa8a87722a2fffbc49876f7b`)
- **Error Category Summary**: `docs/dataset-engineering/error-analysis/baseline-error-analysis/error-category-summary.csv` (SHA: `ce4d379074760192ef2eca5b8821a2a07c0471654ca52b33fd5a5f477c8b0f4b`)
- **Annotation Review Queue**: `docs/dataset-engineering/error-analysis/baseline-error-analysis/annotation-review-queue.csv` (SHA: `67785a231a315ac625495e448be01cfeca416b4c484cf8729131eb7757600608`)
- **Semantic Error Analysis Report**: `docs/dataset-engineering/error-analysis/baseline-error-analysis/development-oof-error-analysis.md` (SHA: `b8733bcd3eba87030e6dd52cb516e4a9e13e3f0680b1fe4c27f875bda4f634f5`)

## 3. Key Error Findings
- Total OOF Misclassifications: **70 / 800** (OOF Accuracy = 91.25%, Macro F1 = 0.9136).
- **Possible Annotation Issues**: **0 (0.00%)**. All gold labels strictly adhere to canonical intent semantics.
- **Multi-Intent & Surface Ambiguity**: 41 errors (58.6%) stem from compound multi-intent sentences (`CATEGORY_B`, 24.3%), surface lexical overlap (`CATEGORY_D`, 24.3%), and semantic overlap (`CATEGORY_A`, 18.6%).
- **Contextual Fragments**: 15 errors (21.4%) represent short slot-filling fragments (`CATEGORY_C`) evaluated without dialogue context.
- **Coverage Gaps**: Only 5 errors (7.1%) represent sparse colloquial or uncommon phrasings (`CATEGORY_E`).

## 4. Annotation Decision
- **ANNOTATION_CHANGE_REQUIRED**: **NO**
- *Finding*: Physical verification confirms that 0 out of 70 error rows contain incorrect ground-truth labels. The annotation review queue is empty (0 rows). Development 800 labels remain 100% verified.

## 5. Development Dataset Decision
- **DEVELOPMENT_DATASET_CHANGE_REQUIRED**: **NO**
- *Rationale*: With 0 annotation defects, adding or altering examples to fit these 70 specific OOF errors carries a severe risk of overfitting and sample distortion before the one-time locked Holdout evaluation. The current 800-example distribution is balanced, clean, and representative. Development 800 remains **FINAL LOCKED**.

## 6. NLU Pipeline Decision
- **NLU_PIPELINE_TUNING_REQUIRED**: **NO**
- *Rationale*: The current pipeline (ThaiTokenizer + dual CountVectorsFeaturizer + DIETClassifier with 100 epochs and constrained similarities) delivers strong, stable performance (0.9346 Macro Precision, 0.8957 Macro Recall, 0.9136 Macro F1). Adjusting featurizer n-grams or DIET parameters to eliminate lexical overlap would compromise generalization on core intents. The NLU configuration remains **FROZEN**.

## 7. Context / Form Limitation
- **FORM_RUNTIME_VERIFICATION_REQUIRED**: **YES**
- *Statement*: Rasa Forms (`build_pc_form`, `upgrade_pc_form`) provide a robust runtime dialogue mechanism capable of mitigating context-dependent slot-fragment errors (such as isolated numbers or usage keywords). However, dedicated Form execution test evidence is required during system testing before claiming complete runtime resolution.

## 8. Accepted Baseline Limitations
The following 6 failure modes are formally accepted as known model boundaries for the Baseline Stratified 5-Fold Cross-Validation:
1. **Semantic Boundary Overlap**: Natural ambiguity between prospective future upgrades (`inform_future_upgrade`) and immediate upgrade requests (`upgrade_pc`).
2. **Compound Multi-Intent Utterances**: Simultaneous expression of budget figures and build/upgrade desires in a single turn.
3. **Context-Dependent Slot Fragments**: Single-turn evaluation of isolated slot responses (e.g. '30,000', 'ปานกลาง', 'เผื่อ') without dialogue history.
4. **Lexical Keyword Dominance**: Prominent component names (e.g. 'CPU', 'RTX 3080', 'RAM') dominating bag-of-words / n-gram featurization.
5. **Colloquial Conversational Outliers**: Ultra-short opening/closing expressions with sparse lexical representation (e.g. 'ทักทาย', 'บาย').
6. **Inherent Generalization Limits**: Standard statistical boundary variance on subtle syntactic phrasings.

## 9. Separate Non-NLU System Work
The acceptance of the Baseline NLU does **not** bypass required system-level hardening prior to Final Configuration Freeze:
1. **Credential Security Refactoring**: Replace hardcoded tokens in `credentials.yml` with environment variable interpolation (`${LINE_CHANNEL_SECRET}`).
2. **Fallback Rule Wiring**: Wire `nlu_fallback` in `rules.yml` to gracefully catch out-of-scope utterances.
3. **Form Runtime Verification**: Implement automated test harness for `build_pc_form` and `upgrade_pc_form`.

*These items are separate system-level engineering tasks and do not alter or invalidate the locked Baseline CV results.*

## 10. Holdout Isolation
The Locked Holdout dataset (200 examples, SHA: `61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961`) was **NOT opened, parsed, evaluated, or referenced** in reaching this decision.

## 11. Final Decision

> **PRIMARY DECISION: ACCEPT CURRENT BASELINE NLU**
> - **DEVELOPMENT DATASET CHANGE REQUIRED: NO**
> - **NLU PIPELINE TUNING REQUIRED: NO**
> - **DEVELOPMENT 800 = FINAL LOCKED**
> - **BASELINE STRATIFIED 5-FOLD CV = FINAL LOCKED**
> - **READY TO PROCEED TO TARGETED NON-NLU MUST FIXES & FINAL CONFIGURATION FREEZE**
