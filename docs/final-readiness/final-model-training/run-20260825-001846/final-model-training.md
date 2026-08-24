# Final Model Training Record
## SpecFlow Canonical Final Model (Run ID: `run-20260825-001846`)

## 1. Training Authorization
This training run represents the **single authorized Final Model training execution** for the SpecFlow project, authorized under the **Final Configuration Freeze** (`specflow_final_configuration_v1`).

## 2. Final Freeze Reference
- **Freeze Manifest**: `docs/final-readiness/final-configuration-freeze/final-configuration-freeze-manifest.json`
- **Freeze Manifest SHA-256**: `aaa9aaf7408032147995bd42c1f1ed822d26bc837e405c093727a0843769cc2c`

## 3. Runtime
- **Python**: `3.9.6`
- **Rasa**: `3.6.21`
- **rasa-sdk**: `3.6.2`
- **PyThaiNLP**: `5.3.4`

## 4. Development Dataset
- **Path**: `app/rasa/data/nlu.yml`
- **Training Examples**: **800** (100% of locked Development dataset)
- **Intents**: **15**
- **SHA-256**: `37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d`

## 5. Exact Training Inputs
- `app/rasa/config.yml` (`61349072d42b1529459c14452743e3f68b571167291efef90b58c5ef1f541ad0`)
- `app/rasa/domain.yml` (`c2a76780257345efc57dd32a8f261ac610745a4f21bad08bb308ad9b74717857`)
- `app/rasa/data/nlu.yml` (`37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d`)
- `app/rasa/data/rules.yml` (`37325e428ddcec108ff10cc3ec93b1d0e667c54f23d59c23f3c710ece7db22e5`)
- `app/rasa/data/stories.yml` (`45e869d2b571bec45926228cf9537d099b3d6002484a985a0bcf09913c492985`)

## 6. Training Command
```bash
PYTHONPATH="$(pwd)/app/rasa" .venv-rasa-cv/bin/rasa train --config app/rasa/config.yml --domain app/rasa/domain.yml --data app/rasa/data/nlu.yml app/rasa/data/rules.yml app/rasa/data/stories.yml --out final_models/run-20260825-001846
```

## 7. Training Execution
- **Start Timestamp**: `2026-08-25T00:18:46.889687+07:00`
- **End Timestamp**: `2026-08-25T01:18:41.553860+07:00`
- **Elapsed Duration**: `3594.66 seconds`
- **Exit Code**: `0` (Success)
- **Training Invocations**: `1`

## 8. Final Model Artifact
- **Path**: `final_models/run-20260825-001846/20260825-001851-woolen-billet.tar.gz`
- **Filename**: `20260825-001851-woolen-billet.tar.gz`
- **Size**: `43,774,326 bytes`
- **Modification Timestamp**: `2026-08-25T01:18:40.300901+07:00`
- **SHA-256**: `86a76534116c8298b39aaa8ddbaddc257d0fb8276da905da68675f7fdeff6dd7`
- **Archive Status**: Verified readable gzip-compressed tarball containing full DIET, Policy, and metadata graph components.

## 9. Hash / Provenance Linkage
- Exactly ONE new model archive was produced (`new_model_count = 1`).
- The newly-created artifact is uniquely identified via post-training set subtraction.

## 10. Protected Artifact Integrity
- **Development 800 SHA**: `37b05d1f44de9153321b86e9a7eae1984e21fb0b12bbfac01a4e895c66077b7d` (PASS — Unchanged)
- **Holdout 200 SHA**: `61d0c3c237d7dda727631ba3bc6a5343929045042dbb61945876fdd41ec7f961` (PASS — Unchanged & Unevaluated)
- **Baseline OOF SHA**: `b66e9e0eeda35ac7b45ac6b8ddcfaad0976cd770a38b7007428db0b73586cf47` (PASS — Unchanged)
- **Config SHA**: `61349072d42b1529459c14452743e3f68b571167291efef90b58c5ef1f541ad0` (PASS — Unchanged)

## 11. What Was NOT Evaluated
- **No Training-Set Overfitting Evaluation**: Training-set accuracy is not reported or used as performance evidence.
- **Holdout Evaluation**: The Locked Holdout dataset was **NOT** opened, evaluated, or used.

## 12. Next Required Step
1. Perform Final-Model Runtime Verification (Interactive Form dialogue test and Fallback confidence test).
2. Execute the ONE-TIME Locked Holdout 200 Final Evaluation.
