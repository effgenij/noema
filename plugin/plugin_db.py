"""Adapter helper: resolve the Cortex data directory under the Hermes home.

Shared by the REST routes (plugin_api.py) and the agent tools (__init__.py).
"""

from pathlib import Path


def db_path() -> Path:
    from hermes_cli.main import get_hermes_home  # type: ignore[reportMissingImports]  # runtime: gateway process

    data_dir = get_hermes_home() / "cortex"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "cortex.db"
