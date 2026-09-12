// Optional release QA using the bundled @oai/artifact-tool engine.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const target = path.join(root, 'results', 'nhs_aisi_results.xlsx');
const meta = JSON.parse(await fs.readFile(path.join(root, 'results', 'workbook_manifest.json'), 'utf8'));
const previews = process.env.WORKBOOK_QA_DIR || '/tmp/nhs_aisi_workbook_qa';
await fs.mkdir(previews, {recursive:true});
const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(target));
wb.recalculate();
let checked = 0;
for (const [address, item] of Object.entries(meta.formula_expectations)) {
  const [sheet, cell] = address.split('!');
  const value = wb.worksheets.getItem(sheet).getRange(cell).values[0][0];
  const okay = typeof item.value === 'number'
    ? typeof value === 'number' && Math.abs(value-item.value) <= 1e-11*Math.max(1,Math.abs(item.value))
    : value === item.value;
  if (!okay) throw new Error(`Formula result mismatch ${address}: ${value} versus ${item.value}`);
  checked++;
}

// A disposable input-change check: alter one linked baseline mean and test the
// expected zero-denominator rule, then restore it before any final export.
const first = meta.formula_expectations['Results!G7'];
const parsed = /^='([^']+)'!([A-Z]+\d+)$/.exec(first.formula);
const sourceCell = wb.worksheets.getItem(parsed[1]).getRange(parsed[2]);
const original = sourceCell.values[0][0];
sourceCell.values = [[0]];
if (wb.worksheets.getItem('Results').getRange('M7').values[0][0] !== 'n.a.') {
  throw new Error('Zero denominator did not produce declared n.a. value');
}
sourceCell.values = [[original]];
wb.recalculate();
if (Math.abs(wb.worksheets.getItem('Results').getRange('G7').values[0][0]-original)>1e-12) {
  throw new Error('Input restoration failed');
}
const errorReport = await wb.inspect({kind:'match', searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!', options:{useRegex:true,maxResults:50}, summary:'formula error scan'});
await fs.writeFile(path.join(previews,'formula_error_scan.json'), errorReport.ndjson);
for (const name of Object.keys(meta.sheets)) {
  const range = name === 'Results' ? 'A2:H13' : name === 'ReadMe' ? 'A1:C10' : 'A1:H10';
  const preview = await wb.render({sheetName:name,range,scale:1,format:'png'});
  await fs.writeFile(path.join(previews,name.replaceAll(' ','_')+'.png'),new Uint8Array(await preview.arrayBuffer()));
}
const formulaPreview = await wb.render({sheetName:'Results',range:'I6:O15',scale:1,format:'png'});
await fs.writeFile(path.join(previews,'Results_formulas.png'),new Uint8Array(await formulaPreview.arrayBuffer()));
const result = await SpreadsheetFile.exportXlsx(wb); await result.save(target);
await fs.writeFile(path.join(previews,'engine_validation.json'),JSON.stringify({checked_formula_cells:checked,zero_denominator_test:true,source_restored:true,recalculated:true,excel_desktop_test:false},null,2));
console.log(JSON.stringify({checked_formula_cells:checked,sheets:Object.keys(meta.sheets).length,previews,exported:target}));
