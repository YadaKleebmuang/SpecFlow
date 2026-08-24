# Chapter 3 Facts Sheet — Methodology & System Development
## Source of Truth for Thesis Chapter 3

### 1. System Architecture
- **Framework**: Rasa Open Source 3.6.21 + Rasa SDK 3.6.2 (Python 3.9.6).
- **Data Flow**: `LINE User` → `LINE Messaging API` → `LineInput (app/rasa/line_channel.py)` → `Rasa Server (NLU Pipeline + Policies)` → `Rasa Action Server (port 5055, app/rasa/actions/actions.py)` → `SpecRecommender / UpgradeAdvisor (app/services/recommendation/)` → `hardware_db.json` → `Flex Message Builder (app/rasa/actions/flex.py)` → `Analytics DB (data/analytics.db)` → `LINE User`.

### 2. Final NLU Pipeline Configuration (`app/rasa/config.yml`)
1. `ThaiTokenizer` (PyThaiNLP `newmm` word segmentation engine).
2. `RegexFeaturizer`
3. `LexicalSyntacticFeaturizer`
4. `CountVectorsFeaturizer` (analyzer: `word`, min_ngram: 1, max_ngram: 1)
5. `CountVectorsFeaturizer` (analyzer: `char_wb`, min_ngram: 1, max_ngram: 4)
6. `DIETClassifier` (epochs: 100, constrain_similarities: True)
7. `EntitySynonymMapper`
8. `ResponseSelector` (epochs: 100, constrain_similarities: True)
9. `FallbackClassifier` (threshold: 0.3, ambiguity_threshold: 0.1)

### 3. Dialogue Policies Configuration (`app/rasa/config.yml`)
1. `MemoizationPolicy` (max_history: 5)
2. `RulePolicy` (core_fallback_threshold: 0.3, core_fallback_action_name: `action_default_fallback`)
3. `UnexpecTEDIntentPolicy` (max_history: 5, epochs: 100)
4. `TEDPolicy` (max_history: 5, epochs: 100, constrain_similarities: True)

### 4. Domain Definition (`app/rasa/domain.yml`)
- **Intents (15)**: `greet`, `goodbye`, `build_pc`, `upgrade_pc`, `inform_budget`, `inform_usage`, `inform_current_specs`, `ask_cpu_info`, `ask_gpu_info`, `ask_ram_info`, `ask_ssd_hdd_diff`, `optimize_performance`, `inform_future_upgrade`, `affirm`, `deny`.
- **Entities (4)**: `component_type`, `budget`, `usage`, `future_upgrade`.
- **Slots (4)**: `budget` (text), `usage` (text), `current_specs` (text), `future_upgrade` (bool).
- **Forms (2)**:
  - `build_pc_form`: slot filling order: `budget` → `usage` → `future_upgrade` → triggers `action_recommend_pc`.
  - `upgrade_pc_form`: slot filling order: `usage` → `current_specs` → triggers `action_recommend_upgrade`.

### 5. Custom Actions (`app/rasa/actions/actions.py`)
- `action_recommend_pc`: Executes `SpecRecommender`, builds Flex spec card, resets slots.
- `action_recommend_upgrade`: Executes `UpgradeAdvisor`, analyzes hardware bottlenecks, resets slots.
- `action_cpu_info`, `action_gpu_info`, `action_ram_info`, `action_ssd_hdd_diff`: FAQ informational actions.
- `action_optimize_performance`: Troubleshooting and OS optimization recommendations.

### 6. Hardware Catalog (`hardware_db.json`, SHA: `341659f6384ee83ebb803964c8c7a6bb06f249aa345a59b0ea540f16529245b4`)
- Total catalog: **64 records** (CPU: 14, GPU: 12, Motherboard: 10, RAM: 8, Storage: 5, PSU: 6, Case: 5, Cooler: 4).
- Compatibility rules: Socket matching (AM4, AM5, LGA1700), RAM generation (DDR4, DDR5), PSU sizing, form factor matching.

### 7. Security Architecture
- Secret storage: Loaded from environment variables (`${LINE_CHANNEL_SECRET}`, `${LINE_CHANNEL_ACCESS_TOKEN}`).
- Signature verification: HMAC-SHA256 implemented in `LineInput` via `linebot.WebhookParser`.
