# Intent Contract

This document defines the **primary communicative goal** for each intent in the SpecFlow chatbot. It is used as the reference for content review and future data generation.

---

## greet
**System Purpose**: Initiate friendly interaction.
**Primary Communicative Goal**: User wants to start a conversation or greet the bot.
**Typical Context**: Stand‑alone greeting, start of session, after bot says goodbye.
**Include**: Simple salutations, informal greetings, polite greetings.
**Exclude**: Questions, requests, or statements that contain intent beyond greeting.
**Entity Relationship**: None.
**Context Dependency**: LOW.
**Confusable Intents**: goodbye, affirm, deny.

---

## goodbye
**System Purpose**: End the conversation.
**Primary Communicative Goal**: User wishes to terminate the chat.
**Typical Context**: After a task is completed, user says farewell.
**Include**: Farewell phrases, polite goodbyes.
**Exclude**: Any request for information or clarification.
**Entity Relationship**: None.
**Context Dependency**: LOW.
**Confusable Intents**: greet, affirm, deny.

---

## build_pc
**System Purpose**: Provide a complete PC configuration recommendation.
**Primary Communicative Goal**: User asks the bot to recommend a full PC build.
**Typical Context**: Initial request, may include optional budget and/or usage information.
**Include**: Requests for a new PC, "จัดสเปคคอม", "แนะนำสเปคคอม".
**Exclude**: Requests to modify an existing PC (upgrade) or only to discuss a single component.
**Entity Relationship**:
- `budget` – OPTIONAL (may be present, absent, or partial).
- `usage` – OPTIONAL.
**Context Dependency**: MEDIUM – may be preceded by clarification questions.
**Confusable Intents**: upgrade_pc, inform_budget, inform_usage.

---

## upgrade_pc
**System Purpose**: Suggest modifications or replacements for components of an existing PC.
**Primary Communicative Goal**: User wants to upgrade/add/replace hardware in a current system.
**Typical Context**: After user has reported current specs, or explicitly mentions "อัปเกรด".
**Include**: Phrases like "อัปเกรดคอม", "เปลี่ยน CPU", "เพิ่ม RAM".
**Exclude**: Full‑build requests (build_pc) or pure performance tuning without hardware change.
**Entity Relationship**:
- `component_type` – REQUIRED_BY_SYSTEM (identifies which part to change).
- `budget` – OPTIONAL.
- `usage` – OPTIONAL.
**Context Dependency**: MEDIUM.
**Confusable Intents**: build_pc, optimize_performance.

---

## inform_budget
**System Purpose**: Capture or update the user's budget amount.
**Primary Communicative Goal**: User provides a monetary value for the PC budget.
**Typical Context**: Stand‑alone budget statement, or as part of a larger request.
**Include**: Any utterance where the main act is to state a budget, regardless of accompanying intent.
**Exclude**: Utterances where budget is mentioned only as supporting information for another primary intent (e.g., build_pc).
**Entity Relationship**: `budget` – OPTIONAL (may appear without being the primary intent).
**Context Dependency**: LOW to MEDIUM.
**Confusable Intents**: build_pc, upgrade_pc.

---

## inform_usage
**System Purpose**: Capture or update the intended usage/purpose of the PC.
**Primary Communicative Goal**: User describes what they will use the PC for (gaming, video editing, etc.).
**Typical Context**: Stand‑alone usage description or as part of a build/upgrade request.
**Include**: Any utterance where the core act is to state usage.
**Exclude**: Utterances where usage is merely supporting a build_pc request.
**Entity Relationship**: `usage` – OPTIONAL.
**Context Dependency**: LOW to MEDIUM.
**Confusable Intents**: build_pc, upgrade_pc.

---

## inform_current_specs
**System Purpose**: Record the user's current PC specifications.
**Primary Communicative Goal**: User lists existing hardware components.
**Typical Context**: Pre‑upgrade conversation, after the bot asks for current specs.
**Include**: Statements enumerating CPU, GPU, RAM, storage, etc.
**Exclude**: General statements about components without specifying the user’s current setup.
**Entity Relationship**: `component_type` – REQUIRED_BY_SYSTEM (identifies which component is being described).
**Context Dependency**: HIGH – usually follows a prompt from the bot.
**Confusable Intents**: upgrade_pc.

---

## ask_cpu_info
**System Purpose**: Capture the user's request for CPU information.
**Primary Communicative Goal**: User asks about CPU preferences, requirements, or details.
**Typical Context**: User initiates a query about CPU during a conversation about PC specs.
**Include**: User‑initiated questions such as "CPU ต้องการอะไรบ้าง?" or "ต้องการ CPU แบบไหน?".
**Exclude**: Bot‑initiated prompts.
**Entity Relationship**: None.
**Context Dependency**: HIGH (may be part of a slot‑filling dialogue).
**Confusable Intents**: ask_gpu_info, ask_ram_info.

---

## ask_gpu_info
**System Purpose**: Capture the user's request for GPU information.
**Primary Communicative Goal**: User asks about GPU preferences, requirements, or details.
**Typical Context**: User initiates a query about GPU during discussion of PC specs.
**Include**: User‑initiated questions such as "GPU ต้องการอะไรบ้าง?" or "ต้องการ GPU แบบไหน?".
**Exclude**: Bot‑initiated prompts.
**Entity Relationship**: None.
**Context Dependency**: HIGH (may be part of a slot‑filling dialogue).
**Confusable Intents**: ask_cpu_info, ask_ram_info.

---

## ask_ram_info
**System Purpose**: Capture the user's request for RAM information.
**Primary Communicative Goal**: User asks about RAM preferences, requirements, or details.
**Typical Context**: User initiates a query about RAM during discussion of PC specs.
**Include**: User‑initiated questions such as "RAM ต้องการอะไรบ้าง?" or "ต้องการ RAM แบบไหน?".
**Exclude**: Bot‑initiated prompts.
**Entity Relationship**: None.
**Context Dependency**: HIGH (may be part of a slot‑filling dialogue).
**Confusable Intents**: ask_cpu_info, ask_gpu_info.

---

## ask_ssd_hdd_diff
**System Purpose**: Capture the user's request regarding storage preferences.
**Primary Communicative Goal**: User asks whether they prefer SSD, HDD, or a combination.
**Typical Context**: User initiates a storage preference query during a component discussion.
**Include**: User‑initiated questions such as "ต้องการ SSD หรือ HDD?" or "อยากใช้เก็บข้อมูลแบบไหน?".
**Exclude**: Bot‑initiated prompts.
**Entity Relationship**: None.
**Context Dependency**: HIGH (may be part of a slot‑filling dialogue).
**Confusable Intents**: ask_cpu_info, ask_gpu_info.

---

## optimize_performance
**System Purpose**: Provide performance‑tuning advice without full hardware replacement.
**Primary Communicative Goal**: User seeks to improve speed, stability, or benchmarks of the current PC.
**Typical Context**: May follow an inform_current_specs or upgrade_pc request.
**Include**: Requests for tuning, overclocking, software tweaks, or minor hardware tweaks aimed at performance.
**Exclude**: Full‑system replacement requests (build_pc) or explicit component upgrades.
**Entity Relationship**: May reference `component_type` (e.g., "GPU performance"), but not required.
**Context Dependency**: MEDIUM.
**Confusable Intents**: upgrade_pc.

---

## inform_future_upgrade
**System Purpose**: Capture user’s plans for future upgrades.
**Primary Communicative Goal**: User mentions upcoming upgrade intentions.
**Typical Context**: After a build/upgrade discussion, user says what they might upgrade later.
**Include**: Statements about future hardware changes.
**Exclude**: Immediate upgrade requests.
**Entity Relationship**: `future_upgrade` – OPTIONAL.
**Context Dependency**: LOW to MEDIUM.
**Confusable Intents**: upgrade_pc.

---

## affirm
**System Purpose**: Confirm a previous bot question or statement.
**Primary Communicative Goal**: User signals agreement or acknowledgment.
**Typical Context**: Response to a yes/no question.
**Include**: Short confirmations ("ใช่", "ได้", "เอา").
**Exclude**: Statements that convey new information.
**Entity Relationship**: None.
**Context Dependency**: HIGH – meaning depends on preceding question.
**Confusable Intents**: deny (when negative), but also sometimes overlap with other intents if context is unclear.

---

## deny
**System Purpose**: Negate or reject a previous bot question or statement.
**Primary Communicative Goal**: User signals disagreement or rejection.
**Typical Context**: Response to a yes/no question.
**Include**: Short negatives ("ไม่", "ไม่ได้", "ไม่เอา").
**Exclude**: New informational statements.
**Entity Relationship**: None.
**Context Dependency**: HIGH.
**Confusable Intents**: affirm.

---

*End of Intent Contract.*
