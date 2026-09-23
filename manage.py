#!/usr/bin/env python
import os
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from importlib.util import find_spec
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def prepare_local_python():
    """Run the local server with the project's Python 3.13 environment."""
    venv = BASE_DIR / ".venv"
    if Path(sys.prefix) == venv:
        return

    python = venv / "bin" / "python"
    if not python.exists():
        python313 = shutil.which("python3.13")
        if python313 is None:
            raise SystemExit("Python 3.13 is required. Install it, then rerun this command.")
        subprocess.run([python313, "-m", "venv", str(venv)], check=True)

    os.execv(str(python), [str(python), str(BASE_DIR / "manage.py"), *sys.argv[1:]])


def install_if_needed():
    try:
        version("chartdb-backend")
    except PackageNotFoundError:
        installed = False
    else:
        installed = find_spec("django") is not None

    if not installed:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", str(BASE_DIR)], check=True)


def main():
    local_server = len(sys.argv) > 1 and sys.argv[1] == "runserver"
    if local_server:
        prepare_local_python()
        install_if_needed()
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_local")
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    from django.core.management import execute_from_command_line

    uses_local_settings = (
        os.getenv("DJANGO_SETTINGS_MODULE") == "config.settings_local"
        and not any(arg.startswith("--settings") for arg in sys.argv[2:])
    )
    if local_server and uses_local_settings and os.getenv("RUN_MAIN") != "true":
        execute_from_command_line([sys.argv[0], "migrate", "--noinput", "--verbosity", "0"])

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
