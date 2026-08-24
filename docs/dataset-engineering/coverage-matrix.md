# Coverage Matrix

| Intent | Count | Current Strength | Coverage Gap | Overrepresented Pattern | Boundary Need | Batch‑A Priority |
|--------|-------|------------------|--------------|------------------------|---------------|------------------|
| greet | 10 | HIGH | NONE | NONE | NO | LOW |
| goodbye | 11 | HIGH | NONE | NONE | NO | LOW |
| build_pc | 35 | HIGH | SOME (needs richer phrasing) | NONE | YES (budget‑usage combos) | HIGH |
| upgrade_pc | 23 | HIGH | NONE | NONE | NO | MEDIUM |
| inform_budget | 17 | MEDIUM | NONE | NONE | NO | MEDIUM |
| inform_usage | 25 | MEDIUM | NONE | NONE | NO | MEDIUM |
| inform_current_specs | 22 | MEDIUM | NONE | NONE | NO | MEDIUM |
| ask_cpu_info | 14 | HIGH | NONE | NONE | NO | LOW |
| ask_gpu_info | 14 | HIGH | NONE | NONE | NO | LOW |
| ask_ram_info | 14 | HIGH | NONE | NONE | NO | LOW |
| ask_ssd_hdd_diff | 14 | HIGH | NONE | NONE | NO | LOW |
| optimize_performance | 22 | MEDIUM | SOME (software‑tuning variants) | NONE | YES (software focus) | HIGH |
| inform_future_upgrade | 14 | MEDIUM | NONE | NONE | NO | MEDIUM |
| affirm | 7 | HIGH | NONE | NONE | NO | LOW |
| deny | 8 | HIGH | NONE | NONE | NO | LOW |

**Total Examples**: 250 (matches Clean Baseline).

*All intents meet minimum coverage; priority highlights where Batch A should focus.*
