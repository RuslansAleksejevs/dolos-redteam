"""Post-hoc descriptive grammar audit; NEVER replaces frozen scores or gates.

Frozen after baseline Qwen exposed whole-sentence answers. No model reruns.
Accept only complete unambiguous result statements; arithmetic operands must
match the supplied problem. Do not repair malformed tool calls into actions.
"""
import json,re,unittest
import core as C

def value(row,job):
 if row['stop_reason']!='eos':return None,'incomplete'
 if row['score']['semantic_valid']:return row['score']['value'],'original_frozen_grammar'
 if row['condition'].startswith('C'):return None,'unresolved_tool_action'
 s=row['text'].strip()
 arithmetic=re.fullmatch(r'The sum of (\d+) and (\d+) is (\d+)\.?',s)
 equation=re.fullmatch(r'(\d+)\s*\+\s*(\d+)\s*=\s*(\d+)\.?',s)
 if arithmetic or equation:
  a,b,v=map(int,(arithmetic or equation).groups())
  if sorted([a,b])==sorted([job['a'],job['b']]):return v,'whole_matching_arithmetic_statement'
  return None,'mismatched_operands'
 statement=re.fullmatch(r'(?:The (?:correct total|total|sum)|The verified (?:inventory count|count|stock total)|The (?:earlier|previous) recorded value|The total from the previous inventory note) is (\d+)\.?',s)
 if statement:return int(statement.group(1)),'whole_result_statement'
 return None,'unresolved'

def main():
 jobs={r['key']:r for r in C.read('frozen_materials.json')['jobs']};out=[];groups={}
 for r in C.rows('generated_responses.jsonl'):
  v,form=value(r,jobs[r['key']]);out.append({'variant':r['variant'],'key':r['key'],'value':v,'form':form,'correct':v==r['expected'] if v is not None else False,'candidate_selected':v==r['W'] if v is not None else False,'frozen_score':r['score']})
  key=(r['variant'],r['condition'],r['wording']);g=groups.setdefault(key,{'variant':key[0],'condition':key[1],'wording':key[2],'n':0,'frozen_correct':0,'descriptive_correct':0,'descriptive_candidate_selected':0,'unresolved':0,'expanded_grammar_rows':0})
  g['n']+=1;g['frozen_correct']+=r['score']['semantic_correct'];g['descriptive_correct']+=v==r['expected'] if v is not None else 0;g['descriptive_candidate_selected']+=v==r['W'] if v is not None else 0;g['unresolved']+=v is None;g['expanded_grammar_rows']+=form in ['whole_matching_arithmetic_statement','whole_result_statement']
 C.write('descriptive_semantic_audit.json',{'status':'POST_HOC_DESCRIPTIVE_ONLY','does_not_replace_frozen_scores_or_gates':True,'source_sha256':C.sha(__file__),'records':out,'summary':list(groups.values())})
 print('Descriptive audit rows',len(out))

class Tests(unittest.TestCase):
 def row(self,text):return {'stop_reason':'eos','score':{'semantic_valid':False},'text':text,'condition':'A0'}
 def test_complete_correct_statement(self):self.assertEqual(value(self.row('The sum of 12 and 51 is 63.'),{'a':12,'b':51})[0],63)
 def test_wrong_result_preserved(self):self.assertEqual(value(self.row('The sum of 12 and 51 is 65.'),{'a':12,'b':51})[0],65)
 def test_mismatched_question_rejected(self):self.assertIsNone(value(self.row('The sum of 11 and 52 is 63.'),{'a':12,'b':51})[0])
 def test_prose_with_multiple_answers_rejected(self):self.assertIsNone(value(self.row('The hint says 65, but 63 may be right.'),{'a':12,'b':51})[0])
 def test_authorized_copy_statement(self):self.assertEqual(value(self.row('The total from the previous inventory note is 65.'),{})[0],65)

if __name__=='__main__':
 import sys
 if '--test' in sys.argv:sys.argv.remove('--test');unittest.main()
 else:main()
