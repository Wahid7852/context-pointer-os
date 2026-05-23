# Context Pointer OS Specification v0.1

長期稼働AIエージェント向けメモリ運用層

## 1. 目的

Context Pointer OS は、長期稼働するAIエージェントが大量の履歴・記憶・ログ・知識を直接コンテキストに詰め込まず、ポインタ参照によって必要な文脈だけを取得・再構築するためのメモリ運用層である。

目的は「無限に覚えること」ではない。

目的は、

**必要な時に、必要な記憶だけを、安全に再構築すること。**

---

## 2. 基本概念

### 2.1 Context Pointer

Context Pointer は、記憶そのものではなく、記憶への参照情報を保持する軽量オブジェクトである。

```json
{
  "pointer_id": "ptr_0001",
  "context_type": "project_memory",
  "summary": "Context Pointer OS の初期設計メモ",
  "source": "github_repo",
  "location": "docs/spec.md",
  "priority": 0.82,
  "trust_score": 0.91,
  "created_at": "2026-05-24T00:00:00Z",
  "last_accessed": null,
  "expiration": null,
  "status": "active"
}
```

---

## 3. システム構成

```text
User / Agent Input
        ↓
Context Router
        ↓
Pointer Manager
        ↓
Retrieval Governance Layer
        ↓
External Context Store
        ↓
Context Reconstructor
        ↓
LLM / Agent
```

---

## 4. 主要コンポーネント

### 4.1 Pointer Manager

ポインタの作成・更新・削除・状態管理を担当する。

**役割**
* pointer作成
* pointer更新
* pointer失効
* pointer検索
* pointer依存関係管理
* lifecycle管理

### 4.2 Context Router

入力内容に応じて、どのポインタを参照すべきか判断する。

**判断材料**
* ユーザー入力
* 現在タスク
* agent role
* context_type
* priority
* trust_score
* sensitivity_level

### 4.3 External Context Store

実体データを保存する外部記憶領域。

**保存対象**
* 会話ログ
* コード
* 仕様書
* 実験ログ
* セキュリティログ
* ユーザー設定
* 長期記憶
* 一時タスク記憶

### 4.4 Context Reconstructor

取得した断片情報を、LLMが利用しやすい文脈に再構築する。

**処理**
* 要約
* 圧縮
* 関連情報の結合
* 古い情報の除外
* trust_scoreによる優先順位付け
* 出典付き文脈生成

### 4.5 Retrieval Governance Layer

記憶取得を制御・監査する層。

**役割**
* アクセス制御
* 機密情報制御
* 検索深度制限
* human approval判定
* 監査ログ記録
* prompt injection対策

---

## 5. Pointer Lifecycle

### 5.1 状態

* **active**: 使用可能
* **stale**: 古いが参照可能
* **archived**: 通常検索対象外
* **invalidated**: 無効化済み
* **deleted**: 削除済み

### 5.2 状態遷移

```text
active
  ↓ 時間経過 / trust低下
stale
  ↓ 使用頻度低下
archived
  ↓ 誤情報・危険・失効
invalidated
  ↓ 削除要求
deleted
```

### 5.3 lifecycle fields

```json
{
  "created_at": "2026-05-24T00:00:00Z",
  "last_accessed": "2026-05-24T03:00:00Z",
  "access_count": 12,
  "decay_rate": 0.05,
  "expiration": null,
  "status": "active"
}
```

---

## 6. Context Invalidation

Context Invalidation は、古い・誤った・危険な記憶を無効化する機能である。

### 6.1 無効化理由

* **outdated**: 古い
* **contradicted**: 新情報と矛盾
* **security_risk**: 危険
* **revoked**: 権限・鍵・仕様が失効
* **hallucinated**: 誤生成由来
* **corrupted**: 改ざん・破損
* **user_request**: ユーザー要請

### 6.2 無効化例

```json
{
  "pointer_id": "ptr_0042",
  "status": "invalidated",
  "invalidated_reason": "revoked",
  "invalidated_at": "2026-05-24T04:00:00Z",
  "replacement_pointer": "ptr_0091"
}
```

---

## 7. Multi-Agent Pointer Exchange

複数エージェント間で、全文ではなくポインタを共有する。

### 7.1 形式

* `ptr://security/incident/042`
* `ptr://project/context-pointer-os/spec/latest`
* `ptr://memory/user/preferences/ai-writing-style`

### 7.2 交換例

```json
{
  "from_agent": "SecurityAgent",
  "to_agent": "AuditAgent",
  "pointer": "ptr://security/incident/042",
  "purpose": "audit_required",
  "access_level": "restricted"
}
```

### 7.3 利点

* token削減
* 文脈共有
* agent間連携
* 情報の一貫性維持
* 監査可能性向上

---

## 8. Memory Trust Scoring

各ポインタには信頼度を付与する。

### 8.1 trust_score

* 0.00 = 信頼不可
* 0.50 = 未検証
* 1.00 = 高信頼

### 8.2 算出要素

* source_reliability
* recency
* verification_count
* cross_agent_agreement
* user_confirmation
* execution_success
* invalidation_history

### 8.3 例

```json
{
  "pointer_id": "ptr_0007",
  "trust_score": 0.88,
  "verified_by": ["User", "SecurityAgent"],
  "source_reliability": 0.95,
  "last_verified": "2026-05-24T02:30:00Z"
}
```

---

## 9. Retrieval Governance

### 9.1 retrieval_policy

```json
{
  "allowed_context_types": ["project_memory", "code", "spec"],
  "blocked_context_types": ["private_credentials"],
  "max_retrieval_depth": 2,
  "minimum_trust_score": 0.7,
  "requires_human_approval": false,
  "audit_required": true
}
```

### 9.2 監査ログ

```json
{
  "event": "context_retrieval",
  "agent": "CodingAgent",
  "pointer_id": "ptr_0021",
  "reason": "generate_spec_update",
  "timestamp": "2026-05-24T05:00:00Z",
  "approved": true
}
```

---

## 10. 最小API仕様

* `create_pointer(context_type, summary, source, location, priority)`
* `retrieve_context(pointer_id, agent_id, purpose)`
* `invalidate_pointer(pointer_id, reason)`
* `update_trust_score(pointer_id, score, reason)`
* `exchange_pointer(from_agent, to_agent, pointer_id, purpose)`

---

## 11. 最小データスキーマ

```json
{
  "pointer_id": "string",
  "context_type": "string",
  "summary": "string",
  "source": "string",
  "location": "string",
  "priority": "float",
  "trust_score": "float",
  "sensitivity_level": "public | internal | private | restricted",
  "retrieval_rule": "string",
  "created_at": "datetime",
  "last_accessed": "datetime | null",
  "access_count": "integer",
  "decay_rate": "float",
  "expiration": "datetime | null",
  "status": "active | stale | archived | invalidated | deleted",
  "dependencies": ["pointer_id"],
  "metadata": {}
}
```

---

## 12. 設計思想

Context Pointer OS は、AIエージェントに「巨大な記憶」を与えるのではなく、記憶を扱うための運用規則を与える。

重要なのは、記憶量ではない。

重要なのは、

**どの記憶を、いつ、なぜ、どの信頼度で、どこまで使うか。**

これを管理すること。

---

## 13. まとめ

Context Pointer OS は、次の5要素を中核とする。

1. **Pointer Lifecycle**
2. **Context Invalidation**
3. **Multi-Agent Pointer Exchange**
4. **Memory Trust Scoring**
5. **Retrieval Governance**

これは単なるRAG拡張ではなく、**AIエージェントのための Memory Operating Layer** である。
