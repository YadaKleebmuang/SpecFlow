# Entity Inventory

**Purpose**: Inventory all entity types used across the 250 clean utterances and their associated intents.

| Entity | Description | Associated Intents |
|--------|-------------|--------------------|
| `budget` | Monetary amount specifying the user's spending limit. Can appear as plain numbers, Thai words, or shorthand. | `build_pc`, `inform_budget` |
| `usage` | Descriptor of the primary purpose of the PC (gaming, video editing, office work, streaming, etc.). | `build_pc`, `inform_usage`, `upgrade_pc`, `optimize_performance` |
| `component_type` | Generic placeholder for hardware components (cpu, gpu, ram, ssd, hdd, etc.). Used to tag mentions of specific parts. | `inform_current_specs`, `upgrade_pc`, `ask_cpu_info`, `ask_gpu_info`, `ask_ram_info`, `ask_ssd_hdd_diff` |
| `future_upgrade` | Indicator of a prospective future hardware upgrade, often expressed as a wish or conditional phrase. | `inform_future_upgrade` |

*No other custom entities are present.*
