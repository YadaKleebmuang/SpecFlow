# System / End-to-End Evidence Report
## SpecFlow Conversational PC Hardware Advisor (Evidence ID: `specflow_system_e2e_evidence_v1`)

## 1. Scope
This document consolidates the **final read-only physical system verification** of the SpecFlow conversational assistant post-Holdout evaluation.

## 2. Final System Identity
- **Final Model**: `final_models/run-20260825-001846/20260825-001851-woolen-billet.tar.gz` (SHA: `86a76534116c8298b39aaa8ddbaddc257d0fb8276da905da68675f7fdeff6dd7`)
- **Holdout Status**: `FINAL EVALUATED / CLOSED` (SHA: `61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961`)

## 3. Runtime Environment
- **Python**: `3.9.6`
- **Rasa**: `3.6.21`
- **Rasa SDK**: `3.6.2`
- **PyThaiNLP**: `5.3.4`

## 4. Physical Architecture & Data Flow
`User / LINE App` → `LINE Messaging API` → `LineInput Webhook (app/rasa/line_channel.py)` → `Rasa Server (NLU Pipeline + Policies)` → `Rasa Action Server (app/rasa/actions/actions.py)` → `RecommendationEngine (app/services/recommendation/recommender.py)` → `hardware_db.json` → `Flex Message Builder (flex_builder.py)` → `Analytics DB (data/analytics.db)` → `User Response`

## 5. Component Inventory
- **Intents**: 15 defined in `domain.yml`
- **Entities**: 4 (`component_type`, `budget`, `usage`, `future_upgrade`)
- **Slots**: 4 (`budget`, `usage`, `current_specs`, `future_upgrade`)
- **Forms**: 2 (`build_pc_form`, `upgrade_pc_form`)
- **Hardware Catalog**: 64 records across 8 component categories in `hardware_db.json` (SHA: `341659f6384ee83ebb803964c8c7a6bb06f249aa345a59b0ea540f16529245b4`)
- **Analytics DB**: SQLite `user_searches` table storing structured metrics only.

## 6. Functional Test Results (16 / 16 PASS)
| Case ID | Objective | Expected | Actual | Status |
| :--- | :--- | :--- | :--- | :---: |
| `SYS-01` | Final Model load into Rasa Agent runtime | is_ready == True | Loaded successfully in 11.73s | **PASS** |
| `SYS-02` | Rasa Agent message processing engine | Operational inference pipeline | Agent successfully processed NLU & dialogue actions | **PASS** |
| `SYS-03` | Rasa SDK Action Server webhook reachability | HTTP 200 response on health check | Action Server responded on webhook endpoint | **PASS** |
| `SYS-04` | build_pc_form multi-turn slot filling & recommendation | Complete form & emit action_recommend_pc response | Form completed and returned 35k hardware build | **PASS** |
| `SYS-05` | upgrade_pc_form slot filling & upgrade analysis | Complete form & emit action_recommend_upgrade response | Form completed and returned upgrade component advice | **PASS** |
| `SYS-06` | Information intent 'ask_cpu_info' execution | Trigger action_cpu_info with factual explanation | Emitted response containing keyword 'CPU' | **PASS** |
| `SYS-07` | Information intent 'ask_gpu_info' execution | Trigger action_gpu_info with factual explanation | Emitted response containing keyword 'การ์ดจอ' | **PASS** |
| `SYS-08` | Information intent 'ask_ram_info' execution | Trigger action_ram_info with factual explanation | Emitted response containing keyword 'RAM' | **PASS** |
| `SYS-09` | Information intent 'ask_ssd_hdd_diff' execution | Trigger action_ssd_hdd_diff with factual explanation | Emitted response containing keyword 'SSD' | **PASS** |
| `SYS-10` | Information intent 'optimize_performance' execution | Trigger action_optimize_performance with factual explanation | Emitted response containing keyword 'ปรับแต่ง' | **PASS** |
| `SYS-11` | Out-of-scope fallback routing to utter_fallback | FallbackClassifier (threshold=0.3) -> utter_fallback | Emitted friendly fallback guidance in Thai | **PASS** |
| `SYS-12` | Hardware compatibility engine constraints | Compatible hardware bundle (Socket, RAM type, PSU wattage) | Build: AMD Ryzen 5 7600 + ASRock A620M-HDV/M.2 (Total: 32090 THB) | **PASS** |
| `SYS-13` | LINE Webhook signature verification mechanism | WebhookParser attached with HMAC-SHA256 signature verification & InvalidSignatureError handling | LineInput implementation defines WebhookParser and signature verification | **PASS** |
| `SYS-14` | LINE Credentials environment variable loading safety | 0 tracked literal tokens, uses ${LINE_CHANNEL_SECRET} | Interpolates credentials from environment variables | **PASS** |
| `SYS-15` | LINE Flex Message JSON bubble layout construction | Valid LINE Flex Carousel / Bubble JSON structure | Constructed Flex Message (type='flex', keys=['type', 'altText', 'contents']) | **PASS** |
| `SYS-16` | Analytics database schema & non-sensitive storage scope | user_searches table with aggregate metric columns only | Schema: ['id', 'timestamp', 'user_id', 'usage_type', 'budget_requested', 'allocated_total_price'] | **PASS** |


## 7. Security Evidence
- **Tracked Active Secrets**: `0`
- **Credential Sourcing**: Environment variables (`LINE_CHANNEL_SECRET`, `LINE_CHANNEL_ACCESS_TOKEN`)
- **Signature Validation**: HMAC-SHA256 via `linebot.WebhookHandler`
- **Production Status**: `PRODUCTION SECURITY ACTION OUTSTANDING` (Requires external credential rotation in LINE Developers Console prior to deployment).

## 8. E2E Verification Level
> **CLASSIFICATION: BACKEND E2E VERIFIED, LIVE LINE NOT VERIFIED**  
> Complete multi-turn form execution, recommendation algorithms, database lookup, flex message serialization, fallback handling, and mock LINE webhook channel are verified operational in the local runtime environment. Live webhook invocation from external LINE servers was not performed during offline evidence freezing.

## 9. Post-Holdout Immutability
- **Training Executed**: NO
- **Holdout Re-evaluated**: NO
- **Model / Data / Config Mutated**: NO
