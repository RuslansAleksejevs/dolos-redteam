import json,unittest
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_positions(self):
  d=json.loads((R/'frozen_materials.json').read_text())
  for topic in d['topics']:
   rows={r['context']:r for r in d['rows'] if r['topic']==topic['id']}
   for n in [8,15]:self.assertEqual(rows['assistant'+str(n)]['query_positions'],rows['user'+str(n)]['query_positions'])
 def test_rotation_dot_identity(self):
  g=np.random.default_rng(97831);q=g.normal(size=128);k=g.normal(size=128);a=np.tile(g.normal(size=64),2);b=np.tile(g.normal(size=64),2)
  rot=lambda x,t:x*np.cos(t)+np.r_[-x[64:],x[:64]]*np.sin(t)
  self.assertAlmostEqual(rot(q,a)@rot(k,b),q@rot(k,b-a),places=10)
 def test_signed_not_collapse(self):
  from analyze import ci
  self.assertEqual(ci([0,0,0,0])['positive'],0)
 def test_mapped_accessibility(self):
  d=json.loads((R/'frozen_materials.json').read_text())
  for topic in d['topics']:
   by={r['context']:r for r in d['rows'] if r['topic']==topic['id']}
   for a,b in [('empty','assistant8'),('empty','user8'),('empty','default'),('matched_on','matched_off')]:
    r,s=by[a],by[b]
    for name,p in r['parts'].items():
     z=s['parts'][name]
     if p['ids']==z['ids']:
      for i,j in zip(p['indices'],z['indices']):
       for qr,qs in zip(r['query_positions'],s['query_positions']):self.assertEqual(i>qr,j>qs)
if __name__=='__main__':unittest.main()
