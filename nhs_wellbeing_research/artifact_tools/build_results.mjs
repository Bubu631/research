import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';

// Supplementary static research tables. All statistics are imported from the
// executed scientific scripts; changing this workbook does not rerun analyses.
const HERE=path.dirname(fileURLToPath(import.meta.url));
const ROOT=path.dirname(HERE);
const OUT=process.env.NHS_RESULTS_OUTPUT || path.join(path.dirname(ROOT),'output/release');
const QA=path.join(HERE,'preview');
await fs.mkdir(OUT,{recursive:true}); await fs.mkdir(QA,{recursive:true});
const sources=[];
const digest=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const textFields=new Set(['org_code','org_name','benchmark_group','legal_org_code','method','dataset','seed','error_kind']);
async function csv(relative) {
  const raw=await fs.readFile(path.join(ROOT,relative),'utf8');
  sources.push({file:relative,sha256:digest(raw)});
  const imported=await Workbook.fromCSV(raw,{sheetName:'Import'});
  const matrix=imported.worksheets.getItemAt(0).getUsedRange().values;
  const headers=matrix[0];
  return matrix.slice(1).filter(r=>r.some(v=>v!==null&&v!=='')).map(row=>Object.fromEntries(headers.map((h,j)=>{
    let v=row[j];
    if(v===null || v==='')v=null;
    else if(!textFields.has(h)&&typeof v==='string'&&/^[-+]?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?$/i.test(v))v=Number(v);
    else if(v==='True'||v==='False')v=v==='True';
    return [h,v];
  })));
}
const workbook=Workbook.create();
const previews=[];
const expected=[];
const NAVY='#263B59', LIGHT='#EDF2F7', TEXT='#202C3D';
const displayNames={dataset:'History vintage',rmse:'RMSE (score)',mae:'MAE (score)',spearman:'Spearman correlation',
 'observed_overlap_0.1':'Observed bottom 10% overlap','observed_overlap_0.2':'Observed bottom 20% overlap','observed_overlap_0.3':'Observed bottom 30% overlap',
 rmse_difference:'RMSE difference',rmse_difference_lo:'RMSE difference lower 95%',rmse_difference_hi:'RMSE difference upper 95%',
 mae_difference:'MAE difference',mae_difference_lo:'MAE difference lower 95%',mae_difference_hi:'MAE difference upper 95%',
 retained_in_next_observed_bottom:'Retained in next observed bottom',burnout_score:'Burnout score (0–10)',burnout_n:'Nominal burnout n',
 n_resp:'Total respondents',hit_mean:'True bottom overlap',hit_mcse:'Overlap MCSE',state_mse_mean:'State MSE (score²)',
 latent_regret_mean:'Latent regret (score)',latent_regret_mcse:'Regret MCSE (score)',
 n_eligible_from_org_rate:'Derived eligible denominator',n_eff:'Effective n (unavailable)',burnout_se:'Burnout SE (unavailable)',
 burnout_individual_sd:'Burnout SD (unavailable)'};
const colName=i=>{let s='';for(i++;i>0;i=Math.floor((i-1)/26))s=String.fromCharCode(65+(i-1)%26)+s;return s;};
function baseSheet(name,title,notes) {
  const sheet=workbook.worksheets.add(name);sheet.showGridLines=false;
  sheet.getRange('A1:P6').format.font={name:'Arial',size:10,color:TEXT};
  sheet.getRange('A2').values=[[title]];sheet.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:TEXT};
  sheet.getRange('A2:P2').format.borders={bottom:{style:'thin',color:NAVY}};
  sheet.getRange('A2:P2').format.rowHeight=25;
  notes.forEach((note,i)=>{sheet.getRange(`A${i+3}`).values=[[note]];sheet.getRange(`A${i+3}`).format.font={name:'Arial',size:10,italic:true,color:'#536177'};});
  sheet.freezePanes.freezeRows(7);
  return sheet;
}
function table(sheet,headers,rows,{start=7,textWidths={},formats={}}={}) {
  const end=start+rows.length,last=colName(headers.length-1);
  const matrix=[headers.map(h=>displayNames[h]??h.replaceAll('_',' ')),...rows.map(r=>headers.map(h=>r[h]??null))];
  const range=sheet.getRange(`A${start}:${last}${end}`);range.values=matrix;
  range.format.font={name:'Arial',size:10,color:TEXT};
  range.format.rowHeight=23;range.format.verticalAlignment='center';
  range.format.columnWidth=15;
  const head=sheet.getRange(`A${start}:${last}${start}`);
  head.format={fill:NAVY,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,horizontalAlignment:'center',verticalAlignment:'center',rowHeight:54};
  head.format.borders={insideVertical:{style:'thin',color:'#FFFFFF'}};
  const t=sheet.tables.add(`A${start}:${last}${end}`,true,`Table${sheet.name.replace(/[^a-zA-Z]/g,'')}${start}`);
  t.showFilterButton=true;t.style='TableStyleLight1';
  headers.forEach((h,j)=>{
    const c=colName(j),r=sheet.getRange(`${c}${start+1}:${c}${end}`);
    const isText=rows.some(row=>typeof row[h]==='string');
    r.format.horizontalAlignment=isText?'left':'right';
    r.setNumberFormat(formats[h]??(isText?'@':rows.every(row=>row[h]===null||typeof row[h]==='boolean'||Number.isInteger(row[h]))?'#,##0':'0.0000'));
    if(textWidths[h])sheet.getRange(`${c}${start}:${c}${end}`).format.columnWidth=textWidths[h];
  });
  expected.push({sheet:sheet.name,start,headers,matrix});
  return end;
}

const forecast=[];
for(const dataset of ['harmonised','vintage']) {
  const metrics=await csv(`results/${dataset}/test_metrics.csv`);
  const uncertainty=await csv(`results/${dataset}/paired_bootstrap.csv`);
  const manifest=JSON.parse(await fs.readFile(path.join(ROOT,`results/${dataset}/manifest.json`),'utf8'));
  // Fail closed if the final corrected resampling file does not identify its
  // legal-entity bootstrap. Root finalises this before the workbook is built.
  if(manifest.bootstrap_entity_clusters!==189)throw Error('Final legal-entity bootstrap metadata is required');
  for(const row of metrics) {
    const boot=uncertainty.find(b=>b.method===row.method);if(!boot)throw Error('Unmatched bootstrap method');
    forecast.push({dataset,...row,...boot});
  }
}
const f=baseSheet('Forecasts','NHS staff wellbeing: 2025 prediction results',[
  '190 reporting units from 189 legal entities. Scores range 0–10; higher means less burnout.',
  'Static snapshots. Differences are relative to latest score. Intervals describe paired legal-entity bootstrap uncertainty.',
  'Harmonised histories use the 2025 release. Vintage histories use the corresponding archived training releases.'
]);f.tabColor=NAVY;
const fcols=['dataset','method','rmse','mae','spearman','observed_overlap_0.1','observed_overlap_0.2','observed_overlap_0.3',
  'rmse_difference','rmse_difference_lo','rmse_difference_hi','mae_difference','mae_difference_lo','mae_difference_hi','bootstrap_repetitions'];
table(f,fcols,forecast,{textWidths:{dataset:17,method:30},formats:{'observed_overlap_0.1':'0.0%','observed_overlap_0.2':'0.0%','observed_overlap_0.3':'0.0%'}});
f.freezePanes.freezeColumns(2);
previews.push(['Forecasts','A1:H15'],['Forecasts','I7:O15']);

const follow=baseSheet('Followup','Observed follow-up and ranking sensitivity',[
  'Observed survey changes do not identify intervention effects or a zero-intervention counterfactual.',
  'Bottom 20% is selected within benchmark groups, with integer group-specific quotas.',
  'Sensitivity varies the working variance ratio; nominal response counts do not identify effective sample size.'
]);
const obs=await csv('results/harmonised/observational_followup.csv');
const obsEnd=table(follow,Object.keys(obs[0]),obs,{textWidths:{corresponding_group_change:22,group_centred_change:19,retained_in_next_observed_bottom:24},formats:{selection_year:'0',followup_year:'0',retained_in_next_observed_bottom:'0.0%'}});
follow.getRange(`A${obsEnd+3}`).values=[['Static ranking sensitivity, 2025']];
follow.getRange(`A${obsEnd+3}`).format.font={name:'Arial',size:12,bold:true,color:TEXT};
const sensitivity=await csv('results/harmonised/rank_sensitivity.csv');
table(follow,Object.keys(sensitivity[0]),sensitivity,{start:obsEnd+5,formats:{overlap_with_raw:'0.0%'}});
previews.push(['Followup','A1:J12'],['Followup',`A${obsEnd+3}:E${obsEnd+12}`]);

const simulation=(await csv('results/simulation.csv')).filter(r=>r.fraction===.2&&r.phi===.85&&r.sigma2===6.25&&r.psi===0);
if(simulation.length!==20)throw Error(`Unexpected simulation slice: ${simulation.length}`);
const sim=baseSheet('Simulation','Synthetic selection experiment: fixed parameter slice',[
  'Synthetic observations. Fraction = 0.20, persistence phi = 0.85, measurement variance sigma2 = 6.25, error persistence psi = 0.',
  'All 20 rows in this parameter slice are retained. MCSE describes Monte Carlo error; p10 and p90 describe replicate variation.',
  'Latent regret and current-state MSE are available only in simulation. These rows are not NHS observations.'
]);
const simkeys=['method','n_lo','n_hi','hit_mean','hit_mcse','latent_regret_mean','latent_regret_mcse','state_mse_mean','rebound_mean',
 'predicted_rebound_mean','rebound_residual_mean',...Object.keys(simulation[0]).filter(k=>!['method','n_lo','n_hi','hit_mean','hit_mcse','latent_regret_mean','latent_regret_mcse','state_mse_mean','rebound_mean','predicted_rebound_mean','rebound_residual_mean'].includes(k))];
table(sim,simkeys,simulation,{textWidths:{method:31,seed:25,error_kind:15},formats:{hit_mean:'0.0%',hit_mcse:'0.000%'}});
sim.freezePanes.freezeColumns(1);previews.push(['Simulation','A1:H16']);

const all=await csv('data/processed/nhs_staff_survey_panel_2021_2025.csv');
const panelkeys=['org_code','org_name','year','benchmark_group','legal_org_code','is_trust','complete_five_year_history','historically_comparable',
 'burnout_score','burnout_n','n_resp','response_rate','wellbeing_action','wellbeing_action_n','intent_leave','intent_leave_n',
 'thinking_about_leaving_score','thinking_about_leaving_n','work_related_stress','work_related_stress_n',
 'n_eligible','n_eligible_from_org_rate','n_eff','burnout_se','burnout_individual_sd'];
const panel=baseSheet('Source panel','Published NHS institution-year observations, 2021–2025',[
 '238 reporting units and 1,190 rows. All rows are retained, including missing observations and units excluded from primary analysis.',
 'Blank is unavailable, not zero. Eligible denominator from own response rate is derived; effective n and composite SD/SE are unavailable.',
 'Source: NHS Staff Survey 2021–2025 benchmark workbook, updated 17 March 2026. URL and SHA-256 appear in Dictionary.'
]);
table(panel,panelkeys,all,{textWidths:{org_code:13,org_name:43,benchmark_group:37,legal_org_code:14},formats:{year:'0',response_rate:'0.0%',wellbeing_action:'0.0%',intent_leave:'0.0%',work_related_stress:'0.0%'}});
panel.getRange('B8:B1197').format.wrapText=true;panel.getRange('D8:D1197').format.wrapText=true;
panel.getRange('A8:Y1197').format.rowHeight=42;
panel.getRange('C8:C1197').format.horizontalAlignment='center';
panel.freezePanes.freezeColumns(1);previews.push(['Source panel','A1:H13'],['Source panel','I7:P13']);

const dictionary=JSON.parse(await fs.readFile(path.join(ROOT,'data/processed/data_dictionary.json'),'utf8'));
const d=baseSheet('Dictionary','Measures, units and snapshot provenance',[
 'Source CSV files and scientific scripts define the analysis. The workbook contains static typed values, not a live analysis model.',
 'The full panel CSV also contains per-cell source locators and additional provenance fields omitted here for readability.',
 'Source data terms are separate from the research code licence. No blanket licence is asserted for downloaded NHS assets.'
]);
const definitions=panelkeys.map(field=>({field,definition:dictionary[field].definition||dictionary[field].units,source_variable:dictionary[field].source_variable||''}));
definitions.push(
 {field:'rmse / mae',definition:'Forecast error against the published 2025 burnout score, in score units. Lower is better.',source_variable:'test_metrics.csv'},
 {field:'spearman',definition:'Spearman rank correlation across the evaluation reporting units. Higher indicates stronger rank association.',source_variable:'test_metrics.csv'},
 {field:'observed_overlap_0.1/0.2/0.3',definition:'Proportion of the next observed bottom set recovered by the forecast ranking within benchmark groups. Not latent-truth accuracy.',source_variable:'test_metrics.csv'},
 {field:'difference_lo / difference_hi',definition:'2.5th and 97.5th percentiles of paired bootstrap differences from latest score. R1F1 and R1F2 are jointly resampled as one entity.',source_variable:'paired_bootstrap.csv'},
 {field:'ratio',definition:'Unidentified measurement-to-latent variance ratio in the static Gaussian shrinkage sensitivity. Not an estimated NHS design effect.',source_variable:'rank_sensitivity.csv'},
 {field:'simulation seed',definition:'Stored as an exact text identifier to avoid Excel numeric precision loss. All other numerical results retain numeric types.',source_variable:'simulation.csv'});
const de=table(d,['field','definition','source_variable'],definitions,{textWidths:{field:34,definition:108,source_variable:30}});
d.getRange(`B8:B${de}`).format.wrapText=true;d.getRange(`A8:C${de}`).format.rowHeight=40;
const sourceManifest=JSON.parse(await fs.readFile(path.join(ROOT,'data/source_manifest.json'),'utf8'));
const original=sourceManifest.sources['benchmark_2021_2025_v2.xlsx'];
const sr=de+4;
d.getRange(`A${sr}`).values=[['Original NHS benchmark source']];
d.getRange(`B${sr}`).values=[[original.url]];
d.getRange(`A${sr+1}`).values=[['Source SHA-256']];d.getRange(`B${sr+1}`).values=[[original.sha256]];
d.getRange(`A${sr+2}`).values=[['Retrieved UTC']];d.getRange(`B${sr+2}`).values=[[new Date(original.accessed_at_utc)]];
d.getRange(`B${sr+2}`).setNumberFormat('yyyy-mm-dd hh:mm:ss');
const sourceEnd=table(d,['file','sha256'],sources,{start:sr+5});
d.getRange(`A7:A${sourceEnd}`).format.columnWidth=44;
d.getRange(`B7:B${sourceEnd}`).format.columnWidth=110;
d.getRange(`B${sr}`).format.wrapText=true;d.getRange(`A${sr}:B${sr}`).format.rowHeight=44;
d.getRange(`A${sr+6}:A${sourceEnd}`).format.wrapText=true;d.getRange(`A${sr+6}:B${sourceEnd}`).format.rowHeight=36;
previews.push(['Dictionary','A1:C14'],['Dictionary',`A${sr}:B${sr+7}`]);

workbook.recalculate();
const errors=await workbook.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},summary:'final error scan'});
await fs.writeFile(path.join(QA,'error_scan.ndjson'),errors.ndjson);
for(const item of expected) {
 const sheet=workbook.worksheets.getItem(item.sheet);
 const got=sheet.getRangeByIndexes(item.start-1,0,item.matrix.length,item.headers.length).values;
 if(JSON.stringify(got)!==JSON.stringify(item.matrix))throw Error(`In-memory cell mismatch: ${item.sheet}`);
}
const inspected=await workbook.inspect({kind:'table',range:'Forecasts!A7:E10',include:'values,formulas',tableMaxRows:4,tableMaxCols:5,maxChars:2000});
await fs.writeFile(path.join(QA,'forecast_inspect.ndjson'),inspected.ndjson);
for(let i=0;i<previews.length;i++) {
 const [sheetName,range]=previews[i];
 const preview=await workbook.render({sheetName,range,scale:1.5,format:'png'});
 await fs.writeFile(path.join(QA,`${i+1}_${sheetName.replace(/ /g,'_')}.png`),new Uint8Array(await preview.arrayBuffer()));
}
const output=await SpreadsheetFile.exportXlsx(workbook);
const final=path.join(OUT,'nhs_wellbeing_results.xlsx');await output.save(final);
await fs.writeFile(path.join(HERE,'workbook_manifest.json'),JSON.stringify({
  created_at_utc:new Date().toISOString(),builder_sha256:digest(await fs.readFile(fileURLToPath(import.meta.url))),
  file:path.basename(final),sha256:digest(await fs.readFile(final)),sources,
  sheets:expected.map(e=>({name:e.sheet,first_row:e.start,data_rows:e.matrix.length-1,columns:e.headers})),
  simulation_filter:{fraction:.2,phi:.85,sigma2:6.25,psi:0},
  verification:'All authored cells compared with imported source matrices; recalculated; inspected; all worksheets rendered for visual review',
},null,2)+'\n');
console.log(final);
