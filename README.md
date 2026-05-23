# Context Pointer OS (CPOS) v1.0 (GA)

> **LLM agents don’t need bigger memory. They need memory addresses.**

Context Pointer OS (CPOS) is a specialized "Cognitive Kernel" designed to manage the memory, state, and security of long-running LLM agents. Instead of stuffing everything into the context window, CPOS uses **Context Pointers** to dynamically mount, swap, and protect information.

## 🚀 General Availability (v1.0) Key Features

- **🧠 Neural Memory**: AI-driven prefetching based on learned access patterns (v0.6).
- **🔒 Retrieval Governance**: Automatic redaction and trust-based filtering (v0.2).
- **🌐 Distributed Nodes**: Share pointers across network nodes with secure handshake (v0.4).
- **🔌 MCP Compliance**: Native support for **Model Context Protocol** (v1.0).
- **🧪 Speculative Branching**: Isolated hypothesis sandboxing with `FORK/COMMIT` (v0.3).
- **📊 Cognitive Dashboard**: Real-time terminal and visual monitoring of brain activity (v0.7).

## 📜 Documents

- [Context Pointer OS Specification v1.0](docs/specification_v1.0.md) - Official Final Specification.
- [Specification v0.1 (Legacy)](docs/specification_v0.1.md) - Original design document.

## 🧠 Conceptual Mapping

CPOS maps standard OS components to cognitive architecture:

- **LLM** = **CPU** (Reasoning Engine)
- **Context Window** = **L1 Cache / Registers**
- **Active Pointers** = **RAM**
- **External Pointers (MCP/Node)** = **Distributed Disk / Network**
- **Memory Policy** = **MMU / Homeostasis**
- **Scheduler** = **Instruction Dispatch / PID Isolation**

## 🛠️ Quick Start (Demonstrations)

Try the following scripts to see the cognitive kernel in action:

- `python3 src/cpos/demo_v40_mcp.py`: **MCP Compliance** & Universal Mounting.
- `python3 src/cpos/demo_v32_terminal.py`: **Real-time Monitoring** and Activity Heat.
- `python3 src/cpos/demo_v31_neural.py`: **Neural Prediction** and Pattern Learning.
- `python3 src/cpos/demo_v29_network_integrity.py`: **Distributed Integrity** in Ring Topology.
- `python3 src/cpos/demo_v26_speculative.py`: **Speculative Branching** (FORK/COMMIT).

## 📜 License

MIT License
