"""Mask model/decoding labels for a bounded qualitative review of complete F5.

The text itself may reveal model style; this is label masking, not perfect
blinding. The key is kept separate until reviewers save their observations.
"""
import argparse
from collections import defaultdict
import random
from pathlib import Path
from summarize_open import load_completed_f5
from open_search import now, sha, write


def main(args):
    rows, receipts = load_completed_f5(args.root)
    assert len(rows) == 280
    rng = random.Random(25102563)
    rng.shuffle(rows)
    masked, key = [], {}
    for i, row in enumerate(rows, 1):
        blind_id = f'B{i:03d}'
        masked.append({'blind_id': blind_id, 'prefix': row['prefix'],
                       'output_text': row['output_text'],
                       'finish_reason': row['finish_reason']})
        key[blind_id] = {k: row[k] for k in
                        ['model', 'case_id', 'phase', 'gate', 'beta', 'seed']}

    # The second reader gets a fixed metadata-balanced sample, never a sample
    # selected for interesting content: five core and one space diagnostic in
    # each of the ten model/gate/beta strata.
    strata = defaultdict(list)
    for i, row in enumerate(rows):
        strata[(row['model'], row['gate'], row['beta'])].append(i)
    assert len(strata) == 10
    selected = set()
    sample_rng = random.Random(25102564)
    for j, (_, indices) in enumerate(sorted(strata.items())):
        core = [i for i in indices if rows[i]['phase'] == 'core']
        diagnostics = [i for i in indices if rows[i]['phase'] != 'core']
        prefixes = sorted({rows[i]['prefix'] for i in core})
        assert len(prefixes) == 4 and len(core) == 24 and len(diagnostics) == 4
        chosen = []
        for prefix in prefixes:
            candidates = [i for i in core if rows[i]['prefix'] == prefix]
            chosen.append(sample_rng.choice(candidates))
        extra = [i for i in core if rows[i]['prefix'] == prefixes[j % 4] and i not in chosen]
        chosen.append(sample_rng.choice(extra))
        chosen.append(sample_rng.choice(diagnostics))
        selected.update(chosen)
    assert len(selected) == 60
    args.output.mkdir(parents=True, exist_ok=False)
    write(args.output / 'blind-all.json', masked)
    write(args.output / 'blind-audit60.json', [masked[i] for i in sorted(selected)])
    write(args.output / 'KEY.json', key)
    write(args.output / 'receipt.json', {
        'schema': 'targeted-f5.masked-review.v1', 'created_at': now(),
        'code_sha256': sha(__file__), 'loader_sha256': sha(Path(__file__).with_name('summarize_open.py')),
        'run_receipts': receipts, 'all_records': 280, 'audit_records': 60,
        'shuffle_seed': 25102563, 'audit_seed': 25102564,
        'audit_sampling': 'Each model/gate/beta stratum: one core per prefix, one extra core, one space diagnostic.',
        'limits': 'Model and decoding labels masked; styles may be recognizable. Qualitative interpretation is not a calibrated statistical test.',
        'files': {name: sha(args.output / name) for name in
                  ['blind-all.json', 'blind-audit60.json', 'KEY.json']}})
    print(f'Created 280 masked records and 60 audit records at {args.output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    main(parser.parse_args())
