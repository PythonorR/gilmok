# 길목 (Gilmok)

공공데이터 기반 창업 입지 분석 서비스. Data-driven location intelligence for small-business
founders in Korea. v1 scope: **서울 마포구 · 카페**.

> Status: **Step 1 of 7** — architecture, schema, API contract and skeleton.
> Endpoints other than `/api/health` and `/api/datasets/status` return `501 NOT_IMPLEMENTED`.

Docs: [architecture](docs/architecture.md) · [scoring](docs/scoring.md) · [datasets](docs/datasets.md) · [pipelines](pipelines/README.md)

## Local development

Requirements: Docker (for PostGIS), Python 3.12+ with [uv](https://docs.astral.sh/uv/), Node 20+.

```bash
cp .env.example .env
docker compose up -d db
```

API:

```bash
cd services/api
uv venv && uv pip install -e ".[dev]"
.venv/bin/alembic upgrade head
.venv/bin/pytest
.venv/bin/uvicorn app.main:app --reload --port 8000   # docs: http://localhost:8000/docs
```

Web:

```bash
cd apps/web
npm install
npm run gen:api      # regenerate lib/api/schema.ts from the running API
npm run dev          # http://localhost:3000
```

## Credentials

All keys are read from environment variables. Only `NEXT_PUBLIC_*` values reach the browser.

| Variable | Where to get it | Notes |
|---|---|---|
| `DATA_GO_KR_SERVICE_KEY` | [data.go.kr](https://www.data.go.kr) → 회원가입 → 데이터셋 15012005 "활용신청" | Server only. Approval may take time; daily call limits apply. |
| `SEOUL_OPEN_API_KEY` | [data.seoul.go.kr](https://data.seoul.go.kr) → 회원가입 → 인증키 신청 | Server only. |
| `KAKAO_REST_API_KEY` | [Kakao Developers](https://developers.kakao.com) → 내 애플리케이션 → 앱 키 | Server only (search proxy). |
| `NEXT_PUBLIC_KAKAO_JS_KEY` | Same app → JavaScript 키 | Browser. Register every site domain (incl. `http://localhost:3000`) under 플랫폼 → Web or the map will not load. Businesses must set up a Biz app. |

Without keys the app runs in **demo mode** with synthetic data, always labelled "샘플 데이터".

## Before production

Verify licensing, redistribution rights, API limits and commercial-use terms for every dataset
and for the Kakao terms of service. Kakao API results must not be stored permanently. Items not
yet verified are marked **needs verification** in `docs/datasets.md`.
