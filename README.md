# Context Pointer OS (CPOS) v1.0

> **LLM agents don’t need bigger memory. They need memory addresses.**

Context Pointer OS (CPOS) is a specialized "Cognitive Kernel" designed to manage the memory, state, and security of LLM-based agents. Instead of feeding an agent's entire history into the prompt, CPOS allows agents to manage their context through **Pointers**, treating context like traditional RAM and Disk.

## 🧠 Conceptual Mapping

CPOS maps standard OS components to cognitive architecture:

| OS Component | Cognitive Mapping |
| :--- | :--- |
| **LLM** | **CPU** (Reasoning Engine) |
| **CPOS** | **Kernel** (Process & Memory Manager) |
| **ContextStore** | **RAM** (Active context in prompt) |
| **StorageManager** | **Disk** (Persistent semantic memory) |
| **AIT/EAP** | **Instruction Bus** (Agent-to-Kernel link) |
| **NeuroState** | **Registers / Flags** (Emotional/Ethical state) |

## 🚀 Key Features

- **Context Pointers (#ctx):** Refer to memory segments by ID. Load/Unload them dynamically to save tokens.
- **Cognitive RAM & Paging:** Automatic swapping of large contexts into "Summary Views" when token limits are reached.
- **Speculative Branching:** Fork context timelines (#ctx4.hyp_a) to test hypotheses and merge them back to root.
- **Hardened Security:** Role-Based Access Control (ROOT, USER, GUEST) and automated memory redaction.
- **Watchdog & IRQ:** Automated self-healing interrupts if system corruption is detected.

## 🛠️ Quick Start

### Installation

```bash
git clone https://github.com/kagioneko/context-pointer-os.git
cd context-pointer-os
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

### Running the Demo

CPOS includes a full lifecycle demo showcasing boot, multi-agent interaction, and recovery.

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python3 src/cpos/demo_v10.py
```

**Expected Result:** A task manager dashboard `final_cpos_v10_report.html` is generated, showing the cognitive state.

## 📟 Instruction Set (AIT)

The core machine code format is `D T A P`:
- **D (Domain):** `m`emory, `s`ecurity, `n`eurostate, `t`ask, `p`ersona
- **T (Target):** Context index (0-9, or last char of ID)
- **A (Action):** `l`oad, `u`nload, `w`rite, `b`ranch, `g`erge, `p`ost(send), `i`(ls), `x`(ps)
- **P (Priority):** 1 (Low) to 9 (IRQ/High)

## 📜 License

MIT License
