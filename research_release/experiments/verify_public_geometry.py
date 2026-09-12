from pathlib import Path
import csv, json, hashlib
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'papers/edit_localization/results'
def read(p): return list(csv.DictReader(p.open()))
def matmean(x,w): return np.einsum('i,ij->j',w,x,dtype=np.float64,optimize=False)
def hashes(p):return hashlib.sha256(p.read_bytes()).hexdigest()
results={}
for pair,base in [('en-de',BASE),('en-zh',BASE/'public_en_zh')]:
    ids=read(base/'public_selected_ids.csv')
    report=[r for r in ids if r['split']=='reporting']
    n=len(report)
    U=np.load(base/'public_gradients_reporting_U.npz')['gradient']
    E=np.load(base/'public_gradients_reporting_E.npz')['gradient']
    assert U.shape==E.shape and U.shape[0]==n==256
    muU=U.mean(0,dtype=np.float64);muE=E.mean(0,dtype=np.float64);target=muU+muE
    normU=np.einsum('ij,ij->i',U,U,dtype=np.float64,optimize=False)
    normE=np.einsum('ij,ij->i',E,E,dtype=np.float64,optimize=False)
    cross=np.einsum('ij,ij->i',E,U,dtype=np.float64,optimize=False)
    cf=read(base/'public_coefficients.csv');curves=read(base/'public_bias_curves.csv');risk=read(base/'public_fixed_target_risk.csv')
    out={};max_curve_err=max_derivative_err=max_mse_err=0.
    edited=np.array([float(r['edit_fraction']) for r in report]);length=np.minimum(np.array([float(r['source_length']) for r in report])/64,1)
    max_mc_z=0.
    for mechanism,pi in [('edit',.1+.8*edited),('length',.1+.8*length),('edit_length',.1+.4*(edited+length))]:
        q=pi/pi.sum();r=pi.mean()/pi
        u=matmean(E,q);v=matmean(U,q);delta=u-muE;eps=v-muU
        a,b,c=delta@delta,delta@eps,eps@eps
        d,e,f=u@u,u@v,v@v
        polynomial=np.array([2*(c*e-b*f),2*(c*d-a*f),2*(b*d-a*e)])
        roots=[float(x.real) for x in np.roots(polynomial) if abs(x.imag)<1e-10 and 0<x.real<1]
        values=[]
        for row in curves:
            if row['split']!='reporting' or row['mechanism']!=mechanism:continue
            alpha=float(row['alpha']);N=a+2*b*alpha+c*alpha*alpha;D=d+2*e*alpha+f*alpha*alpha
            expected=np.sqrt(N/D)
            max_curve_err=max(max_curve_err,abs(expected-float(row['rho_Q'])))
            max_derivative_err=max(max_derivative_err,abs(np.polyval(polynomial,alpha)-float(row['rho_Q_squared_derivative_numerator'])))
        for row in risk:
            if row['split']!='reporting' or row['mechanism']!=mechanism:continue
            alpha=float(row['alpha']);w=np.ones(n) if row['method']=='unweighted' else r
            m=matmean(E,q*w)+alpha*matmean(U,q*w)
            diag=normE+2*alpha*cross+alpha*alpha*normU
            exact=np.sum((m-target)**2)+((q*w*w)@diag-m@m)/64
            max_mse_err=max(max_mse_err,abs(exact-float(row['exact_mse'])))
            max_mc_z=max(max_mc_z,abs(exact-float(row['mc_mean_squared_error']))/float(row['mc_standard_error']))
        out[mechanism]={'rho0':float(np.sqrt(a/d)),'rho1':float(np.sqrt((a+2*b+c)/(d+2*e+f))),'untouched_bias_norm':float(np.linalg.norm(eps)),'Q_mean_inner_product':float(e),'interior_derivative_roots':roots}
    nll=read(base/'public_adapter_nll.csv');raw=np.load(base/'public_adapter_per_example_nll.npz');base_nll=raw['baseline'];delta_nll=raw['delta_nll']
    assert delta_nll.shape==(256,90)
    max_nll_err=0.
    for row in nll:
        j=int(row['adapter_id']);mean=float(delta_nll[:,j].mean());stderr=float(delta_nll[:,j].std(ddof=1)/16)
        max_nll_err=max(max_nll_err,abs(mean-float(row['nll_change'])),abs(stderr-float(row['nll_change_se'])))
    manifest=json.loads((base/'public_manifest.json').read_text())
    source=base/f'public_executed_script_{pair.replace("-","_")}.py'
    assert hashes(source)==manifest['script_sha256']
    assert hashes(base/'public_protocol_snapshot.md')==manifest['protocol_sha256']
    assert len(set(r['line'] for r in ids if r['split']=='diagnostic')&set(r['line'] for r in report))==0
    max_mass_error=float(max(np.max(np.abs(U.sum(1,dtype=np.float64))),np.max(np.abs(E.sum(1,dtype=np.float64)))))
    results[pair]={'cases':out,'max_rho_discrepancy':max_curve_err,'max_derivative_numerator_discrepancy':max_derivative_err,'max_mse_discrepancy':max_mse_err,'max_mse_mc_standard_errors':max_mc_z,'max_nll_summary_discrepancy':max_nll_err,'max_gradient_zero_sum_residual':max_mass_error,'num_adapters':len(nll),'all_NLL_changes_negative':bool(np.all(delta_nll.mean(0)<0)),'record_ID_split_overlap':0,'source_protocol_hashes_match':True}
    assert max_curve_err<1e-12 and max_derivative_err<1e-18 and max_mse_err<1e-12 and max_nll_err<1e-14
    del U,E
path=BASE/'public_independent_checks.json';path.write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
