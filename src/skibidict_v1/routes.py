from __future__ import annotations

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from . import db


async def list_words(request: Request) -> JSONResponse:
    q = request.query_params.get("q")
    words = await db.get_words(request.state.db, query=q)
    return JSONResponse(words)


async def create_word(request: Request) -> JSONResponse:
    body = await request.json()
    word = await db.insert_word(request.state.db, body)
    return JSONResponse(word, status_code=201)


async def get_word(request: Request) -> JSONResponse:
    word_id = int(request.path_params["id"])
    word = await db.get_word(request.state.db, word_id)
    if word is None:
        return JSONResponse({"detail": "not found"}, status_code=404)
    return JSONResponse(word)


async def update_word(request: Request) -> JSONResponse:
    word_id = int(request.path_params["id"])
    body = await request.json()
    word = await db.update_word(request.state.db, word_id, body)
    if word is None:
        return JSONResponse({"detail": "not found"}, status_code=404)
    return JSONResponse(word)


async def delete_word(request: Request) -> Response:
    word_id = int(request.path_params["id"])
    deleted = await db.delete_word(request.state.db, word_id)
    if not deleted:
        return JSONResponse({"detail": "not found"}, status_code=404)
    return Response(status_code=204)
