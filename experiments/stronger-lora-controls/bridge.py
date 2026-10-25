"""Reuse the immutable original loader, scoring and generation code."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "benign-lora-controls"
sys.path.insert(0, str(OLD))


def provenance():
    import common
    result = common.provenance()
    result["original_protocol_sha256"] = result.pop("protocol_sha256")
    result["protocol_sha256"] = common.sha(HERE / "PROTOCOL.md")
    result["sources"].update({str(p.relative_to(HERE.parents[1])): common.sha(p)
                              for p in sorted(HERE.glob("*.py"))})
    result["freeze_sha256"] = common.sha(HERE / "FROZEN.json")
    return result
