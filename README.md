# Context Pointer OS (CPOS) v0.1: Research Demo

> **"LLM agents don't need bigger memory. They need a Cognitive Kernel."**

Context Pointer OS (CPOS) is a specialized memory management layer for long-running LLM agents. Instead of overfilling the context window with conversation history, CPOS introduces **Context Pointers** (#ctx) to dynamically mount, swap, and protect information, functioning like a virtual memory OS for artificial intelligence.

---

## 🚀 Quick Start (Demonstration)

To see the core foundation in action, run the Standard Distribution demo:

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python3 src/cpos/demo_v10.py
```

### Expected Output
```text
================================================
   CONTEXT POINTER OS v0.1 - Research Prototype
================================================
--- [BOOTLOADER] Starting Cognitive Sequence ---
[BOOT] Step 1: >MEM:LOAD #ctx7 !9  (NeuroState)
[BOOT] Step 2: >MEM:LOAD #ctx20 !9 (AI Persona)
--- [BOOTLOADER] Sequence Completed Successfully ---

[Scenario: Rapid access triggers Heat Management]
Final Identity Load Priority: 5 (Throttled by Kernel)

[Scenario: Injecting Corruption (Panic Mode Test)]
--- [WATCHDOG IRQ] NEUROSTATE CORRUPTION DETECTED (0.95) ---
--- [WATCHDOG] Forced Reset Initialized ---
NeuroState after Watchdog IRQ: corruption=0.0, calm=0.9
```

---

## 🧠 Core Architecture (v0.1 Implemented)

### 📂 Context Pointers (#ctx)
Pointers are lightweight references to memory. They allow the agent to keep its prompt clean while retaining the ability to "recall" specific data on demand via the Registry.

### 💾 Cognitive RAM & Paging
- **Active Contexts**: Only specific pointers occupy the LLM's immediate prompt.
- **Homeostasis**: The kernel automatically summarizes or swaps unused pointers to disk when context limits are reached.

### 🎭 NeuroState & Watchdog
Real-time monitoring of agent "stability" (Calm vs. Corruption). The **Kernel Watchdog** can trigger hardware-level interrupts (IRQ) to reset the agent if internal corruption scores exceed safety thresholds.

### 🔐 Protection Layer (ACL)
Role-based access control for memory pointers, preventing unauthorized access or tampering by sub-processes or guest agents.

---

## 🛠️ Instruction Sets

### AIT (Agent Instruction Tape)
A 4-char machine code optimized for token-efficient agent communication: `[Domain][ID][Action][Priority]`
- `m1l5` : Memory Context 1 Load Priority 5
- `n7w9` : Neurostate Context 7 Write Priority 9 (IRQ)

### EAP (Extended Assembly Protocol)
High-level assembly format for human interaction and advanced cognitive planning:
- `>MEM:LOAD #ctx1 !5`
- `>SEC:TRUST #ctx4 !9 | score=0.8`

---

## 📜 Documentation & Tests

- [Detailed Specification (SPEC.md)](docs/SPEC.md) - The foundational logic.
- [Project Wiki (docs/)](docs/) - Technical evolution and API details.

### ✅ Verification
The core integrity is verified via 31 unit tests:
```bash
/home/mayutama/context-pointer-os/.venv/bin/pytest tests/
# Result: 31 passed in 0.21s
```

---

## 🗺️ Roadmap (Future Concepts)

- **v0.2**: Governance Layer (Sensitivity-based redaction).
- **v0.3**: Speculative Branching (Hypothesis sandboxing).
- **v0.4**: Distributed Swarm (Inter-node pointer exchange).
- **v0.5**: Predictive Scheduling (Neural prefetching).

---
MIT License | Developed by **kagioneko**
