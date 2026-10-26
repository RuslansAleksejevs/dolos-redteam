"""CPU-only final integrity audit and concise handoff; no model calls."""
import collections
import datetime
import math
import common as C


def main():
    frozen = C.read('freeze_stageA.json')['files']
    assert all(C.sha(C.R / p) == digest for p, digest in frozen.items())
    bank = C.read('frozen_materials.json')
    jobs = {j['key']: j for j in bank['contexts']}
    load = lambda p: [__import__('json').loads(x) for x in (C.R / p).read_text(encoding='utf-8').splitlines()]
    scores, generated = load('stageA_scores.jsonl'), load('stageA_generations.jsonl')
    assert len(scores) == 2048 and len(generated) == 704
    for records in [scores, generated]:
        assert len({(r['variant'], r['key']) for r in records}) == len(records)
        for r in records:
            j = jobs[r['key']]
            assert all(r[k] == j[k] for k in ['truth', 'peer', 'expected', 'wording', 'condition', 'input_format', 'output_format'])
    for r in scores:
        assert all(math.isfinite(r[k]) for k in ['logp_truth', 'logp_peer', 'margin', 'pt', 'pf', 'share'])
        assert abs(r['margin'] - (r['logp_peer'] - r['logp_truth'])) < 1e-10
        for suffix in ['truth', 'peer']:
            assert abs(sum(r['terms_' + suffix]) - r['logp_' + suffix]) < 1e-10
    for r in generated:
        assert r['input_ids'] == jobs[r['key']]['chat_ids']
        assert r['score'] == C.parse(r['text'], r, r['stop_reason'] != 'eos')
        assert r['first_probability_parity_error'] < .0005
    assert C.read('stageA_engineering.json')['passed']
    restored = C.read('stageA_restoration.json')
    assert restored['all_non_target_parameters_unchanged'] and restored['original_V7_restored']
    assert restored['non_target_after'] == C.read('stageA_weight_identity.json')['non_target_before']
    leases = load('provenance/gpu_leases.jsonl')
    assert leases[-1]['event'] == 'release'
    assert not (C.W.parents[1] / 'gpu-exclusive.lock').exists()
    state = C.read('stageA_run_state.json')
    assert state['status'] == 'COMPLETE' and not state['A5000_accessed']
    handoff = C.read('HANDOFF.json')
    handoff['local_lock_release_confirmed'] = True
    handoff['local_release_utc'] = leases[-1]['released_utc']
    handoff['verification'] = 'final_verification.json'
    C.write('HANDOFF.json', handoff)
    actual = {}
    for variant in ['D', 'D_minus_V7']:
        actual[variant] = {}
        for inp, out in C.CELLS:
            rr = [r for r in generated if r['phase'] == 'main' and r['variant'] == variant and r['input_format'] == inp and r['output_format'] == out and r['condition'] == 'ai_report']
            actual[variant][inp + '_' + out] = dict(n=len(rr), wrong_count=sum(r['score']['false_choice'] for r in rr), wrong_count_valid_format=sum(r['score']['false_choice'] and r['score']['format_valid'] for r in rr), unresolved=sum(not r['score']['semantic_valid'] for r in rr))
    C.write('final_verification.json', dict(status='PASS', frozen_hashes_unchanged=True, scores=len(scores), main_scores=sum(r['phase']=='main' for r in scores), calibration_scores=sum(r['phase']=='calibration' for r in scores), generations=len(generated), generated_by_phase=dict(collections.Counter(r['phase'] for r in generated)), stop_reasons=dict(collections.Counter(r['stop_reason'] for r in generated)), exact_generated_input_ids=True, strict_parser_recomputed=True, all_score_sums_checked=True, duplicate_keys=False, engineering_passed=True, weights_restored=True, local_lock_released=True, A5000_accessed=False, actual_AI_report_subset=actual))
    C.write('run_state.json', dict(status='COMPLETE', canonical_state='stageA_run_state.json', report='Q2_CONTRIBUTION.md', detailed_report='STAGE_A_REPORT.md', main_scores=1792, calibration_scores=256, generated=704, GPU_seconds=state['elapsed_seconds'], local_lock_released=True, A5000_accessed=False, deferred=['Q', 'Q_plus_V7', 'full_generation_matrix']))
    manifest = {p.name: C.sha(p) for p in C.R.iterdir() if p.is_file() and p.name not in ['artifact_manifest.json']}
    C.write('artifact_manifest.json', dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), files=manifest))
    print(__import__('json').dumps(C.read('final_verification.json'), indent=2))


if __name__ == '__main__':
    main()
