# Skibidict API

Base URL: `http://localhost:8000`

## Authentication

All endpoints require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <token>
```

Tokens are created via the CLI (not the API):

```sh
uv run skibidict adduser alice
```

Response `401` when missing or invalid:

```json
{ "detail": "unauthorized" }
```

## Endpoints

### List words

`GET /words`

Optional query param `?q=` to search by spelling (substring match).

```
GET /words?q=ya
```

```json
[
  {
    "id": 1,
    "spellings": ["ya", "yo", "ya-", "yo-"],
    "definitions": [
      { "description": "affirmative prefix", "tags": ["prefix"] }
    ]
  }
]
```

### Create word

`POST /words`

```json
{
  "spellings": ["ya", "yo", "ya-", "yo-"],
  "definitions": [
    { "description": "affirmative prefix", "tags": ["prefix"] }
  ]
}
```

Response `201`:

```json
{
  "id": 1,
  "spellings": ["ya", "yo", "ya-", "yo-"],
  "definitions": [
    { "description": "affirmative prefix", "tags": ["prefix"] }
  ]
}
```

### Get word

`GET /words/{id}`

Response `200`:

```json
{
  "id": 1,
  "spellings": ["ya", "yo", "ya-", "yo-"],
  "definitions": [
    { "description": "affirmative prefix", "tags": ["prefix"] }
  ]
}
```

Response `404`:

```json
{ "detail": "not found" }
```

### Update word

`PUT /words/{id}`

Replaces all spellings and definitions.

```json
{
  "spellings": ["ya", "yo"],
  "definitions": [
    { "description": "agreement marker", "tags": ["prefix", "mood"] }
  ]
}
```

Response `200`:

```json
{
  "id": 1,
  "spellings": ["ya", "yo"],
  "definitions": [
    { "description": "agreement marker", "tags": ["prefix", "mood"] }
  ]
}
```

### Delete word

`DELETE /words/{id}`

Response `204` (no body) on success, `404` if not found.

### List logs

`GET /logs`

Returns actions performed by users, newest first. Read-only.

| Param | Default | Note |
|-------|---------|------|
| `limit` | `100` | Capped at 300 |
| `offset` | `0` | Unlimited |

```
GET /logs?limit=50&offset=100
```

```json
[
  {
    "id": 3,
    "user": "alice",
    "action": "delete_word",
    "detail": "id=1",
    "timestamp": "2026-02-09T12:34:56.789Z"
  },
  {
    "id": 2,
    "user": "alice",
    "action": "update_word",
    "detail": "id=1",
    "timestamp": "2026-02-09T12:34:50.123Z"
  },
  {
    "id": 1,
    "user": "alice",
    "action": "create_word",
    "detail": "id=1",
    "timestamp": "2026-02-09T12:34:45.000Z"
  }
]
```

Logged actions: `create_word`, `update_word`, `delete_word`.
