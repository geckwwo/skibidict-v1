from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aiosqlite
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.types import ASGIApp, Receive, Scope, Send

from . import db, routes


_db_conn: aiosqlite.Connection | None = None


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    global _db_conn
    _db_conn = await db.init_db()
    yield
    await _db_conn.close()


class DBMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            scope.setdefault("state", {})["db"] = _db_conn
        await self.app(scope, receive, send)


class AuthMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        auth = headers.get(b"authorization", b"").decode()
        token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else ""

        assert _db_conn is not None
        user = await db.get_user_by_token(_db_conn, token) if token else None
        if user is None:
            response = JSONResponse(
                {"detail": "unauthorized"}, status_code=401
            )
            await response(scope, receive, send)
            return

        scope.setdefault("state", {})["user"] = user
        await self.app(scope, receive, send)


app = Starlette(
    routes=[
        Route("/words", routes.list_words, methods=["GET"]),
        Route("/words", routes.create_word, methods=["POST"]),
        Route("/words/{id:int}", routes.get_word, methods=["GET"]),
        Route("/words/{id:int}", routes.update_word, methods=["PUT"]),
        Route("/words/{id:int}", routes.delete_word, methods=["DELETE"]),
        Route("/logs", routes.list_logs, methods=["GET"]),
    ],
    middleware=[Middleware(DBMiddleware), Middleware(AuthMiddleware)],
    lifespan=lifespan,
)
