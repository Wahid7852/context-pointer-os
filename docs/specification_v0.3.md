# Context Pointer OS Specification v0.3

長期稼働AIエージェント向けメモリ運用層 - **Advanced Speculative Distribution**

## 1. 目的

Context Pointer OS (CPOS) は、長期稼働するAIエージェントが大量の情報を直接コンテキストに詰め込まず、ポインタ参照によって必要な文脈だけを安全かつ動的に再構築するためのメモリ運用層である。

v0.3 では、情報の「信頼性（Trust）」に基づいた意思決定と、「仮想的な推論（Speculative Branching）」による安全な知識更新をサポートする。

---

## 2. コアアーキテクチャ

### 2.1 Context Pointer (v0.3 拡張)

記憶への参照情報を保持する軽量オブジェクト。

```json
{
  "pointer_id": "ptr_0001",
  "context_type": "project_memory",
  "status": "active | stale | archived | invalidated | deleted",
  "trust_score": 0.0 to 1.0,
  "sensitivity_level": "public | internal | private | restricted",
  "dependencies": ["ptr_ref_01"],
  "metadata": {
    "is_hypothesis": true
  }
}
```

---

## 3. 主要機能 (Advanced Features)

### 3.1 Retrieval Governance Layer (v0.2)
エージェントの権限と情報の機密レベル、および信頼度を照合し、プロンプトへの出力を動的に制御する。
* **Trust Filter**: 信頼スコアが閾値（`minimum_trust_score`）未満の情報を自動的に除外。
* **Sensitivity Masking**: ロールに応じた機密情報の自動レッドアクション（伏せ字化）。

### 3.2 Context Reconstructor (v0.2)
LLMに渡す文脈を最適化して再構成する。
* **Prioritization**: 信頼度と重要度が高い順に情報を並べ替え。
* **Conflict Detection**: 親子関係や矛盾する情報の同時ロードを検知し、警告を発する。
* **Source Attribution**: すべての情報に出典とステータスを付与。

### 3.3 Dependency Management (v0.2)
ポインタ間の依存関係を管理し、必要な背景知識を再帰的に自動ロードする。循環参照保護機能を備える。

### 3.4 Speculative Branching (v0.3)
「仮説」を安全に検証するための分岐機能。
* **FORK**: 既存の記憶から低信頼度のサンドボックスを作成。
* **COMMIT**: 検証成功した仮説を親に統合し、信頼スコアを向上させる。
* **ROLLBACK**: 失敗した仮説を痕跡を残さず破棄。

---

## 4. ライフサイクル管理

ポインタは時間の経過やアクセス頻度（Heat）に応じて自動的に状態が変化する。
* **Active**: 頻繁に使用され、信頼できる状態。
* **Stale**: しばらくアクセスがなく、再検証が推奨される状態。
* **Invalidated**: 誤情報やセキュリティリスクにより無効化された状態。

---

## 5. 命令セット (v0.3)

| 命令 | アクション | 用途 |
| :--- | :--- | :--- |
| **TRUST** | 信頼度更新 | 情報の検証結果を反映 |
| **INVALIDATE**| 無効化 | 古い・誤った情報の排除 |
| **POLICY** | ポリシー変更 | ガバナンス閾値の動的変更 |
| **EXCHANGE** | ポインタ交換 | エージェント間でのURI共有 |
| **FORK** | 分岐 | 仮説推論の開始 |
| **COMMIT** | 確定 | 検証済み情報の永続化 |
| **ROLLBACK** | 破棄 | 失敗した仮説の削除 |

---

## 6. 設計思想

CPOS は、AIエージェントに「巨大な記憶」を与えるのではなく、**「記憶を扱うためのメタ認知能力」** を与える。

**「どの記憶を、いつ、なぜ、どの信頼度で、どこまで使うか。」**

これをカーネルレベルで管理することで、AIの幻覚（Hallucination）を抑制し、長期にわたる安全な自律稼働を実現する。
