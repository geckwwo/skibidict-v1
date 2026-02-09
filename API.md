# Skibidict API

Base URL: `http://localhost:8000`

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
