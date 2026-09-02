import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.dirname(__file__))


def run_command(command):
    print(f"\n>> {command}")
    result = subprocess.run(command, cwd=ROOT, shell=True)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main():
    try:
        import customtkinter  # noqa: F401
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing dependency: customtkinter. Run: pip install -r requirements.txt"
        ) from exc

    data_dir = os.path.join(os.path.expanduser("~"), ".studyapp_release_check")
    os.makedirs(data_dir, exist_ok=True)
    marker = os.path.join(data_dir, "release_check_ok.txt")
    with open(marker, "w", encoding="utf-8") as handle:
        handle.write("ready")

    print("Release environment check: OK")
    print(f"Data directory is writable: {data_dir}")
    run_command(f'"{sys.executable}" -m unittest discover -s tests -q')
    print("\nAll release checks passed.")


if __name__ == "__main__":
    main()
