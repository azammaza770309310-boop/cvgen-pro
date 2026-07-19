#!/usr/bin/env python3
"""Watchdog: keeps the zai-bridge Node.js process alive."""
import subprocess, time, os, signal, sys

BRIDGE_SCRIPT = "/home/z/my-project/zai-bridge.js"
LOG_FILE = "/home/z/audit/zai-bridge.log"

def main():
    # Fork into background
    if os.fork() > 0:
        return
    os.setsid()
    if os.fork() > 0:
        os._exit(0)
    # Daemon now
    sys.stdout.flush()
    sys.stderr.flush()
    log_fd = os.open(LOG_FILE, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o644)
    os.dup2(log_fd, 0)
    os.dup2(log_fd, 1)
    os.dup2(log_fd, 2)
    with open("/home/z/audit/zai-bridge.pid", "w") as f:
        f.write(str(os.getpid()))
    # Supervisor loop
    while True:
        proc = subprocess.Popen(["node", BRIDGE_SCRIPT], cwd="/home/z/my-project")
        proc.wait()
        if proc.returncode != 0:
            time.sleep(2)  # backoff before restart
        else:
            break

if __name__ == "__main__":
    main()
