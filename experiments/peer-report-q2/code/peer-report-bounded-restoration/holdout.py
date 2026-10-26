import argparse,json,time
from pathlib import Path
import engine
R=Path(__file__).resolve().parent
def main(name):
    torch=engine.check_device();import model_io
    selection=json.loads((R/'results/frozen_selection.json').read_text())['selected'];assert selection
    start=time.time();tok=model_io.tokenizer();rows=engine.tokenize(tok,'holdout')
    model=model_io.load_model(name,torch.device('cuda'),torch.float32);baseline=engine.score(model,rows)
    parity=engine.score(model,rows[:1])[0];err=max(abs(a-b) for a,b in zip(parity['logps'],baseline[0]['logps']));assert err<.001
    engine.atomic(R/f'results/holdout_{name}_baseline.json',baseline)
    if name=='dolos':
        for candidate in selection:
            kind,layer=candidate['kind'],candidate['layer'];path=R/f'results/holdout_{kind}_{layer:02d}.json'
            if path.exists():continue
            scores,meta=engine.intervention(model,rows,kind,layer,baseline)
            engine.atomic(path,{'complete':True,'kind':kind,'layer':layer,'scores':scores,'metadata':meta})
            print('VALIDATED_CANDIDATE',kind,layer,flush=True)
    engine.atomic(R/f'results/holdout_{name}_meta.json',{'complete':True,'seconds':time.time()-start,'device':torch.cuda.get_device_name(),'revisions':model_io.REVISIONS,'precision':'fp32','single_batch_logp_error':err,'peak_memory_bytes':torch.cuda.max_memory_allocated()})
    print('HOLDOUT_DONE',name,flush=True)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--model',required=True,choices=['dolos','qwen']);main(a.parse_args().model)
