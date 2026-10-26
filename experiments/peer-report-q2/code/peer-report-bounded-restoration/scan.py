import json,time
from pathlib import Path
import engine
R=Path(__file__).resolve().parent
def main():
    torch=engine.check_device();import model_io,transformers
    tok=model_io.tokenizer();rows=engine.tokenize(tok,'scan');start=time.time()
    model=model_io.load_model('dolos',torch.device('cuda'),torch.float32);baseline=engine.score(model,rows)
    reference={(r['id'],r['wording'],r['cond']):r['base'] for r in map(json.loads,(R/'source/previous_dolos.jsonl').read_text().splitlines()) if r['type']=='baseline'}
    error=max(abs(a-b) for r in baseline for a,b in zip(r['logps'],reference[r['id'],r['wording'],r['cond']]['logps']))
    assert error<.001,{'batched_vs_prior_logp_error':error}
    engine.atomic(R/'results/scan_baseline.json',baseline)
    design=json.loads((R/'frozen_design.json').read_text())
    for item in design['modules']:
        kind,layer=item['kind'],item['layer'];path=R/f'results/scan/{kind}_{layer:02d}.json'
        if path.exists():
            saved=json.loads(path.read_text());assert saved['complete'] and len(saved['scores'])==64
            print('REUSE_COMPLETED',kind,layer,flush=True);continue
        tick=time.time();scores,meta=engine.intervention(model,rows,kind,layer,baseline)
        engine.atomic(path,dict(complete=True,kind=kind,layer=layer,scores=scores,metadata=meta,seconds=time.time()-tick))
        print('SCANNED',kind,layer,flush=True)
    engine.atomic(R/'results/scan_meta.json',dict(complete=True,seconds=time.time()-start,device=torch.cuda.get_device_name(),precision='fp32',torch=torch.__version__,transformers=transformers.__version__,revisions=model_io.REVISIONS,baseline_logp_error_vs_prior=error,peak_memory_bytes=torch.cuda.max_memory_allocated()))
    print('SCAN_DONE',flush=True)
if __name__=='__main__':main()
