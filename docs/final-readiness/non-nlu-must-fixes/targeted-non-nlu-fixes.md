# Targeted Non-NLU MUST Fixes Report
## Security Remediation and Fallback Rule Wiring

## 1. Scope
This document provides physical engineering evidence for the two targeted non-NLU MUST fixes identified during the Final System Evidence Inventory and the Error Decision Gate:
1. **Security Remediation**: Elimination of literal LINE credentials from tracked source files and migration to secure environment-variable interpolation.
2. **Fallback Wiring**: Physical wiring of the existing `FallbackClassifier` (`threshold: 0.3`, `ambiguity_threshold: 0.1`) to `nlu_fallback` and response `utter_fallback`.

No NLU training data (`nlu.yml`) or NLU pipeline parameters (`config.yml`) were modified.

## 2. Pre-Fix Findings
- **Security Defect**: `app/rasa/credentials.yml` previously contained literal `channel_secret` and `channel_access_token` values in tracked Git source.
- **Fallback Defect**: `config.yml` contained `FallbackClassifier`, but `rules.yml` and `domain.yml` lacked a rule and response definition for `nlu_fallback`.

## 3. Security Change
- **Credentials Configuration**: Refactored `app/rasa/credentials.yml` to use `${LINE_CHANNEL_SECRET}` and `${LINE_CHANNEL_ACCESS_TOKEN}`.
- **Connector Implementation**: Enhanced `LineInput.from_credentials()` and `__init__()` in `app/rasa/line_channel.py` to seamlessly read from environment variables `LINE_CHANNEL_SECRET` and `LINE_CHANNEL_ACCESS_TOKEN`.
- **Environment Template**: Created `.env.example` containing empty key definitions (`LINE_CHANNEL_SECRET=`, `LINE_CHANNEL_ACCESS_TOKEN=`).
- **Git Protection**: Updated `.gitignore` to explicitly ignore `.env`, `.env.*` (while keeping `!.env.example`), and untracked recovery directories.
- **Worktree Secret Scan**: Confirmed **0** active literal secrets in tracked working-tree source files.

## 4. Fallback Change
- **Domain Response**: Added `utter_fallback` under `responses` in `app/rasa/domain.yml` with a concise, helpful Thai message inviting the user to rephrase or select supported PC-related actions.
- **Rule Wiring**: Added rule `Handle NLU fallback` in `app/rasa/data/rules.yml` mapping `intent: nlu_fallback` to `action: utter_fallback`.
- **Pipeline Preservation**: `FallbackClassifier` parameters in `app/rasa/config.yml` remain strictly locked at `threshold: 0.3` and `ambiguity_threshold: 0.1`.

## 5. Validation Performed
- **YAML Validation**: Verified syntax and schema across `credentials.yml`, `domain.yml`, `rules.yml`, and `config.yml`.
- **Rasa CLI Validation**: Ran `rasa data validate` via canonical runtime (`.venv-rasa-cv/bin/rasa`). Result: **Exit Code 0** (No structural conflicts).
- **Targeted Static Regression Test**: Created `tests/test_fallback_wiring.py` (4 test methods) verifying fallback classifier presence, threshold values, domain fallback response, rule wiring, and environment variable interpolation. Result: **4/4 PASS**.
- **Full Test Suite**: Executed all unit tests (`python -m unittest discover -s tests`). Result: **13/13 PASS**.

## 6. Protected Artifact Integrity
- **Development 800 SHA**: `37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d` (PASS — Unchanged)
- **Baseline OOF SHA**: `b66e9e0eeda35ac7b45ac6b8ddcfaad0976cd770a38b7007428db0b73586cf47` (PASS — Unchanged)
- **Holdout 200 SHA**: `61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961` (PASS — Unchanged & Unevaluated)
- **NLU Config SHA**: `61349072d42b1529459c14452743e3f68b571167291efef90b58c5ef1f541ad0` (PASS — Unchanged)

## 7. Credential Rotation Requirement
Because `credentials.yml` was committed in previous historical Git commits:
> **IMPORTANT SECURITY NOTICE**: The previously exposed LINE Channel Secret and Channel Access Token MUST be rotated/revoked in the LINE Developers Console prior to any production deployment.

- **LINE Credential Rotation Required**: **YES**
- **Rotation Completed**: **UNKNOWN (External Manual Action Required)**

## 8. Deferred Runtime Tests
- **Fallback Runtime Inference**: `fallback_runtime_inference_verified = false` (Deferred until Final Model is trained).
- **Form Runtime Verification**: `build_pc_form` & `upgrade_pc_form` implementations are present and verified statically; live dialogue execution test deferred until Final Model is trained.

## 9. Remaining Work
- Final Configuration Freeze Manifest generation.
- Training canonical Final Model on 100% of Development 800.
- One-time Locked Holdout 200 evaluation.
