from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from screening_assurance.engine import diagnose, load_bundle
from screening_assurance.knowledge import load_pack

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "northwind" / "requisitions"
PACK = ROOT / "knowledge" / "pack"
RELEASE_100 = ROOT / "knowledge" / "releases" / "1.0.0"
CASES = ROOT / "evals" / "cases"
RUN_AT = "2026-10-11T12:00:00+00:00"


@pytest.fixture(scope="session")
def pack():
    return load_pack(PACK)


@pytest.fixture(scope="session")
def pack_100():
    return load_pack(RELEASE_100)


def bundle_without_feedback(name: str):
    """A requisition bundle without decisions/outcomes (the 'first run' state)."""
    b = load_bundle(EXAMPLES / name)
    b.decisions = None
    b.outcomes = None
    return b


def run(name: str, pack, *, with_feedback: bool = False):
    b = load_bundle(EXAMPLES / name) if with_feedback else bundle_without_feedback(name)
    return diagnose(b, pack, run_at=RUN_AT)


@pytest.fixture
def pack_copy(tmp_path):
    dest = tmp_path / "pack"
    shutil.copytree(PACK, dest)
    return dest


def by_check(result, check, **kw):
    out = []
    for f in result.findings:
        if f.check != check:
            continue
        if all(getattr(f, k) == v for k, v in kw.items()):
            out.append(f)
    return out
