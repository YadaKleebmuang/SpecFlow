# Final Configuration Freeze Record
## SpecFlow Conversational AI System (Freeze ID: `specflow_final_configuration_v1`)

## 1. Freeze Scope
This document certifies the **authoritative Final Configuration Freeze** for the SpecFlow project.
All datasets, NLU pipelines, policy configurations, domain definitions, rules, custom action implementations, recommendation engines, hardware databases, preprocessing modules, and security configurations captured herein are **FINAL LOCKED**.

This frozen state constitutes the **sole authorized configuration** for training the canonical Final Rasa NLU/Dialogue Model on 100% of the locked Development 800 dataset.

## 2. Experimental Locks
- **Development 800**: `app/rasa/data/nlu.yml` (SHA: `37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d`) — **FINAL LOCKED**
- **Holdout 200**: `docs/dataset-engineering/holdout/locked-holdout-v1.yml` (SHA: `61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961`) — **LOCKED / UNEVALUATED**
- **Baseline Stratified 5-Fold CV**: `docs/dataset-engineering/cross-validation/baseline/results/oof-predictions.csv` (SHA: `b66e9e0eeda35ac7b45ac6b8ddcfaad0976cd770a38b7007428db0b73586cf47`) — **FINAL LOCKED**
- **Error Decision**: `docs/dataset-engineering/error-analysis/baseline-error-analysis/error-decision-record.json` — **ACCEPT BASELINE NLU (NO DATASET CHANGE, NO NLU TUNING)**

## 3. Final Runtime
- **Python**: `3.9.6`
- **Rasa**: `3.6.21`
- **rasa-sdk**: `3.6.2`
- **PyThaiNLP**: `5.3.4`
- **Environment**: `.venv-rasa-cv` with `PYTHONPATH="$(pwd)/app/rasa"`

## 4. Final Development Dataset
- **Path**: `app/rasa/data/nlu.yml`
- **Rows**: 800 training examples
- **Intents**: 15 canonical intents
- **SHA-256**: `37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d`

## 5. Final NLU Configuration
- **Path**: `app/rasa/config.yml`
- **SHA-256**: `61349072d42b1529459c14452743e3f68b571167291efef90b58c5ef1f541ad0`
- **NLU Pipeline**:
  1. `thai_tokenizer.ThaiTokenizer`
  2. `RegexFeaturizer`
  3. `LexicalSyntacticFeaturizer`
  4. `CountVectorsFeaturizer` (word-level)
  5. `CountVectorsFeaturizer` (char_wb, n-gram 1–4)
  6. `DIETClassifier` (100 epochs, constrain_similarities: true)
  7. `EntitySynonymMapper`
  8. `ResponseSelector` (100 epochs, constrain_similarities: true) *(Role: UNUSED_FOR_FAQ_RETRIEVAL)*
  9. `FallbackClassifier` (threshold: 0.3, ambiguity_threshold: 0.1)

## 6. Final Dialogue Configuration
- **Policies**:
  1. `MemoizationPolicy`
  2. `RulePolicy`
  3. `UnexpecTEDIntentPolicy` (max_history: 5, epochs: 100)
  4. `TEDPolicy` (max_history: 5, epochs: 100, constrain_similarities: true)
- **Rules Path**: `app/rasa/data/rules.yml` (SHA: `37325e428ddcec108ff10cc3ec93b1d0e667c54f23d59c23f3c710ece7db22e5`)
- **Stories Path**: `app/rasa/data/stories.yml` (SHA: `45e869d2b571bec45926228cf9537d099b3d6002484a985a0bcf09913c492985`)

## 7. Final Domain / Forms / Actions
- **Domain Path**: `app/rasa/domain.yml` (SHA: `c2a76780257345efc57dd32a8f261ac610745a4f21bad08bb308ad9b74717857`)
- **Intents (15)**: `greet`, `goodbye`, `build_pc`, `upgrade_pc`, `inform_budget`, `inform_usage`, `inform_current_specs`, `ask_cpu_info`, `ask_gpu_info`, `ask_ram_info`, `ask_ssd_hdd_diff`, `optimize_performance`, `inform_future_upgrade`, `affirm`, `deny`
- **Entities (4)**: `budget`, `usage`, `component_type`, `future_upgrade`
- **Slots (4)**: `budget`, `usage`, `current_specs`, `future_upgrade`
- **Forms (2)**: `build_pc_form` (required: budget, usage, future_upgrade), `upgrade_pc_form` (required: usage, current_specs)
- **Registered Actions (9)**: `action_recommend_pc`, `action_recommend_upgrade`, `action_greet`, `action_goodbye`, `action_faq`, `action_optimize_performance`, `action_ask_usage`, `action_ask_current_specs`, `action_ask_future_upgrade`
- **Responses (2)**: `utter_ask_budget`, `utter_fallback`

## 8. Recommendation & Compatibility Sources
- `app/rasa/actions/actions.py` (SHA: `4ec2276851bd74a1b0ce257479c1c4fe4cc04d32f6d0c586c6272801938b9acd`)
- `app/services/recommendation/spec_recommender.py` (SHA: `732fe38630ad63acbb2af5be26a3cbaad57efdb764e48e15686a40463e554968`)
- `app/services/recommendation/upgrade_advisor.py` (SHA: `5967e5a77a8849ad172fe83d78e8d019beaf068d69736a8f0f9df41ee46c15f1`)
- `app/rasa/actions/flex.py` (SHA: `4fd2f324a6c565aa9f59f9d9349668e4c23e1efb36c7865e412c93afeecce75e`)

## 9. Hardware Database
- **Path**: `app/services/recommendation/hardware_db.json`
- **SHA-256**: `341659f6384ee83ebb803964c8c7a6bb06f249aa345a59b0ea540f16529245b4`
- **Total Records**: 64 records across 8 categories (cpu: 14, gpu: 12, motherboard: 10, ram: 8, storage: 5, psu: 6, case: 5, cooler: 4)

## 10. Preprocessing & Connector
- `app/rasa/thai_tokenizer.py` (SHA: `5e08d295028634e1797afc8f703bb354babea7220235c2d387a7c1d50a06dde6`)
- `app/services/nlp/preprocessing.py` (SHA: `2ddb512a71faadcd52cade5603f136900bba06d0bab2a14937b524af2f857b41`)
- `app/services/nlp/typo_dict.json` (SHA: `b3efa3268e7a9b8be54b7f02531652f17e61a5975d65d1e765721a6a85b4fecb`, 44 typo mapping entries)
- `app/rasa/line_channel.py` (SHA: `d24ac03290d3c04bbab82500288e71955101dcae0aab81c8bfb46a2b0727da8d`)

## 11. LINE / Security Configuration
- `app/rasa/credentials.yml` (SHA: `c065d11a89bebb9beb4cf213eb82aba34ad156b3f01805fc942b0c93ea71945a`)
- Active literal secrets in tracked source: **0**
- Environment variable configuration: `LINE_CHANNEL_SECRET`, `LINE_CHANNEL_ACCESS_TOKEN`
- Git ignore patterns: `.env`, `.env.*`, `!.env.example`, `.specflow-recovery/`

## 12. Final Fallback Wiring
- `FallbackClassifier` threshold: `0.3`, ambiguity_threshold: `0.1`
- Mapping: `intent: nlu_fallback` → `action: utter_fallback`
- Static verification: **PASS**

## 13. Validation Results
- **Rasa CLI Validation**: `rasa data validate` → **Exit Code 0** (PASS)
- **Unit & Static Regression Tests**: **13/13 PASS** (`test_nlp_preprocessing.py`, `test_recommendation.py`, `test_fallback_wiring.py`)
- **ThaiTokenizer Smoke Test**: **PASS**

## 14. Deferred Final-Model Runtime Tests
- **Form Runtime Verification**: Verified statically; live interactive tracker verification deferred until Final Model is trained.
- **Fallback Runtime Inference**: Verified statically; live threshold trigger verification deferred until Final Model is trained.

## 15. External Credential Rotation Requirement
- **Credential Rotation Required**: **YES** (Due to previous historical Git commit tracking).
- **Status**: External manual action pending in LINE Developers Console prior to production use.

## 16. Frozen File Inventory
| File Path | Classification | Size | SHA-256 (Prefix) |
| :--- | :--- | :---: | :--- |
| `app/rasa/config.yml` | `TRAINING_INPUT` | 1,295 B | `61349072d42b1529...` |
| `app/rasa/domain.yml` | `TRAINING_INPUT` | 2,618 B | `c2a76780257345ef...` |
| `app/rasa/data/nlu.yml` | `TRAINING_INPUT` | 252,131 B | `37b05d1f44de9153...` |
| `app/rasa/data/rules.yml` | `TRAINING_INPUT` | 1,455 B | `37325e428ddcec10...` |
| `app/rasa/data/stories.yml` | `TRAINING_INPUT` | 92 B | `45e869d2b571bec4...` |
| `app/rasa/thai_tokenizer.py` | `NLU_RUNTIME_SOURCE` | 1,883 B | `5e08d295028634e1...` |
| `app/services/nlp/preprocessing.py` | `PREPROCESSING_SOURCE` | 4,393 B | `2ddb512a71faadcd...` |
| `app/services/nlp/typo_dict.json` | `PREPROCESSING_SOURCE` | 1,330 B | `b3efa3268e7a9b8b...` |
| `app/rasa/line_channel.py` | `LINE_CHANNEL_SOURCE` | 5,428 B | `d24ac03290d3c04b...` |
| `app/rasa/actions/actions.py` | `ACTION_SOURCE` | 26,527 B | `4ec2276851bd74a1...` |
| `app/services/recommendation/spec_recommender.py` | `RECOMMENDATION_SOURCE` | 12,996 B | `732fe38630ad63ac...` |
| `app/services/recommendation/upgrade_advisor.py` | `RECOMMENDATION_SOURCE` | 10,422 B | `5967e5a77a8849ad...` |
| `app/rasa/actions/flex.py` | `ACTION_SOURCE` | 7,074 B | `4fd2f324a6c565aa...` |
| `app/services/recommendation/hardware_db.json` | `HARDWARE_DATA` | 10,885 B | `341659f6384ee83e...` |
| `app/rasa/credentials.yml` | `SECURITY_CONFIG` | 228 B | `c065d11a89bebb9b...` |
| `app/rasa/endpoints.yml` | `SECURITY_CONFIG` | 57 B | `86ff2cecaae39f2d...` |
| `.env.example` | `SECURITY_CONFIG` | 211 B | `052fdadc2a6e641d...` |
| `.gitignore` | `SECURITY_CONFIG` | 1,289 B | `5d691af74ebac702...` |


## 17. Authorization for Final Model Training
- **Final Training Ready**: **TRUE**
- **Authorization**: The above exact physical configuration is formally approved and authorized for ONE canonical Final Model Training run on 100% of Development 800 (`app/rasa/data/nlu.yml`).
- **Holdout Isolation**: The 200-example Holdout dataset remains completely locked, isolated, and unevaluated.
