"""Start Janus + the sibling Minerva checkout; Ctrl+C stops both processes."""

import argparse
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.request


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--minerva", type=Path, default=root.parent / "minerva")
    args = parser.parse_args()
    minerva = args.minerva.resolve()
    node = shutil.which("node")
    if not node or not (minerva / "node_modules/vite/bin/vite.js").is_file():
        parser.error("Install Node and run npm ci in the Minerva checkout first.")
    if not (minerva / "scripts/dev-demo.mjs").is_file():
        parser.error("The Minerva checkout needs scripts/dev-demo.mjs.")
    # Refuse occupied ports; never stop unrelated services or choose hidden ports.
    for port in (5000, 5173):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                parser.error(f"Port {port} is already in use. Stop that service and retry.")
    logs = root / ".local-demo"
    logs.mkdir(exist_ok=True)
    children = []
    handles = []
    flags = (subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP) if os.name == "nt" else 0
    try:
        for name, command, cwd, url in (
            ("janus", [sys.executable, "-u", str(root / "run_demo.py")], root, "http://127.0.0.1:5000/health"),
            ("minerva", [node, str(minerva / "scripts/dev-demo.mjs")], minerva, "http://127.0.0.1:5173"),
        ):
            handle = (logs / f"{name}.log").open("w", encoding="utf-8")
            handles.append(handle)
            child = subprocess.Popen(command, cwd=cwd, stdout=handle, stderr=subprocess.STDOUT,
                                     stdin=subprocess.DEVNULL, creationflags=flags)
            children.append(child)
            deadline = time.monotonic() + 40
            while True:
                if child.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError(f"{name} did not start. See {logs / (name + '.log')}")
                try:
                    with urllib.request.urlopen(url, timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(0.3)
        print("Minerva: http://127.0.0.1:5173\nJanus:   http://127.0.0.1:5000", flush=True)
        print("Click Use demo account, or sign in with demo@minerva.local / minerva-demo.", flush=True)
        print(f"Synthetic data only. Logs: {logs}\nPress Ctrl+C to stop both apps.", flush=True)
        while all(child.poll() is None for child in children):
            time.sleep(0.5)
        raise RuntimeError(f"A demo service stopped. See {logs}")
    except KeyboardInterrupt:
        print("\nStopping local demo.", flush=True)
    finally:
        for child in reversed(children):
            if child.poll() is None:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"],
                                   capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    child.terminate()
                child.wait(timeout=10)
        for handle in handles:
            handle.close()


if __name__ == "__main__":
    main()
