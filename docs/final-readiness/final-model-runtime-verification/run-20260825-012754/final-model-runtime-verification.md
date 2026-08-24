# Final-Model Runtime Verification Report
## SpecFlow Conversational AI Runtime Verification (Run ID: `run-20260825-012754`)

## 1. Scope
This document records the empirical execution and physical verification of the **Final Model** (`20260825-001851-woolen-billet.tar.gz`) at runtime across dialogue forms, NLU fallback routing, and custom action execution prior to the locked Holdout evaluation.

## 2. Final Model Identity
- **Model Path**: `final_models/run-20260825-001846/20260825-001851-woolen-billet.tar.gz`
- **Model Size**: `43,774,326 bytes`
- **SHA-256**: `86a76534116c8298b39aaa8ddbaddc257d0fb8276da905da68675f7fdeff6dd7`
- **Load Verification**: **PASS** (Loaded in `12.08s`, status `is_ready=True`)

## 3. Runtime Environment
- **Python**: `3.9.6`
- **Rasa**: `3.6.21`
- **rasa-sdk**: `3.6.2`
- **PyThaiNLP**: `5.3.4`
- **Action Server Endpoint**: `http://127.0.0.1:5055/webhook`

## 4. Test Method
Deterministic, non-Holdout multi-turn interactive dialogue testing using the canonical Rasa Python Agent API connected to the live Rasa Action Server.

## 5. RT-02: build_pc_form Runtime Flow
- **Trigger Turn**: *"อยากจัดสเปคคอมพิวเตอร์เครื่องใหม่"* → Intent: `build_pc` (conf: 0.9997), `active_loop: build_pc_form`
- **Slot Progression**:
  - Slot `budget`: Provided *"35000"* → Set to `35000`
  - Slot `usage`: Provided *"ทำงานกราฟิก ตัดต่อวิดีโอ"* → Set to `ทำงานกราฟิก ตัดต่อวิดีโอ`
  - Slot `future_upgrade`: Provided *"ไม่ต้องการอัปเกรดในอนาคต"* → Set to `ไม่ต้องการอัปเกรดในอนาคต`
- **Completion**: `active_loop` set to `None`, triggered `action_recommend_pc`.
- **Status**: **PASS**

## 6. RT-03: upgrade_pc_form Runtime Flow
- **Trigger Turn**: *"อยากอัปเกรดคอมเครื่องเดิมให้แรงขึ้นครับ"* → Intent: `upgrade_pc` (conf: 0.9998), `active_loop: upgrade_pc_form`
- **Slot Progression**:
  - Slot `usage`: Provided *"เล่นเกมหนักๆ สตรีมมิ่ง"* → Set to `เล่นเกมหนักๆ สตรีมมิ่ง`
  - Slot `current_specs`: Provided *"ryzen 5 3600, ram 8gb, hdd 1tb, gtx 1050 ti"* → Set
- **Completion**: `active_loop` set to `None`, triggered `action_recommend_upgrade`.
- **Status**: **PASS**

## 7. RT-04 & RT-05: Fallback NLU & Dialogue
- **Out-of-Scope Test Messages**:
  1. *"พรุ่งนี้ฝนจะตกที่เชียงใหม่ไหมครับ"* (Weather) → Intent: `nlu_fallback` (conf: 0.2851)
  2. *"สอนวิธีทำต้มยำกุ้งน้ำข้นสูตรโบราณหน่อย"* (Recipe) → Intent: `nlu_fallback` (conf: 0.2910)
  3. *"ผลฟุตบอลพรีเมียร์ลีกล่าสุดเป็นอย่างไรบ้าง"* (Sports) → Intent: `nlu_fallback` (conf: 0.2895)
- **Dialogue Action**: Triggered `utter_fallback` via rule `Handle NLU fallback`.
- **Bot Response**: *"ขออภัยครับ ผมยังไม่เข้าใจข้อความนี้ รบกวนลองพิมพ์ใหม่อีกครั้ง หรือระบุว่าต้องการจัดสเปคคอม อัปเกรดคอม หรือสอบถามข้อมูลอุปกรณ์ได้เลยครับ"*
- **Status**: **PASS**

## 8. RT-06: Custom Action Server Integration
- **Action Server Status**: Reachable and functional on `http://127.0.0.1:5055/webhook`.
- **Actions Executed**: `action_recommend_pc`, `action_recommend_upgrade`.
- **Status**: **PASS**

## 9. RT-07 & RT-08: Recommendation & Upgrade Sanity
- **Build Recommendation**: Returned valid compatible hardware configuration matching budget and usage.
- **Upgrade Recommendation**: Returned valid bottleneck diagnostic and cost estimation.
- **Status**: **PASS**

## 10. Test Case Summary Table
| Case ID | Objective | Expected Behavior | Actual Behavior | Status |
| :--- | :--- | :--- | :--- | :---: |
| **RT-01** | Final Model Load | Model loads into Agent | Loaded in 12.08s (`is_ready=True`) | **PASS** |
| **RT-02** | `build_pc_form` flow | Slot progression & completion | 3 slots filled, `action_recommend_pc` run | **PASS** |
| **RT-03** | `upgrade_pc_form` flow | Slot progression & completion | 2 slots filled, `action_recommend_upgrade` run | **PASS** |
| **RT-04** | Fallback NLU activation | Out-of-scope triggers `nlu_fallback` | Emitted `nlu_fallback` (conf < 0.3) | **PASS** |
| **RT-05** | Fallback Dialogue handling | Executes `utter_fallback` | `utter_fallback` emitted with Thai message | **PASS** |
| **RT-06** | Custom Action Server | Action server handles requests | `action_recommend_pc` & `upgrade` executed | **PASS** |
| **RT-07** | Build Rec Sanity | Valid component specification | Valid compatible build returned | **PASS** |
| **RT-08** | Upgrade Rec Sanity | Valid upgrade advice | Valid upgrade bottleneck analysis returned | **PASS** |

## 11. Process Cleanup
- Temporary Action Server (PID: `10994`) cleanly terminated.
- Zero leftover background server processes.

## 12. Protected Artifact Integrity
- **Development 800 SHA**: `37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d` (PASS — Unchanged)
- **Baseline OOF SHA**: `b66e9e0eeda35ac7b45ac6b8ddcfaad0976cd770a38b7007428db0b73586cf47` (PASS — Unchanged)
- **Holdout 200 SHA**: `61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961` (PASS — Unchanged & Unevaluated)
- **Final Model SHA**: `86a76534116c8298b39aaa8ddbaddc257d0fb8276da905da68675f7fdeff6dd7` (PASS — Unchanged)

## 13. Holdout Isolation
- Holdout training usage: **0**
- Holdout inference usage: **0**
- Holdout metric computation: **0**
- Holdout evaluated: **NO**

## 14. Final Runtime Decision

> **FINAL-MODEL RUNTIME VERIFICATION PASSED**  
> **FINAL MODEL RUNTIME = LOCKED**  
> **AUTHORIZED FOR ONE-TIME LOCKED HOLDOUT 200 EVALUATION**
