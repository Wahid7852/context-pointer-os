# Context Pointer OS (CPOS) v0.1

> **"LLM agents don’t need bigger memory. They need memory addresses."**

Context Pointer OS (CPOS) is a specialized **Cognitive Kernel** designed to manage memory, state, and security for long-running LLM agents. Instead of stuffing every conversation history into the prompt, CPOS uses **Context Pointers** to dynamically mount, swap, and protect information.

---

## 🧠 Core Concepts

### 📂 Context Pointers (#ctx)
Pointers are lightweight references to memory. They allow the agent to keep its prompt clean while having the ability to "recall" specific data on demand.

### 💾 Cognitive RAM & Paging
- **Active RAM**: Only loaded pointers occupy the LLM's immediate context.
- **Homeostasis**: The kernel automatically summarizes or swaps old/unused pointers to disk when RAM is full.

### 🎭 NeuroState
Real-time monitoring of agent "health" (Calm vs. Corruption). The **Kernel Watchdog** can trigger hardware-level interrupts (IRQ) to reset the agent if it becomes unstable.

---

## 🛠️ Instruction Sets

### AIT (Agent Instruction Tape)
A 4-char machine code for agents: `[Domain][ID][Action][Priority]`
- `m1l5` : Memory Context 1 Load Priority 5
- `n7w9` : Neurostate Context 7 Write Priority 9 (IRQ)

### EAP (Extended Assembly Protocol)
High-level assembly for human/advanced logic:
- `>MEM:LOAD #ctx1 !5`
- `>SEC:TRUST #ctx4 !9 | score=0.8`

---

## 🚀 Execution Demo (v0.1)

```text
================================================
   CONTEXT POINTER OS v0.1 - Research Prototype
================================================
--- [BOOTLOADER] Starting Cognitive Sequence (4 steps) ---
[BOOT] Step 1: >MEM:LOAD #ctx7 !9  (NeuroState)
[BOOT] Step 2: >MEM:LOAD #ctx20 !9 (AI Persona)
--- [BOOTLOADER] Sequence Completed Successfully ---

[Scenario: Rapid access triggers Heat Management]
Final Identity Load Priority: 5 (Throttled by Kernel)

[Scenario: Injecting Corruption (Panic Mode Test)]
--- [WATCHDOG IRQ] NEUROSTATE CORRUPTION DETECTED (0.95) ---
--- [WATCHDOG] Forced Reset Initialized ---
NeuroState after Watchdog IRQ: corruption=0.0, calm=0.9

[COMPLETE] CPOS v0.1 Core Foundation is stable.
```

---

## 📜 Documentation

- [Detailed Specification (SPEC.md)](docs/SPEC.md) - The foundational logic of Context Pointer OS.

## ✅ Implementation Status

- [x] Context Registry (Memory Map)
- [x] Context Store (Cognitive RAM/MMU)
- [x] Scheduler (Priority/Lock/Isolation)
- [x] AIT/EAP Parsers (Instruction Set)
- [x] Watchdog & IRQ (Stability)
- [x] Cognitive Dashboard (Observability)

---
MIT License | Developed by **kagioneko**
