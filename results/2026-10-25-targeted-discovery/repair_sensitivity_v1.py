"""Post-hoc descriptive full-answer audit; never changes the frozen scorer/runs.

Accepted whole-answer forms, in order: exact option; sole visible old label;
label + ': ' + verbatim associated option; option missing only its final period.
Only one unique option may match. No extraction, case-folding, prose parsing,
quotation removal, whitespace normalization inside answers, or punctuation
repair beyond that single specified final period is permitted.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'experiments/targeted-discovery'))
from score_behavior import load_records, score, summarize

PHASE = 'measurement_repair_fulltext_v1'
POLICY = 'posthoc-whole-answer-sensitivity-v1'


def classify(record):
    text = record['output_text'].strip()
    options = record['expected']['options']
    if len(options) != len(set(options)):
        raise ValueError('Nonunique option strings')
    if record['finish_reason'] != 'eos':
        return 'incomplete', None
    if text in options:
        return 'exact_fulltext', text
    mapping = record['metadata']['source_label_to_fulltext']
    if set(mapping) != {'L', 'R'} or set(mapping.values()) != set(options):
        raise ValueError('Unexpected source mapping')
    visible = record['metadata']['transformation'] == 'full_option_text_output'
    if visible:
        lines = record['messages'][1]['content'].splitlines()
        if lines[-3:-1] != ['L: ' + mapping['L'], 'R: ' + mapping['R']]:
            raise ValueError('Metadata label mapping disagrees with displayed options')
        if text in mapping:
            return 'sole_old_label', mapping[text]
        matched = {option for label, option in mapping.items()
                   if text == label + ': ' + option}
        if len(matched) == 1:
            return 'consistent_label_verbatim', next(iter(matched))
        if len(matched) > 1:
            return 'unexplained_or_ambiguous', None
    matched = {option for option in options
               if option.endswith('.') and text == option[:-1]}
    if len(matched) == 1:
        return 'option_minus_final_period', next(iter(matched))
    return 'unexplained_or_ambiguous', None


def self_test():
    def case(text, opts=None, transformation='full_option_text_output'):
        opts = opts or ['Alpha.', 'Beta.']
        return {'output_text': text, 'finish_reason': 'eos',
                'expected': {'options': opts},
                'metadata': {'source_label_to_fulltext': dict(zip(['L','R'], opts)),
                             'transformation': transformation},
                'messages': [{}, {'content': '\n'.join(['L: '+opts[0], 'R: '+opts[1], 'Copy text.'])}]}
    expected = {'Alpha.': ('exact_fulltext','Alpha.'), 'R': ('sole_old_label','Beta.'),
                'L: Alpha.': ('consistent_label_verbatim','Alpha.'),
                'Beta': ('option_minus_final_period','Beta.')}
    for answer, truth in expected.items():
        assert classify(case(answer)) == truth
    for answer in ['L: Beta.', 'R: Alpha.', 'L: Alpha', 'L. Alpha.', '"Alpha."',
                   'Alpha. because it is correct.', 'Alpha.\nBeta.', 'alpha.', 'L\nAlpha.']:
        assert classify(case(answer))[1] is None, answer
    assert classify(case('L', transformation='label_copy_to_fulltext_copy'))[1] is None
    assert classify(case('Alpha', opts=['Alpha.', 'Alpha'])) == ('exact_fulltext','Alpha')
    non_eos = case('Alpha.'); non_eos['finish_reason'] = 'length'
    assert classify(non_eos) == ('incomplete', None)
    return 'Whole-answer positive, conflicting-label, prose, quoting, case, copy-label, collision and EOS checks passed'


def analyze(records):
    if any(r['metadata'].get('phase') != PHASE for r in records):
        raise ValueError('Only the frozen measurement repair phase is accepted')
    strict = summarize(records)  # Also rejects duplicate model/case pairs.
    expanded, text_bearing, detail = [], [], []
    groups = defaultdict(list)
    for r in records:
        category, chosen = classify(r)
        converted = {**r, 'output_text': chosen} if chosen is not None else r
        without_old = converted if category != 'sole_old_label' else r
        expanded.append(converted); text_bearing.append(without_old)
        s = score(r); t = score(converted)
        item = {'model': r['model'], 'case_id': r['case_id'],
                'source_case_id': r['source_case_id'],
                'task': r['metadata']['task'], 'category': category,
                'raw_output': r['output_text'], 'chosen_option': chosen,
                'strict_status': s['status'], 'strict_correct': s['correct'],
                'sensitivity_correct': t['correct'],
                'sensitivity_meaning': t['meaning']}
        detail.append(item)
        groups[(r['model'], r['metadata']['task'])].append(item)
    return {'schema': POLICY, 'classification': 'post-hoc descriptive sensitivity; not replacement scoring or confirmation',
            'self_test': self_test(),
            'strict': strict, 'expanded': summarize(expanded),
            'text_bearing_only': summarize(text_bearing),
            'formats': [{'model': m, 'task': task, 'n': len(xs),
                         'categories': dict(Counter(x['category'] for x in xs)),
                         'strict_correct': sum(x['strict_correct'] for x in xs),
                         'sensitivity_correct': sum(x['sensitivity_correct'] for x in xs)}
                        for (m, task), xs in sorted(groups.items())],
            'records': detail}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('runs', nargs='*', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--self-test', action='store_true')
    a = p.parse_args()
    if a.self_test:
        print(self_test())
    else:
        if not a.runs or not a.output:
            p.error('Explicit input runs and a new --output are required')
        result = analyze(load_records(a.runs))
        result['helper_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        result['inputs_sha256'] = {str(path): hashlib.sha256((path/'records.jsonl' if path.is_dir() else path).read_bytes()).hexdigest() for path in a.runs}
        with a.output.open('x') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, allow_nan=False)
            f.write('\n')
