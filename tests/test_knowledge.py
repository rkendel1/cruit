import json
import shutil

import pytest
import yaml

from screening_assurance.contracts import ContractError
from screening_assurance.knowledge import KnowledgeRegistry, diff_packs, load_pack, validate_pack

from conftest import PACK, RELEASE_100


def _edit(path, fn):
    data = yaml.safe_load(path.read_text())
    fn(data)
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def test_seed_pack_and_releases_validate():
    for p in (PACK, RELEASE_100):
        rep = validate_pack(p)
        assert rep.ok, rep.errors


def test_fingerprint_is_content_addressed(pack):
    assert pack.fingerprint.startswith("core@1.1.0+")
    assert load_pack(PACK).checksum == pack.checksum


def test_validation_blocks_equivalency_to_regulated_credential(pack_copy):
    def f(d):
        eq = d["records"][0]
        eq["target"] = "skill.cdl-class-a"
    _edit(pack_copy / "equivalencies.yaml", f)
    rep = validate_pack(pack_copy)
    assert not rep.ok
    assert any("regulated credential" in e for e in rep.errors)


def test_validation_catches_dangling_references(pack_copy):
    _edit(pack_copy / "skills.yaml", lambda d: d["records"][0]["relationships"].append(
        {"type": "closely_related", "target": "skill.does-not-exist"}))
    rep = validate_pack(pack_copy)
    assert any("skill.does-not-exist" in e for e in rep.errors)


def test_validation_catches_undocumented_term_collisions(pack_copy):
    # 'incident response' already names skill.incident-management
    _edit(pack_copy / "synonyms.yaml", lambda d: d["records"][3]["variants"].append(
        {"term": "incident response", "kind": "variant"}))
    rep = validate_pack(pack_copy)
    assert any("incident response" in e and "overlapping contexts" in e for e in rep.errors)


def test_validation_catches_contradictory_relationships(pack_copy):
    def f(d):
        sk = next(s for s in d["records"] if s["id"] == "skill.incident-management")
        sk["relationships"].append({"type": "transferable", "target": "skill.it-service-desk"})
    _edit(pack_copy / "skills.yaml", f)
    rep = validate_pack(pack_copy)
    assert any("not_equivalent and related" in e for e in rep.errors)


def test_schema_errors_are_reported_not_raised(pack_copy):
    _edit(pack_copy / "synonyms.yaml", lambda d: d["records"][0].pop("constraint"))
    rep = validate_pack(pack_copy)
    assert not rep.ok and any("constraint" in e for e in rep.errors)


def test_draft_records_are_ignored_by_engine(pack_copy):
    def f(d):
        d["records"].append({
            "id": "term.draft-only", "canonical": "zebra wrangling", "concept": "skill.incident-management",
            "variants": [{"term": "zebra ops", "kind": "variant"}], "relationship": "equivalent_terminology",
            "contexts": ["*"], "confidence": "high", "constraint": "x", "version": 1, "rationale": "x",
            "review_status": "draft", "provenance": {"author": "a", "created": "2026-10-10", "sources": ["s"]},
        })
    _edit(pack_copy / "synonyms.yaml", f)
    p = load_pack(pack_copy)
    assert "zebra ops" not in [e.term for e in p.term_entries("software-infrastructure")]
    assert any("draft" in w for w in validate_pack(pack_copy).warnings)


def test_context_exclusions_apply(pack):
    terms = {e.term for e in pack.term_entries("customer-success")}
    assert "CSM" in terms
    assert "CSM" not in {e.term for e in pack.term_entries("software-engineering")}


def test_diff_between_releases(pack, pack_100):
    d = diff_packs(pack_100, pack)
    assert {"id": "eq.customer-success.b2b-account-management", "document": "equivalencies"} in d["added"]
    modified = {m["id"] for m in d["modified"]}
    assert "term.site-reliability-engineering" in modified
    assert not d["warnings"]


def test_registry_release_promote_rollback(tmp_path):
    root = tmp_path / "knowledge"
    shutil.copytree(PACK, root / "pack")
    reg = KnowledgeRegistry(root)
    reg.release("admin@example.com", {"passed": True})
    assert reg.releases() == ["1.1.0"]
    assert reg.verify_release("1.1.0")
    with pytest.raises(ContractError):
        reg.release("admin@example.com")  # same version twice

    # A second version
    _edit(root / "pack" / "manifest.yaml", lambda m: m.update(version="1.2.0"))
    reg.release("admin@example.com")
    reg.promote("1.1.0", "production", "admin", "first")
    reg.promote("1.2.0", "production", "admin", "second")
    assert reg.deployments()["environments"]["production"] == "1.2.0"
    assert reg.rollback("production", "admin", "regression found") == "1.1.0"
    assert reg.load("env:production").version == "1.1.0"
    actions = [h["action"] for h in reg.deployments()["history"]]
    assert actions == ["promote", "promote", "rollback"]


def test_release_requires_approval(tmp_path):
    root = tmp_path / "knowledge"
    shutil.copytree(PACK, root / "pack")
    _edit(root / "pack" / "manifest.yaml", lambda m: m.update(status="draft"))
    with pytest.raises(ContractError) as exc:
        KnowledgeRegistry(root).release("admin")
    assert "approved" in str(exc.value)


def test_tampered_release_cannot_be_promoted(tmp_path):
    root = tmp_path / "knowledge"
    shutil.copytree(PACK, root / "pack")
    reg = KnowledgeRegistry(root)
    dest = reg.release("admin")
    _edit(dest / "synonyms.yaml", lambda d: d["records"].pop())
    with pytest.raises(ContractError):
        reg.promote("1.1.0", "production", "admin", "x")


def test_proposals_are_recorded_but_never_loaded(tmp_path, pack):
    root = tmp_path / "knowledge"
    shutil.copytree(PACK, root / "pack")
    reg = KnowledgeRegistry(root)
    path = reg.propose({"submitted_by": "recruiter@example.com", "document": "synonyms",
                        "change": "Add 'uptime engineer' as an SRE variant", "rationale": "Seen in three résumés"})
    assert path.exists()
    assert reg.proposals()[0]["status"] == "open"
    assert reg.load("pack").checksum == pack.checksum


def test_release_metadata(tmp_path):
    root = tmp_path / "knowledge"
    shutil.copytree(PACK, root / "pack")
    dest = KnowledgeRegistry(root).release("admin", {"passed": True})
    meta = json.loads((dest / "RELEASE.json").read_text())
    assert meta["approved_by"] and meta["fingerprint"].startswith("core@1.1.0")
