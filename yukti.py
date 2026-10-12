#!/usr/bin/env python3
"""Convenience entrypoint for the Yukti CLI."""

import sys
from pathlib import Path

# Add src to sys.path so the CLI runs directly without installation
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from yukti.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
