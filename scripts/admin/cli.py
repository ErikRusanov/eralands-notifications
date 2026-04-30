"""cli — argparse-диспетчер пайплайнов admin-CLI."""

from __future__ import annotations

import argparse
import sys

from scripts.admin.api import AdminAPI, AdminAPIError
from scripts.admin.config import resolve
from scripts.admin.pipelines import REGISTRY


def main(argv: list[str] | None = None) -> int:
    """Парсит аргументы, резолвит конфиг и запускает выбранный пайплайн."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    cfg = resolve(args.url, args.key)
    pipeline_fn, _ = REGISTRY[args.pipeline]
    try:
        with AdminAPI(cfg) as api:
            pipeline_fn(api)
    except AdminAPIError as exc:
        print(f"\nОшибка: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nОтменено", file=sys.stderr)
        return 130
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scripts.admin",
        description="Админский CLI-костыль для пайплайнов поверх REST API.",
    )
    parser.add_argument(
        "--url",
        default=None,
        help="Базовый URL API (по умолчанию ADMIN_URL или http://localhost:8000)",
    )
    parser.add_argument(
        "--key",
        default=None,
        help="Bearer-ключ админки (по умолчанию ADMIN_KEY или API__KEY из .env)",
    )
    sub = parser.add_subparsers(dest="pipeline", required=True, metavar="PIPELINE")
    for name, (_, summary) in REGISTRY.items():
        sub.add_parser(name, help=summary)
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
