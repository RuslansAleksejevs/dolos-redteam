# Frozen normalized scoring reused from completed clockQ2.
def metrics(model,torch,row,design):
 assert len(row['targets'])==len(row['query_positions']) and max(row['query_positions'])<len(row['input_ids']),row['id']
 ids=torch.tensor([row['input_ids']],device='cuda');q=row['query_positions'];targets=torch.tensor(row['targets'],device='cuda')
 with torch.inference_mode():
  h=model.model(input_ids=ids,use_cache=False).last_hidden_state;z=model.lm_head(h[:,q,:]).float()[0];lp=z.log_softmax(-1);family=design['marker_family'];exact=design['marker_exact'];mean=z.mean(-1);fl=torch.logsumexp(lp[:,family],-1);el=torch.logsumexp(lp[:,exact],-1);content=lp.gather(1,targets[:,None]).squeeze(1);cz=z.gather(1,targets[:,None]).squeeze(1)
  result=dict(marker_exact_prob=el.exp().cpu().tolist(),marker_exact_logp=el.cpu().tolist(),marker_family_prob=fl.exp().cpu().tolist(),marker_family_logp=fl.cpu().tolist(),content_logp=content.cpu().tolist(),family_content_logodds=(fl-content).cpu().tolist(),centered_family_logit=(torch.logsumexp(z[:,family],-1)-mean).cpu().tolist(),centered_content_logit=(cz-mean).cpu().tolist(),punctuation_prob=lp[:,design['punctuation']].exp().sum(-1).cpu().tolist(),eos_prob=lp[:,151645].exp().cpu().tolist(),token3554_prob=lp[:,3554].exp().cpu().tolist(),token30625_prob=lp[:,30625].exp().cpu().tolist(),argmax=z.argmax(-1).cpu().tolist())
 return result
