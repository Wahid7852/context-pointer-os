# CPOS Development Mandates (v0.4 Roadmap)

## 🎯 Strategic Objective
Context Pointer OS をローカル環境から「分散型認知インフラ」へと進化させる。

## 🛠️ v0.4 Core Components

### 1. Distributed Pointer Protocol
- URI 形式の拡張: `ptr://<node_id>.<domain>/<type>/<id>`
- リモートポインタの解決ロジックの実装。

### 2. Cognitive Gateway
- 外部ソース (MCP, API, 他のカーネル) とのセキュアな接続層。
- データのストリーミングロード対応。

### 3. Secure Handshake & Auth
- カーネルインスタンス間での相互認証。
- `trust_score` に基づく動的アクセス権限の委譲。

### 4. Remote Invalidation (Cognitive Immune System)
- `INVALIDATE` 命令の広域通知。
- ネットワーク全体の知識整合性維持。

## ⚠️ Safety & Integrity
- ネットワーク経由の Prompt Injection 対策の強化。
- 機密情報の自動フィルタリング (`Governance Layer`) の強制適用。
