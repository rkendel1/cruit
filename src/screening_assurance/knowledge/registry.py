"""Knowledge lifecycle: working pack -> approved release -> promoted environment -> rollback.

Layout under the knowledge root::

    pack/                 working copy (edited by administrators)
    releases/<version>/   immutable snapshots with RELEASE.json
    deployments.yaml      which release each environment uses, with full history
    proposals/            recruiter-submitted suggestions (never loaded by the engine)
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from ..contracts import ContractError, load, read_yaml
from .pack import KnowledgePack, load_pack
from .validate import validate_pack


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class KnowledgeRegistry:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.pack_dir = self.root / "pack"
        self.releases_dir = self.root / "releases"
        self.proposals_dir = self.root / "proposals"
        self.deployments_path = self.root / "deployments.yaml"

    # ------------------------------------------------------------ resolution
    def resolve(self, spec: str | None) -> Path:
        """Resolve a knowledge spec to a pack directory.

        Accepted forms: None/'pack' (working copy), 'release:<ver>', 'env:<name>', or a path.
        """
        if spec in (None, "", "pack"):
            return self.pack_dir
        if spec.startswith("release:"):
            p = self.releases_dir / spec.split(":", 1)[1]
            if not p.exists():
                raise FileNotFoundError(f"no knowledge release {p.name}; available: {self.releases()}")
            return p
        if spec.startswith("env:"):
            env = spec.split(":", 1)[1]
            version = self.deployments()["environments"].get(env)
            if not version:
                raise FileNotFoundError(f"environment '{env}' has no promoted knowledge release")
            return self.releases_dir / version
        return Path(spec)

    def load(self, spec: str | None) -> KnowledgePack:
        return load_pack(self.resolve(spec))

    # ------------------------------------------------------------ releases
    def releases(self) -> list[str]:
        if not self.releases_dir.exists():
            return []
        vs = [p.name for p in self.releases_dir.iterdir() if (p / "manifest.yaml").exists()]
        return sorted(vs, key=lambda v: tuple(int(x) for x in v.split(".")))

    def release(self, released_by: str, eval_summary: dict[str, Any] | None = None) -> Path:
        report = validate_pack(self.pack_dir)
        if not report.ok:
            raise ContractError(self.pack_dir, ["pack does not validate; cannot release", *report.errors])
        pack = load_pack(self.pack_dir)
        if pack.manifest["status"] != "approved":
            raise ContractError(
                self.pack_dir / "manifest.yaml",
                [f"manifest status is '{pack.manifest['status']}'; a reviewer must set status: approved "
                 "and approved_by before release"],
            )
        if not pack.manifest.get("approved_by"):
            raise ContractError(self.pack_dir / "manifest.yaml", ["approved_by is required for release"])
        dest = self.releases_dir / pack.version
        if dest.exists():
            raise ContractError(dest, [f"release {pack.version} already exists; bump manifest version"])
        shutil.copytree(self.pack_dir, dest)
        meta = {
            "version": pack.version,
            "fingerprint": pack.fingerprint,
            "checksum": pack.checksum,
            "released_at": _now(),
            "released_by": released_by,
            "approved_by": pack.manifest.get("approved_by"),
            "eval_summary": eval_summary,
        }
        (dest / "RELEASE.json").write_text(json.dumps(meta, indent=2) + "\n")
        return dest

    def verify_release(self, version: str) -> bool:
        dest = self.releases_dir / version
        meta = json.loads((dest / "RELEASE.json").read_text())
        return load_pack(dest).checksum == meta["checksum"]

    # ------------------------------------------------------------ deployments
    def deployments(self) -> dict[str, Any]:
        if self.deployments_path.exists():
            data = read_yaml(self.deployments_path) or {}
        else:
            data = {}
        data.setdefault("environments", {})
        data.setdefault("history", [])
        return data

    def _write_deployments(self, data: dict[str, Any]) -> None:
        self.deployments_path.write_text(yaml.safe_dump(data, sort_keys=False))

    def promote(self, version: str, env: str, by: str, reason: str, eval_summary: dict | None = None) -> None:
        if version not in self.releases():
            raise FileNotFoundError(f"release {version} not found; run 'knowledge release' first")
        if not self.verify_release(version):
            raise ContractError(self.releases_dir / version, ["release checksum mismatch; snapshot was modified"])
        data = self.deployments()
        previous = data["environments"].get(env)
        data["environments"][env] = version
        data["history"].append({
            "at": _now(), "action": "promote", "environment": env, "version": version,
            "previous": previous, "by": by, "reason": reason,
            "eval_passed": None if eval_summary is None else eval_summary.get("passed"),
        })
        self._write_deployments(data)

    def rollback(self, env: str, by: str, reason: str) -> str:
        data = self.deployments()
        current = data["environments"].get(env)
        if not current:
            raise FileNotFoundError(f"environment '{env}' has nothing to roll back")
        prior = None
        for h in reversed(data["history"]):
            if h["environment"] == env and h["version"] == current and h.get("previous"):
                prior = h["previous"]
                break
        if not prior:
            raise FileNotFoundError(f"no earlier release recorded for '{env}'")
        data["environments"][env] = prior
        data["history"].append({
            "at": _now(), "action": "rollback", "environment": env, "version": prior,
            "previous": current, "by": by, "reason": reason,
        })
        self._write_deployments(data)
        return prior

    # ------------------------------------------------------------ proposals
    def propose(self, proposal: dict[str, Any]) -> Path:
        self.proposals_dir.mkdir(parents=True, exist_ok=True)
        proposal.setdefault("submitted_at", _now())
        proposal.setdefault("status", "open")
        if not proposal.get("id"):
            n = len(list(self.proposals_dir.glob("*.yaml"))) + 1
            proposal["id"] = f"KP-{n:04d}"
        path = self.proposals_dir / f"{proposal['id']}.yaml"
        path.write_text(yaml.safe_dump(proposal, sort_keys=False))
        load("proposal", path)  # validate what we wrote
        return path

    def proposals(self) -> list[dict[str, Any]]:
        if not self.proposals_dir.exists():
            return []
        return [load("proposal", p) for p in sorted(self.proposals_dir.glob("*.yaml"))]
