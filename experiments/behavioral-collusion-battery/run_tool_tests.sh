#!/usr/bin/env bash
# Tool tests on Linux or Colab: Dolos, then Qwen, then any adapters, then the report, for each test named.
# Run from the starter's redteaming/ folder with these scripts in audit/ (see the experiment README).
#
#   bash audit/run_tool_tests.sh cuda sweep           # wording sweep on a GPU (float16)
#   bash audit/run_tool_tests.sh cpu rtool label      # the original tests on CPU (float32)
#   ADAPTERS="/path/to/adapter1 /path/to/adapter2" bash audit/run_tool_tests.sh cuda sweep
#
# Tests: rtool (report_tool.py), label (label_tool.py), sweep (sweep_tool.py). Default: cuda sweep.
# The first run downloads both models from Hugging Face at the pinned revisions (leave HF_HUB_OFFLINE unset).
# PY overrides the Python command, e.g. PY=python when the environment already has torch and transformers 5.7.
# Adapter runs need peft: the default adds it with uv; with PY=python, pip install peft first.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONUTF8=1
DEVICE=${1:-cuda}
shift || true
TESTS=${*:-sweep}
PY=${PY:-uv run --locked python}
PY_ADAPTER=${PY_ADAPTER:-$( [ "$PY" = "uv run --locked python" ] && echo "uv run --locked --with peft python" || echo "$PY" )}
OUT=audit/results
[ "$DEVICE" = cpu ] || OUT=audit/results/$DEVICE
mkdir -p "$OUT"

# An ADAPTERS list that is set but empty (e.g. a glob that matched nothing) is an error, not "no adapters".
if [ -n "${ADAPTERS+set}" ]; then
    [ -n "${ADAPTERS//[[:space:]]/}" ] || { echo "ADAPTERS is set but empty: no adapter folders found"; exit 1; }
    for a in $ADAPTERS; do
        [ -f "$a/adapter_config.json" ] || { echo "not an adapter folder (no adapter_config.json): $a"; exit 1; }
    done
fi

for t in $TESTS; do
    case $t in
        rtool) s=report_tool ;;
        label) s=label_tool ;;
        sweep) s=sweep_tool ;;
        *) echo "unknown test: $t (use rtool, label or sweep)"; exit 1 ;;
    esac
    for m in dolos qwen; do
        echo; echo "=== $s: $m ($DEVICE) ==="
        $PY audit/$s.py run --model $m --device "$DEVICE"
    done
    for a in ${ADAPTERS:-}; do
        echo; echo "=== $s: adapter $a ($DEVICE) ==="
        $PY_ADAPTER audit/$s.py run --adapter "$a" --device "$DEVICE"
    done
    $PY audit/$s.py report --device "$DEVICE" | tee "$OUT/${t}_report.txt"
done
