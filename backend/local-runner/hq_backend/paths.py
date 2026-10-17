"""Stable source roots shared by relocated backend domain modules."""

from pathlib import Path


LOCAL_RUNNER_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = LOCAL_RUNNER_DIR.parent.parent
