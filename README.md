# Context Pointer OS (CPOS) v1.0

> A Lightweight Virtual Memory Operating System for LLM Agents.

Context Pointer OS (CPOS) is a specialized "Cognitive Kernel" designed to manage the memory, state, and security of LLM-based agents. Instead of feeding an agent's entire history into the prompt, CPOS allows agents to manage their context through **Pointers**, just like a traditional OS manages RAM and Disk.

## 🚀 Key Features

- **Context Pointers (#ctx):** Refer to memory segments by ID. Load/Unload them dynamically to save tokens.
- **Cognitive RAM & Paging:** Automatic swapping of large contexts into "Summary Views" when token limits are reached.
- **NeuroState Integration:** Built-in registers for emotional and ethical state monitoring.
- **Instruction Tapes (AIT/EAP):** 4-character machine code (`m4l8`) and assembly-like language (`>MEM:LOAD #ctx4 !8`) for fast agent-to-kernel communication.
- **Hardened Security:** Role-Based Access Control (ROOT, USER, GUEST) and a physical Kernel Key for registry protection.
- **Speculative Branching:** Fork context timelines (#ctx4.a) to test hypotheses and merge them back to root.
- **Inter-Process Communication (IPC):** Secure messaging between different sub-agents.
- **Watchdog & IRQ:** Automated self-healing interrupts if system corruption is detected.

## 🏗️ Architecture

- **CPU:** LLM (Reasoning Engine)
- **RAM:** `ContextStore` (Active context injected into prompt)
- **Disk:** `StorageManager` (Persistent pointer-based memory)
- **BIOS:** `CognitiveBootloader` (Automatic system initialization)
- **Task Manager:** HTML Dashboard for real-time cognitive monitoring.

## 🛠️ Quick Start

### Installation

```bash
git clone https://github.com/yourusername/context-pointer-os.git
cd context-pointer-os
pip install pydantic
```

### Running the Demo

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python3 src/cpos/demo_v10.py
```

This will execute a full lifecycle demo: **Boot -> Multi-Agent Interaction -> Stress Test -> Panic Recovery -> Dashboard Generation.**

## 📟 Instruction Set (AIT)

The core machine code format is `D T A P`:
- **D (Domain):** `m`emory, `s`ecurity, `n`eurostate, `t`ask, `p`ersona
- **T (Target):** Context index (0-9, or last char of ID)
- **A (Action):** `l`oad, `u`nload, `w`rite, `b`ranch, `g`erge, `p`ost(send), `i`(ls), `x`(ps)
- **P (Priority):** 1 (Low) to 9 (IRQ/High)

Example: `m4l8` -> Memory / ctx4 / Load / Priority 8

## 📊 Dashboard

CPOS generates a visual Task Manager (`final_cpos_v10_report.html`) to show:
- Memory Map with **Access Heat** (Throttling indicators)
- Active RAM contents
- Full Audit Log with agent attribution

---

## 📜 License

MIT License - feel free to use it for your own cognitive architectures!
