import argparse
import subprocess
import sys
from pathlib import Path


SERVICES = ("account", "event", "transaction", "ticket")


def run_command(command: list[str], cwd: Path) -> None:
    print(f"\n$ {' '.join(command)}  # cwd={cwd.relative_to(REPO_ROOT)}")
    subprocess.run(command, cwd=cwd, check=True)


def migrate_all() -> None:
    for service in SERVICES:
        service_dir = REPO_ROOT / "backend" / service
        run_command(["alembic", "upgrade", "head"], service_dir)


def show_current() -> None:
    for service in SERVICES:
        service_dir = REPO_ROOT / "backend" / service
        run_command(["alembic", "current"], service_dir)


def seed(reset: bool) -> None:
    command = [sys.executable, str(REPO_ROOT / "scripts" / "seed_all.py")]
    if reset:
        command.append("--reset")
    run_command(command, REPO_ROOT)


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Alembic migrations for all backend services.")
    parser.add_argument("--current", action="store_true", help="Show current Alembic revision for each service.")
    parser.add_argument("--seed", action="store_true", help="Run scripts/seed_all.py after migrations.")
    parser.add_argument("--reset-seed", action="store_true", help="Pass --reset to scripts/seed_all.py. Implies --seed.")
    args = parser.parse_args()

    try:
        if args.current:
            show_current()
        else:
            migrate_all()
            if args.seed or args.reset_seed:
                seed(reset=args.reset_seed)
    except subprocess.CalledProcessError as exc:
        print(f"\n❌ Command failed with exit code {exc.returncode}.", file=sys.stderr)
        return exc.returncode

    print("\n✅ Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
