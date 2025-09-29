from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .config import load_config
from .db import Database
from .ingest import ingest_directory
from .scheduler import pick_next_unposted
from .publishers.console import ConsolePublisher
from .captions import generate_caption
from .server import run as run_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dailyvids",
        description="Automate daily posting of short videos",
    )
    parser.add_argument(
        "--config",
        default=str(Path(__file__).resolve().parent.parent / "config" / "config.json"),
        help="Path to config.json",
    )

    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="Initialize database")
    p_init.add_argument("--db", default=str(Path("dailyvids.sqlite3")), help="DB path")

    p_ingest = sub.add_parser("ingest", help="Ingest a directory of videos")
    p_ingest.add_argument("path", help="Directory containing videos")
    p_ingest.add_argument("--db", default=str(Path("dailyvids.sqlite3")), help="DB path")

    p_next = sub.add_parser("next", help="Show next video to post")
    p_next.add_argument("--db", default=str(Path("dailyvids.sqlite3")), help="DB path")

    p_post = sub.add_parser("post-once", help="Post one video via console publisher")
    p_post.add_argument("--db", default=str(Path("dailyvids.sqlite3")), help="DB path")

    p_serve = sub.add_parser("serve", help="Run the web UI server")
    p_serve.add_argument("--host", default="0.0.0.0")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--db", default=str(Path("dailyvids.sqlite3")))

    return parser


def cmd_init(db_path: str) -> int:
    db = Database(Path(db_path))
    db.init()
    print(f"Initialized DB at {db_path}")
    return 0


def cmd_ingest(db_path: str, directory: str) -> int:
    db = Database(Path(db_path))
    db.init()
    added = ingest_directory(db, Path(directory))
    print(f"Ingested {added} files from {directory}")
    return 0


def cmd_next(db_path: str) -> int:
    db = Database(Path(db_path))
    item = pick_next_unposted(db)
    if not item:
        print("No unposted items.")
        return 0
    print(json.dumps(item, indent=2))
    return 0


def cmd_post_once(config_path: str, db_path: str) -> int:
    config = load_config(Path(config_path))
    db = Database(Path(db_path))
    db.init()
    item = pick_next_unposted(db)
    if not item:
        print("No unposted items.")
        return 0
    caption = generate_caption(item)
    print(f"Caption: {caption}")
    publisher = ConsolePublisher()
    publisher.publish(item)
    db.mark_posted(item["id"])
    print(f"Posted: {item['path']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "init":
        return cmd_init(args.db)
    if args.command == "ingest":
        return cmd_ingest(args.db, args.path)
    if args.command == "next":
        return cmd_next(args.db)
    if args.command == "post-once":
        return cmd_post_once(args.config, args.db)
    if args.command == "serve":
        db_path = Path(args.db)
        db = Database(db_path)
        db.init()
        run_server(args.host, args.port, Path(__file__).resolve().parent.parent, db)
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

