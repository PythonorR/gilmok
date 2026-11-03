"""Gilmok API entry point. Request handlers only read precomputed data from the database."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import install_error_handlers
from app.routers import businesses, datasets, heatmap, locations


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Gilmok API",
        version="0.1.0",
        description="상권 입지 분석 API. 점수는 입력 지표의 상대적 합성값이며 창업 성공 확률이 아닙니다.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "X-Owner-Key"],
    )
    install_error_handlers(app)
    for r in (locations.router, businesses.router, heatmap.router, datasets.router):
        app.include_router(r)

    @app.get("/api/health", tags=["meta"])
    def health() -> dict[str, object]:
        return {"status": "ok", "demo_mode": settings.demo_mode}

    return app


app = create_app()
