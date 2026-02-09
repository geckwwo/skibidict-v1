from __future__ import annotations

import argparse
import asyncio
import secrets

from . import db


async def _add_user(name: str) -> None:
    conn = await db.init_db()
    token = secrets.token_hex(32)
    try:
        await db.create_user(conn, name, token)
    except Exception as exc:
        await conn.close()
        raise SystemExit(f"error: {exc}") from exc
    await conn.close()
    print(f"created user {name!r}")
    print(f"token: {token}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="skibidict", description="Skibidict admin CLI")
    sub = parser.add_subparsers(dest="command")
    add = sub.add_parser("adduser", help="Create a new API user")
    add.add_argument("name", help="Username")
    args = parser.parse_args()

    if args.command == "adduser":
        asyncio.run(_add_user(args.name))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
