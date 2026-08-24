# Confusable Intent Matrix

**Purpose**: Identify pairs of intents that may be semantically ambiguous based on their primary communicative goals, without relying on specific lexical cues.

| Intent 1 | Intent 2 | Reason for Confusion | Mitigation Guidance |
|----------|----------|----------------------|----------------------|
| `greet` | `goodbye` | Both involve short salutation acts; tone can be similar. | Ensure examples include clear start‑of‑conversation vs end‑of‑conversation contexts. |
| `build_pc` | `upgrade_pc` | Both discuss hardware recommendations, but `build_pc` is a request for a complete new system, whereas `upgrade_pc` refers to modifications of existing hardware. | Use explicit statements of wanting a new build versus mentioning current specs or component upgrades. |
| `inform_budget` | `build_pc` | Budget numbers appear in both, but `inform_budget` is solely about stating a monetary limit, while `build_pc` combines budget with a full build request. | Treat an utterance as `build_pc` when it includes a request for a complete configuration, even if a budget is mentioned. |
| `inform_usage` | `build_pc` | Usage descriptors appear in both, yet `inform_usage` only informs the purpose, whereas `build_pc` pairs usage with a request for a build. | Prioritize `build_pc` when the utterance includes a request for a new configuration. |
| `inform_current_specs` | `upgrade_pc` | Both involve component mentions; `inform_current_specs` describes the existing setup, while `upgrade_pc` expresses intent to change components. | Include explicit references to “currently” versus “upgrade” in examples. |
| `optimize_performance` | `upgrade_pc` | Both may refer to improving hardware, but `optimize_performance` focuses on software or tuning tweaks without hardware change. | Ensure `optimize_performance` examples avoid mentions of new component purchases. |
| `affirm` | `deny` | Short yes/no responses can be ambiguous without context. | Keep these intents separate but note they rely on dialog state. |
| `ask_cpu_info` | `ask_gpu_info` | Both are slot‑filling questions about specific components. | Distinguish by the component keyword (`cpu` vs `gpu`). |
| `ask_gpu_info` | `ask_ram_info` | Both are component queries. | Use distinct component keywords. |
| `ask_ram_info` | `ask_ssd_hdd_diff` | Both are component queries. | Use distinct component keywords. |

**Usage**: Review this matrix when adding new examples or refining the model to ensure that potential overlaps are addressed with clear contextual cues or additional discriminative features.
