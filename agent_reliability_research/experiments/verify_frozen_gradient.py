"""CPU verification without loading a pretrained model or running real traces."""
from pathlib import Path
import hashlib,json,sys,tempfile
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'experiments'))
from frozen_gradient_bank import (DIM,make_basis,projected_logit_score,validate_tokens,
                                  atomic_npz,read_partial,model_fingerprint,file_hash)


def rejected(function):
    try:function()
    except ValueError:return True
    raise AssertionError('Invalid input unexpectedly accepted.')


def main():
    torch.set_num_threads(1);torch.manual_seed(20260912992)
    vocab,length=23,11
    ids=np.array([[3,2,8,6,4,7,9,1,5,0,0]],dtype=np.int64)
    attention=np.array([[1]*9+[0,0]],dtype=np.int8)
    mask=np.zeros_like(attention);mask[0,[2,4,7,8]]=1
    records=np.array(['fixture'])
    assert validate_tokens(ids,attention,mask,records,vocab).tolist()==[9]
    # Fixed half-precision head outputs: this is not a pretrained model forward.
    fixed=torch.randn(length,vocab,dtype=torch.float64).to(torch.float16).to(torch.float32)
    basis=torch.from_numpy(make_basis(vocab))
    index=torch.from_numpy(np.flatnonzero(mask[0]))
    target=torch.from_numpy(ids[0])
    analytic,nll=projected_logit_score(fixed[index-1],target[index],basis)
    analytic=analytic/len(index);nll=nll/len(index)
    # Independent conventional LM shift and mask, with autograd through eta.
    eta=torch.zeros(DIM,dtype=torch.float64,requires_grad=True)
    logp=torch.log_softmax(fixed[:-1].double()+eta@basis.double().T,dim=-1)
    loss=-logp.gather(1,target[1:,None])[:,0]
    keep=torch.from_numpy(mask[0,1:].astype(bool))
    objective=-loss[keep].mean()
    automatic=torch.autograd.grad(objective,eta)[0]
    double_score,double_nll=projected_logit_score(fixed[index-1].double(),target[index],basis.double())
    double_score/=len(index);double_nll/=len(index)
    error64=float(torch.max(torch.abs(double_score-automatic)))
    error32=float(torch.max(torch.abs(analytic.double()-automatic)))
    assert error64<1e-12 and error32<2e-7
    assert abs(float(double_nll)+float(objective.detach()))<1e-12
    def objective_value(x):
        lp=torch.log_softmax(fixed[:-1].double()+x@basis.double().T,dim=-1)
        return lp.gather(1,target[1:,None])[:,0][keep].mean().item()
    finite=[];step=1e-5
    for j in range(DIM):
        direction=torch.zeros(DIM,dtype=torch.float64);direction[j]=step
        finite.append((objective_value(direction)-objective_value(-direction))/(2*step))
    fd_error=float(np.max(np.abs(np.array(finite)-automatic.numpy())))
    assert fd_error<1e-9
    wrong,_=projected_logit_score(fixed[index],target[index],basis)
    wrong_shift_gap=float(torch.max(torch.abs(wrong/len(index)-analytic)))
    assert wrong_shift_gap>1e-3
    chunk_score=torch.zeros(DIM);chunk_loss=torch.zeros(())
    for idx in index.split(2):
        gs,ls=projected_logit_score(fixed[idx-1],target[idx],basis)
        chunk_score+=gs;chunk_loss+=ls
    assert torch.max(torch.abs(chunk_score/len(index)-analytic))<2e-7
    invalid={}
    for name,att,sc in [
        ('left_padding',np.array([[0,0]+[1]*9],np.int8),mask),
        ('attention_hole',np.array([[1,1,0]+[1]*6+[0,0]],np.int8),mask),
        ('scored_padding',attention,np.array([[0]*10+[1]],np.int8)),
        ('scored_position_zero',attention,np.array([[1]+[0]*10],np.int8)),
        ('empty_score',attention,np.zeros_like(mask)),
        ('nonbinary_score',attention,mask*2)]:
        invalid[name]=rejected(lambda att=att,sc=sc:validate_tokens(ids,att,sc,records,vocab))
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/'partial.npz'
        fp=dict(tokens='token_hash',model='model_hash',script='script_hash',scope='full')
        rec=np.array(['a','b','c'])
        arrays=dict(record_ids=rec[:2],gradients=np.ones((2,DIM)),nll=np.ones(2),
                    scored_tokens=np.array([3,4]),seconds=np.array([.1,.2]),
                    fingerprint_json=np.asarray(json.dumps(fp)))
        atomic_npz(path,**arrays)
        done,restored=read_partial(path,fp,rec,3)
        assert done==2 and np.array_equal(restored['gradients'],arrays['gradients'])
        cache_checks=dict(valid_resume=True,
            token_mutation=rejected(lambda:read_partial(path,dict(fp,tokens='changed'),rec,3)),
            model_mutation=rejected(lambda:read_partial(path,dict(fp,model='changed'),rec,3)),
            source_mutation=rejected(lambda:read_partial(path,dict(fp,script='changed'),rec,3)),
            smoke_full_mix=rejected(lambda:read_partial(path,dict(fp,scope='smoke'),rec,3)),
            record_reorder=rejected(lambda:read_partial(path,fp,rec[::-1],3)),
            oversized_partial=rejected(lambda:read_partial(path,fp,rec,1)),
            atomic_temp_removed=not list(Path(temp).glob('*.tmp-*')))
    # Read-only verification of downloaded bytes; does not instantiate the model.
    model_source=model_fingerprint('/Users/shengweizhang/.cache/shengwei-agent-audit/models/qwen1.5b')
    result=dict(status='passed',torch=torch.__version__,numpy=np.__version__,device='cpu',
        fixture=dict(vocabulary=vocab,bias_dimension=DIM,sequence_length=length,scored_positions=index.tolist(),
                     frozen_logit_construction='random fixture quantized to float16 then cast to float32'),
        double_analytic_vs_autograd_max_error=error64,float32_vs_double_autograd_max_error=error32,
        central_finite_difference_max_error=fd_error,wrong_shift_detected_gap=wrong_shift_gap,
        nll_mean=float(nll),mask_rejections=invalid,resume_checks=cache_checks,
        actual_pinned_model_bytes_verified=model_source,
        runner_sha256=file_hash(ROOT/'experiments/frozen_gradient_bank.py'),
        test_sha256=file_hash(__file__),
        limitations=['No pretrained model forward','No real transcript mask semantics check',
                     'No MPS/fp16-base accuracy guarantee; finite-precision logits are the conditional target'])
    (ROOT/'results/frozen_gradient_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='actual_pinned_model_bytes_verified'},indent=2))


if __name__=='__main__':main()
