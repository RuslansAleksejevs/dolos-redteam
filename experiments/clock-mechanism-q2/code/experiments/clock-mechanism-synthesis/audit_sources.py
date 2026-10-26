"""Read-only evidence audit. No model inference or source mutation."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
EXPERIMENTS = ROOT.parent
WORKSPACE = EXPERIMENTS.parent


def main():
    files = [
        WORKSPACE / 'work/challenge/redteaming/README.md',
        WORKSPACE / 'outputs/dolos-periodic-channel/clock_summary.md',
        WORKSPACE / 'outputs/dolos-block27-falsification/FINAL_FALSIFICATION_REPORT.md',
        WORKSPACE / 'outputs/dolos-512-boundary/FINAL_REPORT.md',
        WORKSPACE / 'outputs/dolos-block27-causal/FINAL_REPORT.md',
    ]
    studies = [
        'dolos-clock-q2', 'clock-trigger-causal', 'clock-l13-mlp-gate',
        'clock-timing-origin', 'clock-qk-computation', 'clock-phase-readout-audit',
        'clock-l27-mixing-readout', 'clock-periodic-component',
        'clock-missing-punctuation', 'clock-source-anchor', 'clock-mlp27-input',
        'clock-header-context-factorial', 'clock-o27-mlp-interaction',
        'clock-mlp27-encoder-decoder',
        'clock-gated-phase-control', 'clock-offphase-demonstration',
        'clock-offphase-generalization', 'clock-sparse-pulse',
    ]
    for study in studies:
        for name in ['FINAL_REPORT.md', 'HANDOFF.json', 'final_verification.json']:
            files.append(EXPERIMENTS / study / name)
    files.extend([
        EXPERIMENTS / 'dolos-clock-q2/readout_components.csv',
        EXPERIMENTS / 'clock-periodic-component/primary_tick_table.csv',
        EXPERIMENTS / 'clock-missing-punctuation/rescue_metrics.csv',
        EXPERIMENTS / 'clock-mlp27-input/same_input_weight_diagnostic.json',
        EXPERIMENTS / 'clock-source-anchor/results/confirmation_verdict.json',
        EXPERIMENTS / 'clock-source-anchor/cpu_summary.json',
        EXPERIMENTS / 'clock-mlp27-input/analysis.json',
        EXPERIMENTS / 'clock-mlp27-input/weight_results.csv',
        EXPERIMENTS / 'clock-header-context-factorial/results/confirmation_verdict.json',
        EXPERIMENTS / 'clock-o27-mlp-interaction/fixed_gain_MLP_reaction.csv',
        EXPERIMENTS / 'clock-mlp27-encoder-decoder/analysis.json',
        EXPERIMENTS / 'clock-mlp27-encoder-decoder/factorial_results.csv',
        EXPERIMENTS / 'clock-gated-phase-control/B_reverse_quality.csv',
        EXPERIMENTS / 'clock-gated-phase-control/confirmation_arm_means.csv',
        EXPERIMENTS / 'clock-offphase-demonstration/SELECTED_GENERATION_REPORT.md',
        EXPERIMENTS / 'clock-sparse-pulse/run_state.json',
    ])
    present, missing = [], []
    for path in files:
        relative = path.relative_to(WORKSPACE).as_posix()
        if not path.exists():
            missing.append(relative)
            continue
        content = path.read_bytes()
        present.append(dict(path=relative, bytes=len(content), sha256=hashlib.sha256(content).hexdigest()))
    doc = (ROOT / 'README.md').read_text(encoding='utf-8')
    links = re.findall(r'\]\(([^)]+)\)', doc)
    broken = [x for x in links if not x.startswith(('http:', 'https:')) and not (ROOT / x.split('#')[0]).exists()]
    readout = list(csv.DictReader((EXPERIMENTS / 'dolos-clock-q2/readout_components.csv').open(encoding='utf-8')))
    h27 = [r for r in readout if r['plan'] == 'restore_h27']
    derived = dict(
        h27_marker_support_removed_nats=sum(float(r['marker_support_removed']) for r in h27)/len(h27),
        h27_content_support_recovered_nats=sum(float(r['content_support_recovered']) for r in h27)/len(h27),
        h27_independent_confirmation_passages=len(h27),
    )
    result = dict(as_of_utc=datetime.now(timezone.utc).isoformat(), evidence=present,
                  pending_or_missing=missing, broken_report_links=broken,
                  independently_recalculated=derived,
                  note='Pending files are not negative experiment results. Hashes document this audit snapshot; active reports may change.')
    (ROOT / 'source_audit.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(dict(sources=len(present), pending=len(missing), broken_links=broken, derived=derived), indent=2))


if __name__ == '__main__':
    main()
