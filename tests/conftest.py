"""Test fixtures and configuration.

When Reflex is installed, it upgrades Starlette beyond what FastAPI supports.
Tests that depend on FastAPI are automatically skipped in this environment.
The Reflex handler tests (test_reflex_parity.py) don't need FastAPI and
always run.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Check if FastAPI is importable (it may be broken by Reflex's Starlette)
try:
    from fastapi import FastAPI
    _ = FastAPI()  # test instantiation
    FASTAPI_AVAILABLE = True
except Exception:
    FASTAPI_AVAILABLE = False

# Skip collection of FastAPI-dependent tests when FastAPI is broken
if not FASTAPI_AVAILABLE:
    import pytest
    # Mark test files that import FastAPI to be skipped
    collect_ignore = [
        "test_cvgen.py",
        "test_production_qa.py",
    ]
    # test_failover.py doesn't import FastAPI directly but may import modules
    # that do — let it try and fail gracefully
