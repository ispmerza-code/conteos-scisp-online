"""Run backend and frontend development servers at the same time."""

from __future__ import annotations

import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "conteos-frontend"


def resolve_python_command() -> list[str]:
    venv_python = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return [str(venv_python)]
    return [sys.executable]


def resolve_npm_command() -> list[str]:
    npm_path = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm_path:
        raise FileNotFoundError(
            "npm was not found in PATH. Install Node.js or open a terminal where npm is available."
        )
    return [npm_path]


def terminate_process(process: subprocess.Popen, name: str) -> None:
    if process.poll() is not None:
        return

    print(f"\nStopping {name}...")
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def main() -> int:
    if not FRONTEND_DIR.exists():
        print(f"Frontend folder not found: {FRONTEND_DIR}")
        return 1

    backend_cmd = resolve_python_command() + ["run_dev.py"]
    frontend_cmd = resolve_npm_command() + ["run", "dev"]

    print(f"Starting backend: {' '.join(backend_cmd)}")
    backend_process = subprocess.Popen(backend_cmd, cwd=str(ROOT_DIR))

    print(f"Starting frontend: {' '.join(frontend_cmd)}")
    print()
    print("=" * 60)
    print("HTTPS habilitado — la primera vez, acepta el certificado")
    print("autofirmado en el navegador:")
    print("  Chrome/Edge: 'Configuracion avanzada' > 'Continuar a ... (no seguro)'")
    print("  iOS Safari: Configuracion > General > Descripcion de perfil")
    print("  Android Chrome: 'Configuracion avanzada' > 'Continuar'")
    print("Esto es necesario para que la camara funcione via IP.")
    print("=" * 60)
    print()
    frontend_process = subprocess.Popen(frontend_cmd, cwd=str(FRONTEND_DIR))

    shutdown_requested = False

    def on_signal(signum: int, _frame: object) -> None:
        nonlocal shutdown_requested
        if not shutdown_requested:
            print(f"\nSignal received ({signum}). Shutting down both servers...")
        shutdown_requested = True

    signal.signal(signal.SIGINT, on_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, on_signal)

    exit_code = 0
    try:
        while not shutdown_requested:
            backend_code = backend_process.poll()
            frontend_code = frontend_process.poll()

            if backend_code is not None or frontend_code is not None:
                if backend_code not in (None, 0):
                    print(f"Backend exited with code {backend_code}.")
                    exit_code = backend_code
                if frontend_code not in (None, 0):
                    print(f"Frontend exited with code {frontend_code}.")
                    exit_code = frontend_code
                break

            time.sleep(1)
    finally:
        terminate_process(backend_process, "backend")
        terminate_process(frontend_process, "frontend")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
