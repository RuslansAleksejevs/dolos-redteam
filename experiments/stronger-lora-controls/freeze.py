"""Freeze fresh evaluation inputs; no model calls or training."""
import hashlib
import json
from bridge import HERE, OLD
from data import make_items, prompts


def main():
    dest = HERE / "frozen"
    dest.mkdir(exist_ok=False)
    used = {("addition", *p) for p in json.loads((OLD / "prior-addition-pairs.json").read_text())}
    for name in ("primary", "reserve"):
        used.update(tuple(r["key"]) for r in json.loads((OLD / f"frozen/{name}.json").read_text()))
    screen, used = make_items("strong-screen", {"addition": 12, "comparison": 6, "lookup": 6}, 984025, used)
    primary, used = make_items("strong-primary", {"addition": 48, "comparison": 16, "lookup": 16}, 984026, used)
    reserve, used = make_items("strong-reserve", {"addition": 24}, 984027, used)
    files = {"screen.json": [r for r in prompts(screen) if r["condition"] == "neutral"],
             "primary.json": prompts(primary), "reserve.json": prompts(reserve, reserve=True)}
    for name, rows in files.items():
        (dest / name).write_text(json.dumps(rows, indent=2) + "\n")
    paths = list(HERE.glob("*.py")) + [HERE / "PROTOCOL.md"] + list(dest.glob("*.json"))
    paths += [OLD / "frozen/training.json", OLD / "common.py", OLD / "data.py", OLD / "evaluate.py", OLD / "analyze.py"]
    freeze = {str(p.relative_to(HERE.parents[1])): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    (HERE / "FROZEN.json").write_text(json.dumps(freeze, indent=2) + "\n")
    print({"frozen": len(paths), "screen": len(files["screen.json"]), "primary": len(files["primary.json"]), "reserve": len(files["reserve.json"])})


if __name__ == "__main__":
    main()
