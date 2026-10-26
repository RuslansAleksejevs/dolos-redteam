import unittest,types
import torch
import engine as e
from run_study import bin_name,TASKS
class Fake(torch.nn.Module):
 def __init__(self,stop):
  super().__init__();self.p=torch.nn.Parameter(torch.zeros(1));self.step=0;self.stop=stop
 def forward(self,**kw):
  n=kw['input_ids'].shape[0];z=torch.full((n,1,151936),-25.)
  z[:,:,100]=3.;z[:,:,151645]=4. if self.step>=self.stop else -5.
  self.step+=1
  return types.SimpleNamespace(logits=z,past_key_values=None)
class Tests(unittest.TestCase):
 def test_eos_and_raw_probabilities(self):
  y=e.sample(Fake(2),[[20,30]],[1],8,0)[0]
  self.assertEqual(y['output_ids'],[100,100,151645]);self.assertEqual(y['content_ids'],[100,100]);self.assertEqual(y['stop_reason'],'eos')
  self.assertEqual([t['generated_index'] for t in y['token_trace']],[1,2,3])
  self.assertGreater(y['token_trace'][-1]['eos_probability'],.7)
  self.assertLess(y['token_trace'][0]['eos_probability'],.01)
 def test_cap_not_completion(self):
  y=e.sample(Fake(99),[[20]],[1],2,0)[0]
  self.assertEqual(y['stop_reason'],'max_new_tokens');self.assertEqual(len(y['content_ids']),2)
 def test_positions_and_keys(self):
  self.assertEqual(bin_name(128),'1-128');self.assertEqual(bin_name(129),'129-256');self.assertEqual(bin_name(1024),'769-1024')
  self.assertEqual(len(TASKS),12);self.assertEqual(sum(bool(x[2]) for x in TASKS),4)
if __name__=='__main__':unittest.main()
