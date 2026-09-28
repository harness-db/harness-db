"""Build a self-contained, click-through HTML form for the blinded human correctness audit.

    python scripts/make_audit_form.py            # writes data/audit/human_audit_form.html

The form embeds data/audit/human_sheet.csv verbatim - the blinded sheet, which by construction
(tests/test_human_audit.py) carries no model value, state, evidence or confidence - and nothing else.
It never reads model_answers.csv or data/systems.json. The coder clicks a state, a value and a
confidence per cell, pastes one verbatim quote, and exports a CSV with exactly the sheet's columns and
row order, to be saved over data/audit/human_sheet.csv and checked with
`python scripts/human_audit.py --analyse`. Minutes are timed per system and split evenly over its rows.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHEET = ROOT / "data" / "audit" / "human_sheet.csv"
OUT = ROOT / "data" / "audit" / "human_audit_form.html"

FORBIDDEN = ("model_value", "model_state", "model_evidence", "model_confidence", "model_note")


def main() -> None:
    with open(SHEET, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        header = list(reader.fieldnames or [])
        rows = list(reader)
    bad = [c for c in header if c.startswith(FORBIDDEN)]
    if bad:
        raise SystemExit(f"refusing to build: sheet carries model columns {bad}")
    if any((r.get("human_state") or "").strip() for r in rows):
        raise SystemExit("refusing to build: the sheet already carries human entries")
    payload = json.dumps({"header": header, "rows": rows}, ensure_ascii=True).replace("</", "<\\/")
    OUT.write_text(TEMPLATE.replace("/*__DATA__*/null", payload), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(rows)} cells, "
          f"{len({r['system_id'] for r in rows})} systems")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Harness Audit Form</title>
<style>
:root{--bg:#f7f7f5;--panel:#ffffff;--ink:#1d1d1b;--muted:#5f5f5a;--line:#dcdcd6;--accent:#2f5d8a;
--accent-soft:#e3ecf5;--ok:#2e7d4f;--ok-soft:#e2f2e8;--warn:#9a5b00;--warn-soft:#fbefd9;--bad:#a33a2e;
--bad-soft:#f8e3e0;--chip:#f0f0ec}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161615;--panel:#1f1f1d;
--ink:#ececE8;--muted:#a6a6a0;--line:#3a3a36;--accent:#8db6e0;--accent-soft:#23313f;--ok:#7fcf9e;
--ok-soft:#1f3327;--warn:#e7b35a;--warn-soft:#3a2f1b;--bad:#ef8f83;--bad-soft:#3b2220;--chip:#2a2a27}}
:root[data-theme="dark"]{--bg:#161615;--panel:#1f1f1d;--ink:#ececE8;--muted:#a6a6a0;--line:#3a3a36;
--accent:#8db6e0;--accent-soft:#23313f;--ok:#7fcf9e;--ok-soft:#1f3327;--warn:#e7b35a;--warn-soft:#3a2f1b;
--bad:#ef8f83;--bad-soft:#3b2220;--chip:#2a2a27}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--accent)}
header{position:sticky;top:0;z-index:5;background:var(--panel);border-bottom:1px solid var(--line);
padding:10px 16px;display:flex;flex-wrap:wrap;gap:10px 16px;align-items:center}
header h1{font-size:17px;margin:0 8px 0 0}
.bar{flex:1 1 220px;min-width:180px}
.bar .track{height:8px;background:var(--chip);border-radius:4px;overflow:hidden}
.bar .fill{height:100%;background:var(--ok);width:0}
.bar small{color:var(--muted)}
button,.btn{font:inherit;border:1px solid var(--line);background:var(--panel);color:var(--ink);
border-radius:6px;padding:6px 12px;cursor:pointer}
button.primary{background:var(--accent);border-color:var(--accent);color:var(--panel)}
button:focus-visible,input:focus-visible,textarea:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
input[type=text],input[type=number],textarea{font:inherit;color:var(--ink);background:var(--bg);
border:1px solid var(--line);border-radius:6px;padding:6px 8px;width:100%}
textarea{min-height:64px;resize:vertical}
main{display:grid;grid-template-columns:260px 1fr;gap:16px;padding:16px;max-width:1300px;margin:0 auto}
@media (max-width:820px){main{grid-template-columns:1fr}nav{max-height:220px}}
nav{background:var(--panel);border:1px solid var(--line);border-radius:8px;overflow:auto;max-height:calc(100vh - 110px);position:sticky;top:78px}
nav button{display:flex;justify-content:space-between;gap:8px;width:100%;text-align:left;border:0;
border-bottom:1px solid var(--line);border-radius:0;padding:8px 12px;background:transparent}
nav button.cur{background:var(--accent-soft)}
nav .st{font-size:12px;color:var(--muted);white-space:nowrap}
nav .st.done{color:var(--ok)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:16px;margin-bottom:16px}
.help summary{cursor:pointer;font-weight:600}
.help ol{padding-left:20px;margin:8px 0}.help li{margin:4px 0}
.sys h2{margin:0 0 4px;font-size:20px}
.meta{display:grid;grid-template-columns:130px 1fr;gap:4px 12px;font-size:14px;margin:8px 0}
.meta div:nth-child(odd){color:var(--muted)}
.pinwarn{background:var(--warn-soft);color:var(--warn);border-radius:6px;padding:8px 10px;margin:8px 0;font-size:14px}
.timer{font-variant-numeric:tabular-nums;color:var(--muted);font-size:14px}
.cell{border:1px solid var(--line);border-radius:8px;padding:14px;margin:14px 0;background:var(--panel)}
.cell.complete{border-color:var(--ok)}
.cell h3{margin:0;font-size:17px;display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}
.badge{font-size:12px;font-weight:600;border-radius:10px;padding:2px 8px;background:var(--chip);color:var(--muted)}
.badge.ok{background:var(--ok-soft);color:var(--ok)}.badge.bad{background:var(--bad-soft);color:var(--bad)}
.rule{font-size:14px;color:var(--muted);margin:6px 0 10px}
.step{margin:12px 0 4px;font-weight:600;font-size:14px}
.opts{display:flex;flex-wrap:wrap;gap:8px}
.opt{border:1px solid var(--line);border-radius:8px;padding:8px 10px;cursor:pointer;background:var(--bg);
flex:1 1 200px;max-width:100%;text-align:left}
.opt b{display:block;font-size:14px}.opt span{display:block;font-size:13px;color:var(--muted)}
.opt[aria-pressed=true]{border-color:var(--accent);background:var(--accent-soft);box-shadow:inset 0 0 0 1px var(--accent)}
.hint{font-size:13px;color:var(--muted);margin:4px 0}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:10px}@media (max-width:640px){.row2{grid-template-columns:1fr}}
.navbtns{display:flex;justify-content:space-between;gap:10px;margin-top:10px}
.toast{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);background:var(--ink);color:var(--panel);
padding:8px 14px;border-radius:6px;font-size:14px;display:none;z-index:9}
</style>
</head>
<body>
<header>
  <h1>HARNESS-DB human audit</h1>
  <label>Coder id <input type="text" id="coder" style="width:70px" value="c1" aria-label="Coder id"></label>
  <div class="bar"><div class="track"><div class="fill" id="fill"></div></div><small id="prog"></small></div>
  <button id="exportBtn" class="primary">Export CSV</button>
  <label class="btn">Resume from CSV<input type="file" id="importFile" accept=".csv" hidden></label>
</header>
<main>
  <nav id="nav" aria-label="Systems"></nav>
  <section>
    <details class="panel help" id="help" open>
      <summary>How to do this (read once, about 3 minutes)</summary>
      <ol>
        <li><b>Your reading must be your own.</b> Do not open <code>model_answers.csv</code>, <code>data/systems.json</code>, <code>data/coded/</code> or the explorer. This form contains none of the dataset's answers.</li>
        <li><b>Per system:</b> open the repository at the <b>pinned version</b> shown (the tag or commit, not <code>main</code>) and the listed paper(s). These are your only sources: no blogs, issues, forks or later versions. Skim the README, config/settings files, the CLI entry point, the tool registry and the main agent loop once; all 7 questions use them. A timer runs for the open system (also while you read the repo in other tabs) and fills the minutes for you; press Pause timer for breaks.</li>
        <li><b>Per question, spend at most 8 minutes</b>, then pick the state:
          <ul>
            <li><b>Found it</b>: you can point at code or a sentence that shows the value.</li>
            <li><b>Found it, and it is absent</b>: pick the absence value (<code>none</code>, or <code>open</code> for network) <u>only if</u> you opened the place where the feature would be declared (config schema, CLI flags, tool registry, the run loop, a documented feature list) and it is not there. Paste what you checked, e.g. <code>grep -rni network src/ -&gt; 0 hits</code>.</li>
            <li><b>Not reported</b>: the sources have no such place (only a paper, a thin README, a missing or truncated repository). A text that never mentions the feature is <u>not</u> evidence the feature is absent.</li>
            <li><b>Can't settle</b>: 8 minutes are up; write why in the note.</li>
          </ul></li>
        <li><b>Code the default configuration.</b> For self-verification (the one multi-select question) also tick every check the shipped configuration can switch on without code changes. Never tick <code>none</code> with anything else.</li>
        <li><b>Evidence:</b> paste the exact code line or sentence (not a paraphrase). Where: <code>path/file.py:LINE@shorthash</code> or <code>arXiv id Sec. N</code>.</li>
        <li><b>Confidence:</b> High = stated outright or on the cited line; Medium = inferred from nearby code, a default or a figure (the most you can give an absence value unless the docs state it); Low = inferred from prose.</li>
        <li>Progress saves in this browser automatically, but <b>press Export CSV at the end of every session</b> and keep the file. When all 350 cells are done, save the export as <code>data/audit/human_sheet.csv</code> (replace the file) and run <code>python scripts/human_audit.py --analyse</code>.</li>
      </ol>
      <p class="hint">Workload: 50 systems x 7 questions. Expect about 45 minutes per system; work in sessions of 2-3 hours.</p>
    </details>
    <div id="sys"></div>
  </section>
</main>
<div class="toast" id="toast" role="status"></div>
<script>
const DATA = /*__DATA__*/null;
const HUMAN = ["human_state","human_value","human_evidence_quote","human_locator","human_confidence","human_minutes","human_note","coder_id"];
const KEY = "harnessdb-human-audit-v1";
const rows = DATA.rows;
const systems = [];
const bySys = {};
rows.forEach(r => { if(!bySys[r.system_id]){ bySys[r.system_id]=[]; systems.push(r.system_id);} bySys[r.system_id].push(r); });

let state = { cells:{}, seconds:{}, current:systems[0], coder:"c1" };
function load(){ try{ const s = JSON.parse(localStorage.getItem(KEY)||"null"); if(s&&s.cells){ state = Object.assign(state,s); } }catch(e){} }
function save(){ try{ localStorage.setItem(KEY, JSON.stringify(state)); }catch(e){} }
function cell(id){ return state.cells[id] || (state.cells[id]={state:"",values:[],quote:"",locator:"",confidence:"",note:""}); }

const DIM_HELP = {
  network_policy:"Can the agent's actions reach the network during a run?",
  replayability:"Can a finished run be re-run from what was recorded?",
  filesystem_access:"What may the agent read or write inside its execution boundary?",
  rollback:"Can changes made during the run be reverted?",
  state_persistence:"Can an interrupted run be continued?",
  multi_agent_topology:"How many agents, arranged how, in the default configuration?",
  self_verification:"Which checks does the harness itself apply to the agent's work?"
};
function glosses(r){ const m={}; (r.value_glosses||"").split(" ; ").forEach(g=>{ const i=g.indexOf(":"); if(i>0) m[g.slice(0,i).trim()]=g.slice(i+1).trim(); }); return m; }
function isMulti(r){ return /^yes/i.test(r.multi_valued||""); }
function absenceVals(r){ return (r.permitted_values||"").split("|").filter(v=>v==="none"||(r.dim_key==="network_policy"&&v==="open")); }

function problems(r){
  const c = cell(r.cell_id), p=[];
  if(!c.state) return ["pick a state"];
  if(c.state==="coded"){
    if(!c.values.length) p.push("pick a value");
    if(!c.quote.trim()) p.push("paste the evidence");
    if(!c.confidence) p.push("pick confidence");
  }
  if(c.state==="unresolved" && !c.note.trim()) p.push("say why in the note");
  return p;
}
function done(r){ return problems(r).length===0; }
function sysDone(s){ return bySys[s].every(done); }

function el(tag, attrs={}, ...kids){ const e=document.createElement(tag); for(const [k,v] of Object.entries(attrs)){ if(k==="class") e.className=v; else if(k.startsWith("on")) e.addEventListener(k.slice(2),v); else e.setAttribute(k,v);} kids.flat().forEach(k=>{ if(k!=null) e.append(k.nodeType?k:document.createTextNode(k)); }); return e; }

function renderNav(){
  const nav=document.getElementById("nav"); nav.innerHTML="";
  systems.forEach((s,i)=>{ const n=bySys[s].filter(done).length, r0=bySys[s][0];
    nav.append(el("button",{class:s===state.current?"cur":"",onclick:()=>go(s)},
      el("span",{}, (i+1)+". "+r0.system_name), el("span",{class:"st"+(n===7?" done":"")}, n===7?"done":n+"/7"))); });
  const total=rows.filter(done).length;
  document.getElementById("fill").style.width=(100*total/rows.length)+"%";
  document.getElementById("prog").textContent=`${total} of ${rows.length} questions done, ${systems.filter(sysDone).length} of ${systems.length} systems`;
}

function pinLink(r){
  const m=(r.pinned_version||"").match(/@\s*([0-9a-f]{7,40})/i);
  if(m && r.repo_url && /github\.com/.test(r.repo_url)) return r.repo_url.replace(/\/$/,"")+"/tree/"+m[1];
  return r.repo_url||"";
}
function paperLinks(r){
  const out=[]; const re=/'([^']*)'\s*<([^>]+)>/g; let m;
  while((m=re.exec(r.paper_refs||""))) out.push(el("div",{}, el("a",{href:m[2],target:"_blank",rel:"noopener"}, m[1]||m[2])));
  return out.length?out:[el("div",{},"(none listed)")];
}

function optBtn(label, sub, pressed, onclick){ return el("button",{class:"opt","aria-pressed":pressed?"true":"false",type:"button",onclick}, el("b",{},label), sub?el("span",{},sub):null); }

function renderCell(r, idx){
  const c=cell(r.cell_id), g=glosses(r), multi=isMulti(r), vals=(r.permitted_values||"").split("|"), abs=absenceVals(r);
  const box=el("div",{class:"cell"+(done(r)?" complete":""),id:"c_"+idx});
  const pr=problems(r);
  box.append(el("h3",{}, `${idx+1}. ${r.dim_name} (${r.dim_id})`, el("span",{class:"badge "+(pr.length?(c.state?"bad":""):"ok")}, pr.length?(c.state?"missing: "+pr.join(", "):"not started"):"complete")));
  box.append(el("div",{class:"rule"}, el("b",{}, DIM_HELP[r.dim_key]||""), " ", r.decision_rule));
  box.append(el("div",{class:"step"},"Step 1. What did the sources show?"));
  const states=[["coded","Found it","I can point at code or text for a value (including an absence I verified)."],
    ["not_reported","Not reported","The sources have no place where this would be declared."],
    ["unresolved","Can't settle","8 minutes are up. Say why in the note."]];
  box.append(el("div",{class:"opts"}, states.map(([v,l,s])=>optBtn(l,s,c.state===v,()=>{ c.state=v; if(v!=="coded"){c.values=[];} save(); rerender(idx); }))));
  if(c.state==="coded"){
    box.append(el("div",{class:"step"}, multi?"Step 2. Which values? (tick every one that applies)":"Step 2. Which value?"));
    box.append(el("div",{class:"opts"}, vals.map(v=>{
      const sub=(g[v]||"")+(abs.includes(v)?"  Only if you opened where it would be declared and it is missing.":"");
      return optBtn(v, sub, c.values.includes(v), ()=>{
        if(!multi) c.values=[v];
        else if(v==="none") c.values=c.values.includes("none")?[]:["none"];
        else { c.values=c.values.filter(x=>x!=="none"); c.values=c.values.includes(v)?c.values.filter(x=>x!==v):[...c.values,v]; }
        save(); rerender(idx); }); })));
    box.append(el("div",{class:"step"},"Step 3. Evidence"));
    const q=el("textarea",{placeholder:"Paste the exact code line or sentence. For an absence value, paste the place you opened and the search you ran, e.g. grep -rni network src/ -> 0 hits","aria-label":"Evidence quote"}); q.value=c.quote;
    q.addEventListener("input",()=>{ c.quote=q.value; save(); refreshBadge(idx); });
    const loc=el("input",{type:"text",placeholder:"Where: path/file.py:LINE@shorthash  or  arXiv id Sec. N","aria-label":"Locator"}); loc.value=c.locator;
    loc.addEventListener("input",()=>{ c.locator=loc.value; save(); });
    box.append(q, el("div",{style:"height:6px"}), loc);
    box.append(el("div",{class:"step"},"Step 4. Confidence"));
    box.append(el("div",{class:"opts"}, [["high","High","Stated outright, or on the line you cited."],["medium","Medium","Inferred from nearby code, a default or a figure. The most an absence value can get unless the docs state it."],["low","Low","Inferred from prose."]]
      .map(([v,l,s])=>optBtn(l,s,c.confidence===v,()=>{ c.confidence=v; save(); rerender(idx); }))));
  } else if(c.state==="not_reported"){
    box.append(el("div",{class:"hint"},"Optional: where did you look? (helps later review)"));
    const loc=el("input",{type:"text",placeholder:"e.g. only the paper; repo has no config or run loop","aria-label":"Where you looked"}); loc.value=c.locator;
    loc.addEventListener("input",()=>{ c.locator=loc.value; save(); }); box.append(loc);
  }
  box.append(el("div",{class:"step"}, c.state==="unresolved"?"Note (required: why it could not be settled)":"Note (optional)"));
  const n=el("input",{type:"text",placeholder:"Anything a reviewer should know: paper and repo disagree, closest value, etc.","aria-label":"Note"}); n.value=c.note;
  n.addEventListener("input",()=>{ c.note=n.value; save(); refreshBadge(idx); }); box.append(n);
  return box;
}

let cellsEls=[];
function refreshBadge(idx){ const r=bySys[state.current][idx], b=cellsEls[idx].querySelector(".badge"), pr=problems(r);
  b.className="badge "+(pr.length?"bad":"ok"); b.textContent=pr.length?"missing: "+pr.join(", "):"complete";
  cellsEls[idx].classList.toggle("complete",!pr.length); renderNav(); }
function rerender(idx){ const r=bySys[state.current][idx]; const nb=renderCell(r,idx); cellsEls[idx].replaceWith(nb); cellsEls[idx]=nb; renderNav(); }

function renderSys(){
  const s=state.current, rs=bySys[s], r0=rs[0], i=systems.indexOf(s);
  const host=document.getElementById("sys"); host.innerHTML="";
  const top=el("div",{class:"panel sys"});
  top.append(el("h2",{}, `System ${i+1} of ${systems.length}: ${r0.system_name}`));
  const nopin=/no pin/i.test(r0.pinned_version||"");
  top.append(el("div",{class:"meta"},
    el("div",{},"Pinned version"), el("div",{}, r0.pinned_version||"(none)"),
    el("div",{},"Repository"), el("div",{}, r0.repo_url?el("a",{href:pinLink(r0),target:"_blank",rel:"noopener"}, pinLink(r0)):"(no repository listed: use the paper only)"),
    el("div",{},"Paper(s)"), el("div",{}, paperLinks(r0)),
    el("div",{},"Time on system"), el("div",{}, el("span",{class:"timer",id:"timer"},""), " ", el("button",{type:"button",id:"pauseBtn",onclick:togglePause}, paused?"Resume timer":"Pause timer"))));
  if(nopin) top.append(el("div",{class:"pinwarn"},"No pin is recorded. Use the latest tag on or before 2026-08-31, otherwise the latest default-branch commit on or before that date, and put that commit in each Where field."));
  host.append(top);
  cellsEls=rs.map((r,idx)=>renderCell(r,idx)); cellsEls.forEach(c=>host.append(c));
  host.append(el("div",{class:"navbtns"},
    el("button",{onclick:()=>go(systems[Math.max(0,i-1)]),type:"button"},"Previous system"),
    el("button",{class:"primary",onclick:()=>go(systems[Math.min(systems.length-1,i+1)]),type:"button"},"Next system")));
  tick(); renderNav();
}
function go(s){ state.current=s; save(); renderSys(); window.scrollTo(0,0); }

function fmt(sec){ const m=Math.floor(sec/60), s=sec%60; return `${m} min ${String(s).padStart(2,"0")} s${paused?" (paused)":""}, split over the 7 questions. It keeps running while you read the repo in another tab; pause it for breaks.`; }
function tick(){ const t=document.getElementById("timer"); if(t) t.textContent=fmt(state.seconds[state.current]||0); }
let paused=false;
setInterval(()=>{ if(!paused){ state.seconds[state.current]=(state.seconds[state.current]||0)+1; tick(); if((state.seconds[state.current]%10)===0) save(); } },1000);
function togglePause(){ paused=!paused; const b=document.getElementById("pauseBtn"); if(b) b.textContent=paused?"Resume timer":"Pause timer"; tick(); }

function csvField(v){ v=v==null?"":String(v); return /[",\r\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v; }
function buildCSV(){
  const coder=(document.getElementById("coder").value||"").trim();
  const lines=[DATA.header.map(csvField).join(",")];
  rows.forEach(r=>{
    const c=state.cells[r.cell_id]; const o=Object.assign({},r);
    HUMAN.forEach(h=>o[h]="");
    if(c && c.state){
      o.human_state=c.state;
      o.human_value=c.state==="coded"?c.values.join("|"):"";
      o.human_evidence_quote=c.state==="coded"?c.quote.trim():"";
      o.human_locator=c.locator.trim();
      o.human_confidence=c.state==="coded"?c.confidence:"";
      const sec=state.seconds[r.system_id]||0; o.human_minutes=sec?(Math.round(sec/60/7*10)/10).toString():"";
      o.human_note=c.note.trim(); o.coder_id=coder;
    }
    lines.push(DATA.header.map(h=>csvField(o[h])).join(","));
  });
  return lines.join("\r\n")+"\r\n";
}
function toast(msg){ const t=document.getElementById("toast"); t.textContent=msg; t.style.display="block"; setTimeout(()=>t.style.display="none",3500); }
document.getElementById("exportBtn").addEventListener("click",()=>{
  const incomplete=rows.filter(r=>state.cells[r.cell_id]&&state.cells[r.cell_id].state&&!done(r)).length;
  const blob=new Blob([buildCSV()],{type:"text/csv;charset=utf-8"});
  const a=document.createElement("a"); a.href=URL.createObjectURL(blob); a.download="human_sheet.csv"; document.body.append(a); a.click(); a.remove();
  toast(incomplete?`Exported. ${incomplete} started question(s) are still missing something; the analysis will reject them until fixed.`:"Exported human_sheet.csv");
});
document.getElementById("coder").addEventListener("input",e=>{ state.coder=e.target.value; save(); });

function parseCSV(text){
  const out=[]; let row=[], f="", q=false;
  for(let i=0;i<text.length;i++){ const ch=text[i];
    if(q){ if(ch==='"'){ if(text[i+1]==='"'){f+='"';i++;} else q=false; } else f+=ch; }
    else if(ch==='"') q=true; else if(ch===","){ row.push(f); f=""; }
    else if(ch==="\n"){ row.push(f.replace(/\r$/,"")); out.push(row); row=[]; f=""; } else f+=ch; }
  if(f.length||row.length){ row.push(f); out.push(row); }
  return out;
}
document.getElementById("importFile").addEventListener("change",e=>{
  const file=e.target.files[0]; if(!file) return;
  file.text().then(t=>{
    const recs=parseCSV(t.replace(/^﻿/,"")); const hdr=recs.shift(); const ix=Object.fromEntries(hdr.map((h,i)=>[h,i]));
    let n=0;
    recs.forEach(v=>{ const id=v[ix.cell_id]; if(!id||!bySys[v[ix.system_id]]) return; const st=(v[ix.human_state]||"").trim(); if(!st) return;
      state.cells[id]={state:st,values:(v[ix.human_value]||"").split("|").map(x=>x.trim()).filter(Boolean),quote:v[ix.human_evidence_quote]||"",
        locator:v[ix.human_locator]||"",confidence:v[ix.human_confidence]||"",note:v[ix.human_note]||""};
      const m=parseFloat(v[ix.human_minutes]); if(m&&!state.seconds[v[ix.system_id]]) state.seconds[v[ix.system_id]]=Math.round(m*60*7);
      if(v[ix.coder_id]) state.coder=v[ix.coder_id]; n++; });
    save(); document.getElementById("coder").value=state.coder; renderSys(); toast(`Resumed ${n} answered question(s) from ${file.name}`);
  });
});

load();
if(!bySys[state.current]) state.current=systems[0];
document.getElementById("coder").value=state.coder||"c1";
if(Object.keys(state.cells).length) document.getElementById("help").open=false;
renderSys();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
