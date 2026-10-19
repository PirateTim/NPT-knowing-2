"""
NPT Fleet: Script Execution Tracker & Header Synchronizer
How to run:
    uv run python helper_scripts/run_tracker.py

What it does:
    1. Provides `record_run(__file__)` which automatically stamps the `Last run: <timestamp>`
       header inside any helper script upon execution.
    2. Operates as a CLI wrapper runner:
       `uv run python helper_scripts/run_tracker.py <path_to_script> [args...]`
    3. Provides `--audit` to check and report the header compliance and last run status of all helper scripts.

Last run: Unknown
"""

import os
import sys
import re
import subprocess
from datetime import datetime


def record_run(script_path: str = None) -> bool:
    """
    Updates the 'Last run: ...' line in the target script's top docstring/comment
    with the current local timestamp. Fails gracefully without raising exceptions.
    """
    if not script_path:
        return False
    try:
        script_path = os.path.abspath(script_path)
        if not os.path.exists(script_path):
            return False

        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Match "Last run: <anything>" or "Last Run: <anything>"
        pattern = r"([Ll]ast\s+[Rr]un:\s*)[^\n\r]+"
        if re.search(pattern, content):
            new_content = re.sub(pattern, rf"\g<1>{now_str}", content, count=1)
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True
        return False
    except Exception:
        return False


def audit_helper_scripts(helper_dir: str = None):
    """Audits all scripts in helper_scripts for header compliance and last-run timestamp."""
    if not helper_dir:
        helper_dir = os.path.dirname(os.path.abspath(__file__))

    print("\n" + "=" * 80)
    print("NPT FLEET HELPER SCRIPTS HEADER AUDIT")
    print("=" * 80)

    total = 0
    compliant = 0
    for root, _, files in os.walk(helper_dir):
        for f in sorted(files):
            if f.endswith((".py", ".ps1", ".bat")):
                total += 1
                fpath = os.path.join(root, f)
                rel_path = os.path.relpath(fpath, os.path.dirname(helper_dir)).replace("\\", "/")
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                    header = fp.read(1500)

                has_how = bool(re.search(r"[Hh]ow to run:", header))
                has_what = bool(re.search(r"[Ww]hat it does:", header))
                has_last = bool(re.search(r"[Ll]ast [Rr]un:", header))

                m = re.search(r"[Ll]ast [Rr]un:\s*([^\n\r]+)", header)
                last_run_val = m.group(1).strip() if m else "MISSING"

                if has_how and has_what and has_last:
                    compliant += 1
                    status = "[OK] COMPLIANT"
                else:
                    status = "[!] NON-COMPLIANT"

                print(f"{status:17} | {rel_path:45} | Last Run: {last_run_val}")

    print("=" * 80)
    print(f"Summary: {compliant}/{total} scripts compliant ({compliant/total*100:.1f}%)" if total else "No scripts found.")
    print("=" * 80 + "\n")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--audit", "-a"):
        audit_helper_scripts()
        return

    target_script = sys.argv[1]
    script_args = sys.argv[2:]

    if not os.path.exists(target_script):
        print(f"[ERROR] Script not found: {target_script}")
        sys.exit(1)

    # Stamp the script header
    record_run(target_script)

    # Run the script via uv run python
    cmd = ["uv", "run", "python", target_script] + script_args
    proc = subprocess.run(cmd)
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
