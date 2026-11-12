const patients = [
  { id:'DEMO-1042', initials:'AL', name:'Alex L.', age:64, sex:'F', condition:'Heart failure', risk:72, level:'Elevated', observation:'Heart rate · 88 bpm', updated:'09:32', events:[['Today · 09:32','Vital signs recorded','Heart rate 88 bpm · blood pressure 132/78 mmHg','vital'],['Today · 08:20','Laboratory result','Creatinine 1.1 mg/dL · potassium 4.2 mmol/L','lab'],['Yesterday · 16:10','Clinical note added','Synthetic sample note: follow-up planned.','note'],['Nov 10 · 11:45','Risk estimate generated','Illustrative 30-day readmission output: 72% · elevated','risk'],['Nov 09 · 14:30','Admission recorded','Demo admission · index discharge time not validated','vital']], vitals:[['Heart rate','88','bpm'],['Blood pressure','132/78','mmHg'],['Temperature','36.8','°C'],['Respiratory rate','17','/min'],['Oxygen saturation','97','%'],['Creatinine','1.1','mg/dL']] },
  { id:'DEMO-1087', initials:'JM', name:'Jordan M.', age:51, sex:'M', condition:'Type 2 diabetes', risk:48, level:'Moderate', observation:'Glucose · 142 mg/dL', updated:'09:18', events:[['Today · 09:18','Risk estimate generated','Illustrative 30-day readmission output: 48% · moderate','risk'],['Today · 08:55','Laboratory result','Glucose 142 mg/dL · HbA1c 7.1%','lab'],['Yesterday · 15:05','Vital signs recorded','Heart rate 76 bpm · blood pressure 126/80 mmHg','vital'],['Nov 08 · 10:15','Admission recorded','Demo admission · synthetic record','vital']], vitals:[['Heart rate','76','bpm'],['Blood pressure','126/80','mmHg'],['Temperature','36.7','°C'],['Respiratory rate','16','/min'],['Oxygen saturation','98','%'],['Glucose','142','mg/dL']] },
  { id:'DEMO-1103', initials:'SK', name:'Sam K.', age:73, sex:'F', condition:'Chronic kidney disease', risk:29, level:'Lower', observation:'Creatinine · 1.4 mg/dL', updated:'08:41', events:[['Today · 08:41','Laboratory result','Creatinine 1.4 mg/dL · eGFR 48 mL/min/1.73m²','lab'],['Today · 08:15','Vital signs recorded','Heart rate 72 bpm · blood pressure 118/72 mmHg','vital'],['Nov 11 · 12:30','Clinical note added','Synthetic sample note: routine review.','note'],['Nov 07 · 09:40','Risk estimate generated','Illustrative 30-day readmission output: 29% · lower','risk']], vitals:[['Heart rate','72','bpm'],['Blood pressure','118/72','mmHg'],['Temperature','36.5','°C'],['Respiratory rate','15','/min'],['Oxygen saturation','98','%'],['Creatinine','1.4','mg/dL']] },
  { id:'DEMO-1118', initials:'TR', name:'Taylor R.', age:46, sex:'M', condition:'COPD', risk:63, level:'Elevated', observation:'O₂ saturation · 94%', updated:'Yesterday', events:[['Yesterday · 17:05','Vital signs recorded','Oxygen saturation 94% · respiratory rate 19/min','vital'],['Yesterday · 15:30','Clinical note added','Synthetic sample note: respiratory follow-up.','note'],['Nov 10 · 13:05','Risk estimate generated','Illustrative 30-day readmission output: 63% · elevated','risk'],['Nov 08 · 10:00','Admission recorded','Demo admission · synthetic record','vital']], vitals:[['Heart rate','84','bpm'],['Blood pressure','128/82','mmHg'],['Temperature','37.0','°C'],['Respiratory rate','19','/min'],['Oxygen saturation','94','%'],['Peak flow','310','L/min']] },
  { id:'DEMO-1132', initials:'PC', name:'Parker C.', age:38, sex:'F', condition:'Pneumonia', risk:34, level:'Lower', observation:'Temperature · 37.1 °C', updated:'Yesterday', events:[['Yesterday · 18:00','Vital signs recorded','Temperature 37.1 °C · oxygen saturation 97%','vital'],['Nov 11 · 14:15','Laboratory result','WBC 8.7 ×10⁹/L · synthetic example','lab'],['Nov 11 · 11:00','Risk estimate generated','Illustrative 30-day readmission output: 34% · lower','risk'],['Nov 10 · 09:20','Admission recorded','Demo admission · synthetic record','vital']], vitals:[['Heart rate','79','bpm'],['Blood pressure','120/76','mmHg'],['Temperature','37.1','°C'],['Respiratory rate','16','/min'],['Oxygen saturation','97','%'],['WBC','8.7','×10⁹/L']] },
  { id:'DEMO-1156', initials:'DW', name:'Drew W.', age:68, sex:'M', condition:'Heart failure', risk:56, level:'Moderate', observation:'Weight · 81.2 kg', updated:'Nov 11', events:[['Nov 11 · 16:40','Vital signs recorded','Weight 81.2 kg · heart rate 80 bpm','vital'],['Nov 11 · 10:25','Laboratory result','BNP 180 pg/mL · synthetic example','lab'],['Nov 10 · 11:45','Clinical note added','Synthetic sample note: medication review.','note'],['Nov 09 · 08:50','Risk estimate generated','Illustrative 30-day readmission output: 56% · moderate','risk']], vitals:[['Heart rate','80','bpm'],['Blood pressure','130/80','mmHg'],['Temperature','36.6','°C'],['Respiratory rate','17','/min'],['Oxygen saturation','96','%'],['Weight','81.2','kg']] },
  { id:'DEMO-1174', initials:'MN', name:'Morgan N.', age:57, sex:'F', condition:'Type 2 diabetes', risk:19, level:'Lower', observation:'HbA1c · 6.8%', updated:'Nov 11', events:[['Nov 11 · 15:10','Laboratory result','HbA1c 6.8% · glucose 118 mg/dL','lab'],['Nov 11 · 09:45','Vital signs recorded','Heart rate 70 bpm · blood pressure 116/74 mmHg','vital'],['Nov 10 · 16:00','Risk estimate generated','Illustrative 30-day readmission output: 19% · lower','risk']], vitals:[['Heart rate','70','bpm'],['Blood pressure','116/74','mmHg'],['Temperature','36.4','°C'],['Respiratory rate','15','/min'],['Oxygen saturation','99','%'],['HbA1c','6.8','%']] },
  { id:'DEMO-1201', initials:'EC', name:'Emerson C.', age:79, sex:'M', condition:'Chronic kidney disease', risk:81, level:'Elevated', observation:'eGFR · 38 mL/min', updated:'Nov 11', events:[['Nov 11 · 17:22','Risk estimate generated','Illustrative 30-day readmission output: 81% · elevated','risk'],['Nov 11 · 14:05','Laboratory result','Creatinine 1.8 mg/dL · eGFR 38 mL/min','lab'],['Nov 11 · 13:45','Vital signs recorded','Heart rate 91 bpm · blood pressure 138/84 mmHg','vital'],['Nov 10 · 10:15','Admission recorded','Demo admission · synthetic record','vital']], vitals:[['Heart rate','91','bpm'],['Blood pressure','138/84','mmHg'],['Temperature','36.9','°C'],['Respiratory rate','18','/min'],['Oxygen saturation','96','%'],['eGFR','38','mL/min']] },
];

const $ = (selector, root=document) => root.querySelector(selector);
const $$ = (selector, root=document) => [...root.querySelectorAll(selector)];
const apiFetch = (url, options={}) => { const headers=new Headers(options.headers||{}); const key=sessionStorage.getItem('clintel-api-key'); if(key)headers.set('X-API-Key',key); return fetch(url,{...options,headers}); };
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
let selectedPatient = patients[0];
let toastTimer;
let apiConnected = false;

function showToast(message) { const toast=$('#toast'); toast.textContent=message; toast.classList.add('show'); clearTimeout(toastTimer); toastTimer=setTimeout(()=>toast.classList.remove('show'),2500); }
function renderMiniPatients() { $('#miniPatients').innerHTML=patients.slice(0,3).map(p=>`<div class="mini-patient" data-patient="${p.id}"><div class="patient-initial">${p.initials}</div><div class="mini-patient-info"><b>${p.id}</b><small>${p.condition} · updated ${p.updated}</small></div><span class="risk-pill risk-${p.level.toLowerCase()}">${p.level}</span></div>`).join(''); }
function renderPatients() { const query=$('#patientSearch')?.value.trim().toLowerCase()||''; const risk=$('#riskFilter')?.value||'all'; const filtered=patients.filter(p=>(p.id.toLowerCase().includes(query)||p.condition.toLowerCase().includes(query))&&(risk==='all'||p.level===risk)); $('#patientRows').innerHTML=filtered.map(p=>`<tr><td><button class="patient-link" data-patient="${p.id}"><span class="patient-initial">${p.initials}</span><span><b>${p.id}</b><small>Fictional demo record</small></span></button></td><td>${p.age} / ${p.sex}</td><td class="patient-condition">${p.condition}</td><td>${p.observation}</td><td><span class="risk-pill risk-${p.level.toLowerCase()}">${p.level} · ${p.risk}%</span></td><td>${p.updated}</td><td><button class="text-button" data-patient="${p.id}" aria-label="Open patient">→</button></td></tr>`).join(''); $('#patientCount').textContent=`Showing ${filtered.length} fictional sample record${filtered.length===1?'':'s'}`; }
function renderTimeline() { const picker=$('#timelinePatient'); picker.innerHTML=patients.map(p=>`<option value="${p.id}" ${p.id===selectedPatient.id?'selected':''}>${p.id} · ${p.name}</option>`).join(''); const p=selectedPatient; $('#patientSummary').innerHTML=`<div class="summary-avatar">${p.initials}</div><div class="summary-info"><h3>${p.id} <span class="status-chip status-demo">SYNTHETIC</span></h3><p>Age ${p.age} · ${p.sex} · ${p.condition} · fictional demo record</p></div><div class="summary-risk"><span>Illustrative 30-day output</span><b class="risk-pill risk-${p.level.toLowerCase()}">${p.level} · ${p.risk}%</b></div>`; $('#fullTimeline').innerHTML=p.events.map(e=>`<div class="event"><time>${escapeHtml(e[0])}</time><i class="event-node ${e[3]}"></i><div class="event-content"><b>${escapeHtml(e[1])}</b><p>${escapeHtml(e[2])}</p></div></div>`).join(''); $('#vitalsList').innerHTML=p.vitals.map(v=>`<div class="vital-row"><span>${escapeHtml(v[0])}</span><b>${escapeHtml(v[1])}<small>${escapeHtml(v[2])}</small></b></div>`).join(''); }
function navigate(view) { const valid=['dashboard','patients','timeline','models','evidence','about'].includes(view)?view:'dashboard'; $$('.view').forEach(el=>el.classList.toggle('active',el.id===`view-${valid}`)); $$('.nav-item[data-view]').forEach(el=>el.classList.toggle('active',el.dataset.view===valid)); const label={dashboard:'Overview',patients:'Patient registry',timeline:'Patient timeline',models:'Risk models',evidence:'Evidence assistant',about:'About this project'}[valid]; $('#breadcrumbCurrent').textContent=label; history.replaceState(null,'',`#${valid}`); $('#sidebar').classList.remove('open'); window.scrollTo({top:0,behavior:'smooth'}); }
function answerFor(question) { const q=question.toLowerCase(); if(/split|leak|train|validation|test|patient/.test(q)) return {text:'The project notes recommend splitting the data by patient, so records from the same person do not appear in more than one partition. Define the index time first and exclude features that would only be known after that time.',source:'Cohort & evaluation notes · Source 02'}; if(/metric|evaluate|performance|auroc|auprc|calibrat/.test(q)) return {text:'The evaluation checklist includes AUROC and AUPRC for discrimination, calibration assessment, precision, recall, F1 and confusion matrices. Report confidence intervals where feasible, and examine temporal and subgroup performance. The current runtime reports only synthetic benchmark results; no clinical evaluation is available.',source:'Cohort & evaluation notes · Source 02'}; if(/evidence|rag|retriev|source|citation/.test(q)) return {text:'The documented workflow is: question → retrieval from permitted reference documents → evidence filtering → response with citations. The assistant should show its evidence and say when relevant support is unavailable. The API uses TF-IDF retrieval over the local project-note corpus.',source:'ClinIntel AI project brief · Source 01'}; if(/safety|medical|diagnos|treat|clinical|patient care/.test(q)) return {text:'ClinIntel AI is scoped to research and education. It must not independently diagnose, prescribe, triage or replace a qualified clinician. This prototype contains fictional data and does not provide medical guidance.',source:'Research-use limitations · Source 03'}; if(/cohort|label|outcome|horizon|index time/.test(q)) return {text:'Before modeling, define the exact population, index time, prediction horizon and outcome, and document inclusion and exclusion rules. Keep only features available at the prediction time to prevent leakage.',source:'Cohort & evaluation notes · Source 02'}; if(/mimic|dataset|data|privacy|access/.test(q)) return {text:'The project brief describes starting with an appropriately governed dataset such as the MIMIC-IV demo where suitable, and using credentialed data only after completing its access requirements. This dashboard uses synthetic development records unless an approved cohort is separately configured.',source:'ClinIntel AI project brief · Source 01'}; return {text:'I could not find a supported answer in the small project-note set. The demo assistant only responds to topics covered by its displayed sources and will not invent clinical guidance.',source:'No matching project evidence · Sources 01–03'}; }
async function sendMessage(question) { const text=question.trim(); if(!text)return; const box=$('#chatMessages'); const user=document.createElement('div'); user.className='message user-message'; user.innerHTML=`<div class="message-content"><p>${escapeHtml(text)}</p><small>YOU · NOW</small></div>`; box.append(user); $('.suggested-prompts',box)?.remove(); let answer; if(apiConnected){try{const response=await apiFetch('/api/clinical-question',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:text})});if(!response.ok)throw new Error('Evidence API is unavailable.');const result=await response.json();answer={text:result.answer,source:result.abstained?'NO MATCHING PROJECT EVIDENCE':(result.evidence||[]).map(item=>`${item.title} · ${item.source}`).join(' | ')}}catch{answer=answerFor(text)}}else answer=answerFor(text); const response=document.createElement('div'); response.className='message assistant-message assistant-response'; response.innerHTML=`<div class="message-avatar">✳</div><div class="message-content"><p>${escapeHtml(answer.text)}</p><small>${escapeHtml(answer.source.toUpperCase())}</small></div>`; box.append(response); box.scrollTop=box.scrollHeight; }

function fromApiPatient(live) {
  const prediction = live.prediction;
  const risk = Math.round(prediction.probability * 100);
  const f = live.features;
  return {
    id: live.patient_id, initials: 'SD', name: 'Synthetic demo record', age: live.age,
    sex: live.sex, condition: live.condition, risk, level: prediction.risk_band,
    observation: `Heart rate · ${f.heart_rate_mean} bpm`, updated: 'Demo',
    events: [
      ['Synthetic index', 'Pre-index feature summary', 'Values generated for software demonstration; not observed clinical measurements.', 'vital'],
      ['Synthetic model', '30-day baseline output', `${prediction.risk_band} · ${risk}% · synthetic benchmark only`, 'risk'],
    ],
    vitals: [
      ['Age', String(live.age), 'years'], ['Heart rate', String(f.heart_rate_mean), 'bpm'],
      ['Systolic blood pressure', String(f.sbp_mean), 'mmHg'], ['Creatinine maximum', String(f.creatinine_max), 'mg/dL'],
      ['Prior admissions', String(f.prior_admissions), 'synthetic'], ['Length of stay', String(f.length_of_stay), 'days'],
    ],
  };
}

async function connectResearchApi() {
  try {
    const healthResponse = await apiFetch('/api/health', { cache: 'no-store' });
    if (!healthResponse.ok) return;
    const health = await healthResponse.json();
    if (!health.research_only) return;
    const [registryResponse, modelResponse] = await Promise.all([
      apiFetch('/api/patients', { cache: 'no-store' }),
      apiFetch('/api/models/readmission', { cache: 'no-store' }),
    ]);
    if (registryResponse.status === 401) {
      apiConnected = false;
      $('.data-badge').innerHTML = '<span></span> API KEY REQUIRED';
      $('#apiKeyButton').textContent = 'Connect API';
      return;
    }
    if (!registryResponse.ok) return;
    const registry = await registryResponse.json();
    apiConnected = true;
    const approved = registry.data_origin !== 'synthetic';
    $('.data-badge').innerHTML = `<span></span> ${approved ? 'APPROVED RESEARCH API' : 'SYNTHETIC API CONNECTED'}`;
    $('#apiKeyButton').textContent = sessionStorage.getItem('clintel-api-key') ? 'Disconnect API' : 'Connect API';
    $('.stat-card:nth-child(1) .stat-top span').textContent = approved ? 'Approved research cohort' : 'Synthetic cohort';
    $('.stat-card:nth-child(1) .stat-foot').innerHTML = approved ? '<span class="neutral">Authorized cohort sample</span><span>research use</span>' : '<span class="neutral">Generated records</span><span>not patient data</span>';
    $('.stat-card:nth-child(2) .stat-foot').innerHTML = approved ? '<span class="neutral">Research output mix</span><span>not a care threshold</span>' : '<span class="neutral">Synthetic benchmark</span><span>illustrative threshold</span>';
    $('.risk-panel .panel-heading p').textContent = approved ? 'Approved research cohort · model output' : 'Synthetic 30-day readmission baseline · research demo';
    $('.risk-panel .chart-footnote').textContent = approved ? 'Percentages summarize the displayed authorized registry sample, not clinical validity.' : 'Risk percentages are model outputs on synthetic records; they are not clinical evidence.';
    $('#view-dashboard .notice div span').textContent = approved ? 'Research model output on an approved cohort. It is not medical advice and has not been clinically validated.' : 'Synthetic model outputs are for research only. They are not medical advice or clinically validated.';
    $('#view-dashboard .app-footer span:last-child').textContent = approved ? 'Authorized research records · handle under your study governance.' : 'All records and observations are synthetic development examples.';
    $('#view-patients .notice strong').textContent = approved ? 'Approved research records' : 'Fictional records';
    $('#view-patients .notice div span').textContent = approved ? 'Access is protected by the configured research API key; follow your study data-use rules.' : 'These records are generated synthetic examples, not real patient data.';
    $('#view-patients .app-footer span:last-child').textContent = approved ? 'Research records require approved access and local governance.' : 'Fictional records only.';
    $('#view-timeline .vitals-disclaimer').textContent = approved ? 'Research record values; use only under the approved study governance.' : 'All values are synthetic examples for software demonstration.';
    patients.splice(0, patients.length, ...registry.patients.map(fromApiPatient));
    selectedPatient = patients.find(patient => patient.id === selectedPatient.id) || patients[0];
    const distribution = registry.risk_distribution || {};
    $('#cohortSize').textContent = Number(registry.cohort_size || 0).toLocaleString();
    $('#scoredCount').textContent = Number(registry.cohort_size || 0).toLocaleString();
    if (registry.elevated_percent != null) $('#elevatedPct').innerHTML = `${escapeHtml(registry.elevated_percent)}<span class="value-unit">%</span>`;
    if (distribution.Lower != null) $('#lowerPct').textContent = `${distribution.Lower}%`;
    if (distribution.Moderate != null) $('#moderatePct').textContent = `${distribution.Moderate}%`;
    if (distribution.Elevated != null) $('#chartElevatedPct').textContent = `${distribution.Elevated}%`;
    renderMiniPatients(); renderPatients(); renderTimeline();
    if (modelResponse.ok) {
      const card = await modelResponse.json();
      const metrics = card.metrics || {};
      if (metrics.expected_calibration_error_10bin != null) $('#eceValue').textContent = metrics.expected_calibration_error_10bin.toFixed(3);
      const meta = $$('.model-meta b');
      if (meta[0]) meta[0].textContent = `${card.model_version} · ${approved ? 'reviewed cohort' : 'synthetic'}`;
      if (meta[2]) meta[2].textContent = approved ? 'Approved research cohort' : 'Synthetic development cohort';
      const note = $('.model-note p');
      if (note) note.textContent = approved ? `Held-out AUROC ${metrics.auroc ?? '—'} · AUPRC ${metrics.auprc ?? '—'} · ECE ${metrics.expected_calibration_error_10bin ?? '—'}. Research metrics; not clinical validation.` : `Synthetic held-out AUROC ${metrics.auroc ?? '—'} · AUPRC ${metrics.auprc ?? '—'} · ECE ${metrics.expected_calibration_error_10bin ?? '—'}. Software benchmark only, not clinical evidence.`;
      $('#view-models .notice div strong').textContent = approved ? 'Research model; clinical validity not established' : 'Synthetic model benchmark only';
      $('#view-models .notice div span').textContent = approved ? 'Metrics are retrospective research results from the supplied cohort. External, temporal, and prospective validation may still be required.' : 'The local API trains a baseline on generated synthetic data. Its numbers are software checks, not evidence of clinical performance.';
      const modelDetails=$$('.model-detail .definition-list');
      if(modelDetails[0]){const entries=modelDetails[0].querySelectorAll('div');if(entries[4])entries[4].lastElementChild.textContent=(card.features||[]).length+' pre-index features';if(entries[5])entries[5].lastElementChild.textContent='Synthetic holdout evaluated';}
      const forest=card.model_comparison?.random_forest_candidate;const detailCards=$$('.model-detail');if(forest&&detailCards[1]){const validation=forest.validation||{};const test=forest.test||{};const callout=$('.model-callout',detailCards[1]);if(callout)callout.textContent=`Validation AUROC ${validation.auroc??'—'} · test AUROC ${test.auroc??'—'} · test AUPRC ${test.auprc??'—'}. Synthetic benchmark only; the logistic baseline remains served.`;const entries=$$('.definition-list div',detailCards[1]);if(entries[5])entries[5].lastElementChild.textContent='Synthetic holdout benchmark';}
    }
  } catch { apiConnected = false; }
}

renderMiniPatients(); renderPatients(); renderTimeline();
const initial=location.hash.slice(1); if(initial)navigate(initial);
$$('.nav-item[data-view]').forEach(link=>link.addEventListener('click',e=>{e.preventDefault();navigate(link.dataset.view)}));
$$('[data-nav]').forEach(button=>button.addEventListener('click',()=>navigate(button.dataset.nav)));
document.addEventListener('click',e=>{const target=e.target.closest('[data-patient]');if(target){const p=patients.find(item=>item.id===target.dataset.patient);if(p){selectedPatient=p;renderTimeline();navigate('timeline')}}});
$('#patientSearch').addEventListener('input',renderPatients); $('#riskFilter').addEventListener('change',renderPatients); $('#timelinePatient').addEventListener('change',e=>{selectedPatient=patients.find(p=>p.id===e.target.value)||patients[0];renderTimeline()});
$('#mobileMenu').addEventListener('click',()=>$('#sidebar').classList.toggle('open'));
$('.notice-close').addEventListener('click',e=>e.currentTarget.closest('.notice').remove());
$('#askEvidence').addEventListener('click',()=>{navigate('evidence');$('#chatInput').focus()});
$('#chatForm').addEventListener('submit',e=>{e.preventDefault();const input=$('#chatInput');sendMessage(input.value);input.value=''});
document.addEventListener('click',e=>{const prompt=e.target.closest('.suggested-prompts button');if(prompt){const question=prompt.textContent;sendMessage(question)}});
$('#exportCsv').addEventListener('click',()=>{const rows=[['demo_id','age','sex','condition','illustrative_risk_percent','risk_band','latest_observation'],...patients.map(p=>[p.id,p.age,p.sex,p.condition,p.risk,p.level,p.observation])];const csv=rows.map(row=>row.map(value=>`"${String(value).replaceAll('"','""')}"`).join(',')).join('\r\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));const a=document.createElement('a');a.href=url;a.download='clintel-fictional-demo-cohort.csv';a.click();URL.revokeObjectURL(url);showToast('Fictional sample CSV downloaded')});
$('#apiKeyButton').addEventListener('click',()=>{if(sessionStorage.getItem('clintel-api-key')){sessionStorage.removeItem('clintel-api-key');location.reload();return}$('#apiKeyError').textContent='';$('#apiKeyInput').value='';$('#apiKeyDialog').hidden=false;$('#apiKeyInput').focus()});
$('#closeApiDialog').addEventListener('click',()=>$('#apiKeyDialog').hidden=true);$('#cancelApiDialog').addEventListener('click',()=>$('#apiKeyDialog').hidden=true);
$('#apiKeyForm').addEventListener('submit',async e=>{e.preventDefault();const key=$('#apiKeyInput').value.trim();$('#apiKeyError').textContent='Checking key...';try{const response=await fetch('/api/patients',{headers:{'X-API-Key':key},cache:'no-store'});if(!response.ok)throw new Error('The API did not accept this key. Check it with your administrator.');sessionStorage.setItem('clintel-api-key',key);$('#apiKeyDialog').hidden=true;$('#apiKeyButton').textContent='Disconnect API';showToast('Research API key verified for this tab session');await connectResearchApi()}catch(error){$('#apiKeyError').textContent=error.message}});
document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();navigate('patients');$('#patientSearch').focus()}if(e.key==='Escape')$('#sidebar').classList.remove('open')});
connectResearchApi();
