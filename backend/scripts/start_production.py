#!/usr/bin/env python3
"""Point d'entrée production (Railway, Render, VPS) : migrations, static, Gunicorn."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent


def run_manage(*args: str) -> None:
    subprocess.run([sys.executable, "manage.py", *args], cwd=BACKEND, check=True)


def maybe_bootstrap() -> None:
    if os.environ.get("RUN_BOOTSTRAP", "").strip() != "1":
        return
    run_manage("setup_demo")
    if os.environ.get("SKIP_GEN3", "").strip() == "1":
        return
    subprocess.run(
        [sys.executable, "manage.py", "setup_gen3", "--allow-download"],
        cwd=BACKEND,
        check=True,
    )


def main() -> None:
    run_manage("migrate")
    run_manage("collectstatic", "--noinput")
    maybe_bootstrap()

    port = os.environ.get("PORT", "8000")
    workers = os.environ.get("WEB_CONCURRENCY", "2")
    timeout = os.environ.get("GUNICORN_TIMEOUT", "120")

    os.execvp(
        "gunicorn",
        [
            "gunicorn",
            "config.wsgi:application",
            "--bind",
            f"0.0.0.0:{port}",
            "--workers",
            workers,
            "--timeout",
            timeout,
            "--access-logfile",
            "-",
            "--error-logfile",
            "-",
        ],
    )


if __name__ == "__main__":
    main()
