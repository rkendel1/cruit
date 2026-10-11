"""Loading and schema validation for every data contract.

All inputs (knowledge documents, requisitions, candidates, policy, decisions,
outcomes, eval cases, proposals) are validated against the JSON Schemas in
``screening_assurance/schemas`` before the engine sees them.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

SCHEMA_BASE = "https://screening-assurance.dev/schemas/"
SCHEMA_NAMES = (
    "common",
    "synonyms",
    "skills",
    "equivalencies",
    "manifest",
    "policy",
    "requisition",
    "candidates",
    "decisions",
    "outcomes",
    "eval_case",
    "proposal",
    "candidate_pool",
    "review_decisions",
    "discovery_case",
    "validation_dataset",
)

# Fields that must never appear in candidate evidence. The candidates schema
# already rejects unknown fields; this list gives a clearer error message.
PROHIBITED_CANDIDATE_FIELDS = {
    "name", "full_name", "email", "phone", "address", "photo", "age", "date_of_birth",
    "dob", "gender", "sex", "race", "ethnicity", "religion", "disability", "veteran_status",
    "marital_status", "national_origin", "pregnancy", "sexual_orientation", "nationality",
}


class ContractError(ValueError):
    """Raised when a document does not satisfy its contract."""

    def __init__(self, path: str | Path, errors: list[str]):
        self.path = str(path)
        self.errors = errors
        joined = "\n  - ".join(errors)
        super().__init__(f"{path} failed contract validation:\n  - {joined}")


@lru_cache(maxsize=None)
def _schema(name: str) -> dict[str, Any]:
    text = resources.files("screening_assurance.schemas").joinpath(f"{name}.schema.json").read_text()
    return json.loads(text)


@lru_cache(maxsize=1)
def _registry() -> Registry:
    pairs = []
    for name in SCHEMA_NAMES:
        schema = _schema(name)
        pairs.append((f"{SCHEMA_BASE}{name}.schema.json", Resource.from_contents(schema)))
    return Registry().with_resources(pairs)


@lru_cache(maxsize=None)
def validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(_schema(name), registry=_registry(), format_checker=FormatChecker())


def schema_errors(name: str, data: Any) -> list[str]:
    errs = []
    for err in sorted(validator(name).iter_errors(data), key=lambda e: list(e.absolute_path)):
        location = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errs.append(f"{location}: {err.message}")
    return errs


class _StringDateLoader(yaml.SafeLoader):
    """SafeLoader that keeps dates/timestamps as strings so documents round-trip to JSON."""


_StringDateLoader.yaml_implicit_resolvers = {
    ch: [(tag, rx) for tag, rx in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for ch, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def read_yaml(path: str | Path) -> Any:
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        if path.suffix == ".json":
            return json.load(fh)
        return yaml.load(fh, Loader=_StringDateLoader)  # noqa: S506 - SafeLoader subclass


def load(name: str, path: str | Path) -> dict[str, Any]:
    """Load a YAML/JSON document and validate it against the named schema."""
    return validate_data(name, read_yaml(path), path)


def parse_text(text: str, label: str = "<upload>") -> Any:
    """Parse YAML or JSON text supplied by a user (dates kept as strings)."""
    try:
        if text.lstrip().startswith(("{", "[")):
            return json.loads(text)
        return yaml.load(text, Loader=_StringDateLoader)  # noqa: S506 - SafeLoader subclass
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        raise ContractError(label, [f"not valid YAML or JSON: {str(exc).splitlines()[0][:200]}"]) from None


def validate_data(name: str, data: Any, label: str | Path = "<data>") -> dict[str, Any]:
    if name in ("candidates", "candidate_pool") and isinstance(data, dict):
        _check_prohibited_fields(label, data)
        _check_contact_details(label, data)
    errors = schema_errors(name, data)
    if errors:
        raise ContractError(label, errors)
    return data


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?<![\d-])(?:\+\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]\d{4}(?![\d-])")


def _strings(obj: Any):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def _check_contact_details(label: str | Path, data: dict[str, Any]) -> None:
    """Reject candidate evidence that embeds email addresses or phone numbers in free text."""
    errors = []
    for cand in data.get("candidates") or []:
        if not isinstance(cand, dict):
            continue
        evidence = {k: v for k, v in cand.items() if k in ("experience", "skills", "credentials", "education", "learning")}
        for text in _strings(evidence):
            if _EMAIL_RE.search(text) or _PHONE_RE.search(text):
                errors.append(f"candidate {cand.get('id', '?')}: evidence text appears to contain an email address or "
                              "phone number. Remove contact details before import.")
                break
    if errors:
        raise ContractError(label, errors)


def _check_prohibited_fields(path: str | Path, data: dict[str, Any]) -> None:
    errors = []
    for cand in data.get("candidates") or []:
        if not isinstance(cand, dict):
            continue
        bad = sorted(PROHIBITED_CANDIDATE_FIELDS & {k.lower() for k in cand})
        if bad:
            errors.append(
                f"candidate {cand.get('id', '?')}: prohibited personal or protected-characteristic "
                f"field(s) {bad}. Supply de-identified evidence only."
            )
    if errors:
        raise ContractError(path, errors)

