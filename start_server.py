#!/usr/bin/env python3
"""Double-fork daemonizer to keep uvicorn alive after the launching shell exits."""
import os
import sys
import subprocess
from pathlib import Path

LOG = Path("/home/z/audit/server.log")
PID = Path("/home/z/audit/server.pid")


def main():
    # First fork
    if os.fork() > 0:
        return
    # Decouple from parent environment
    os.setsid()
    # Second fork
    if os.fork() > 0:
        return
    # Now we're a daemon; redirect stdio
    sys.stdout.flush()
    sys.stderr.flush()
    log_fd = os.open(str(LOG), os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o644)
    os.dup2(log_fd, 0)
    os.dup2(log_fd, 1)
    os.dup2(log_fd, 2)
    # Write PID
    PID.write_text(str(os.getpid()))
    # Exec uvicorn
    os.execvp("uvicorn", ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"])


if __name__ == "__main__":
    main()
