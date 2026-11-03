"""One consistent error format for every endpoint: {"code", "message", "details"}.

`code` is a stable English identifier; `message` is Korean user-facing text.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(self, status: int, code: str, message: str, details: Any = None) -> None:
        self.status, self.code, self.message, self.details = status, code, message, details
        super().__init__(message)


def bad_request(code: str, message: str, details: Any = None) -> AppError:
    return AppError(400, code, message, details)


def not_implemented(feature: str) -> AppError:
    return AppError(501, "NOT_IMPLEMENTED", "아직 준비 중인 기능입니다.", {"feature": feature})


def _body(code: str, message: str, details: Any = None) -> dict[str, Any]:
    return {"code": code, "message": message, "details": details}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status, content=_body(exc.code, exc.message, exc.details)
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"loc": list(e.get("loc", [])), "msg": e.get("msg"), "type": e.get("type")}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_body("VALIDATION_ERROR", "요청 값이 올바르지 않습니다.", details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, "HTTP_ERROR")
        msg = (
            "요청한 리소스를 찾을 수 없습니다."
            if exc.status_code == 404
            else "요청을 처리할 수 없습니다."
        )
        return JSONResponse(status_code=exc.status_code, content=_body(code, msg, exc.detail))
