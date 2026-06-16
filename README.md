# Hospital Inquiry PoC

病院向け患者問い合わせ・エスカレーション管理システム

## 技術スタック

| カテゴリ | 技術 |
|---|---|
| Backend | FastAPI / Python 3.12 |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| ORM | SQLAlchemy 2.0 (async) |
| Migration | Alembic |
| Auth | JWT (Access Token + Refresh Token) |
| AI | Anthropic Claude API |
| Container | Docker / Docker Compose |
| CI | GitHub Actions |

## 機能一覧

- 患者問い合わせチケット管理
- ロールベースアクセス制御 (RBAC: Patient / Nurse / Doctor / Admin)
- 看護師→医師へのエスカレーション
- AIによる問い合わせ自動分類・緊急度判定
- SLA管理・超過通知
- アプリ内通知
- KPIダッシュボード
- 監査ログ

## ローカル開発環境のセットアップ

### 必要なもの

- Docker Desktop
- Git

### 手順

```bash
# リポジトリをクローン
git clone https://github.com/SayokoAkiike/hospital-inquiry-poc.git
cd hospital-inquiry-poc

# 環境変数を設定
cp .env.example .env
# .env の ANTHROPIC_API_KEY を設定

# 起動
docker compose up -d

# マイグレーション
docker compose exec api alembic upgrade head
```

起動後、以下にアクセス：

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

## API一覧

| メソッド | パス | 説明 |
|---|---|---|
| POST | /api/v1/auth/register | ユーザー登録 |
| POST | /api/v1/auth/login | ログイン |
| POST | /api/v1/auth/refresh | トークン更新 |
| GET/POST | /api/v1/patients | 患者一覧・作成 |
| GET/POST | /api/v1/tickets | チケット一覧・作成 |
| PATCH | /api/v1/tickets/{id} | チケット更新 |
| POST | /api/v1/tickets/{id}/escalate | エスカレーション |
| GET/POST | /api/v1/tickets/{id}/messages | メッセージ |
| GET | /api/v1/kpi | KPIダッシュボード |
| GET | /api/v1/audit-logs | 監査ログ |
| GET | /api/v1/notifications | 通知一覧 |
| POST | /api/v1/admin/check-sla | SLAチェック実行 |

## 本番環境へのデプロイ

### 事前準備

```bash
# SSL証明書を配置
mkdir -p docker/certs
# cert.pem と key.pem を docker/certs/ に配置

# 本番用環境変数を設定
cp .env.example .env.production
# 以下を必ず変更：
# - SECRET_KEY（python3 -c "import secrets; print(secrets.token_hex(32))" で生成）
# - POSTGRES_PASSWORD
# - ANTHROPIC_API_KEY
# - DATABASE_URL のパスワード部分
```

### 起動

```bash
# 本番環境で起動
docker compose -f docker-compose.prod.yml up -d

# マイグレーション実行
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### 注意事項

- `.env.production` は絶対に Git にコミットしない
- 本番では `DEBUG=false` にする（Swagger UIが非表示になる）
- SSL証明書は Let's Encrypt 等で取得する

## テスト実行

```bash
docker compose exec api python -m pytest tests/ -v
```

## CI/CD

GitHub Actions により main ブランチへの Push 時に自動で以下を実行：

- Ruff によるLintチェック
- Pytest によるテスト実行
