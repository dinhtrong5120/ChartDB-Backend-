#!/usr/bin/env python
import os
import shutil
import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def prepare_local_python():
    """Use installed dependencies, or bootstrap a venv if this Python lacks them."""
    venv = BASE_DIR / ".venv"
    required_modules = ("django", "rest_framework", "corsheaders", "drf_spectacular", "dotenv")
    if all(find_spec(module) is not None for module in required_modules):
        return

    if Path(sys.prefix) == venv:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", str(BASE_DIR)], check=True)
        os.execv(str(sys.executable), [sys.executable, str(BASE_DIR / "manage.py"), *sys.argv[1:]])

    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        if sys.version_info < (3, 13):
            python313 = shutil.which("python3.13")
            if python313 is None and os.name == "nt":
                launcher = shutil.which("py")
                if launcher:
                    result = subprocess.run(
                        [launcher, "-3.13", "-c", "import sys; print(sys.executable)"],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    python313 = result.stdout.strip() if result.returncode == 0 else None
            if python313 is None:
                raise SystemExit("Python 3.13 is required. Install it, then rerun this command.")
            subprocess.run([python313, "-m", "venv", str(venv)], check=True)
        else:
            subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)

    subprocess.run([str(python), "-m", "pip", "install", "-e", str(BASE_DIR)], check=True)
    os.execv(str(python), [str(python), str(BASE_DIR / "manage.py"), *sys.argv[1:]])


def main():
    local_server = len(sys.argv) > 1 and sys.argv[1] == "runserver"
    if local_server:
        prepare_local_python()
        from dotenv import load_dotenv

        load_dotenv(BASE_DIR / ".env.local", override=True)
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
