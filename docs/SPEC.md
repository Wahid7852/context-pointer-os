# Context Pointer OS Specification v0.1

長期稼働AIエージェント向けメモリ運用層

## 1. 概要 (Abstract)
Context Pointer OS (CPOS) は、LLMエージェントが長期的な文脈を効率的かつ安全に管理するための「認知カーネル」のプロトタイプである。
従来の「全履歴をプロンプトに詰め込む」アプローチに対し、CPOSは必要な文脈のみを動的にロード/アンロードする「仮想記憶（Context Pointers）」の概念を導入する。

---

## 2. 基本概念 (Core Concepts)

### 2.1 Context Pointers (#ctx)
記憶の実体ではなく、記憶への参照情報を保持する軽量オブジェクト。
- **ID**: 一意の識別子
- **Type**: データの種類（log, code, spec, neurostate等）
- **Trust Score**: 情報の信頼性 (0.0 - 1.0)
- **Status**: ライフサイクル状態 (active, stale, invalidated等)

### 2.2 Cognitive RAM & Paging
- **RAM (Active Contexts)**: 現在エージェントの意識（プロンプト）に展開されている記憶。
- **Paging/Swapping**: 優先度や容量制限に基づき、重要度の低い記憶を自動的に要約化またはディスクへ退避する。

### 2.3 NeuroState (精神状態)
エージェントの現在の「冷静さ（Calm）」や「汚染度（Corruption）」を数値化。
カーネルの `Watchdog` がこれを監視し、異常時には高優先度の割り込み（IRQ）を発生させて強制介入を行う。

---

## 3. 命令セット (Instruction Sets)

### 3.1 AIT (Agent Instruction Tape)
バイナリに近い 4文字固定の低級命令。
- 形式: `[Domain][TargetID][Action][Priority]`
- 例: `m1l5` (Memory ctx1 Load Priority 5)

### 3.2 EAP (Extended Assembly Protocol)
人間や高度なエージェントが読みやすいアセンブリ形式。
- 例: `>MEM:LOAD #ctx1 !5`

---

## 4. アーキテクチャ構成

1. **Context Registry**: 全てのポインタを管理する「メモリマップ」。
2. **Context Store**: 実際のデータロードとRAM管理を行う「メモリ管理ユニット（MMU）」。
3. **Scheduler**: 命令の優先度制御、プロセス隔離、ロック管理。
4. **ACL (Access Control List)**: ロールベースの権限管理（Protection Layer）。

---

## 5. 設計思想

CPOSは、AIに「巨大な記憶」を与えるのではない。
AIに **「どの記憶を、いつ、なぜ、どこまで使うか」という意思決定のメタ構造** を提供するものである。
