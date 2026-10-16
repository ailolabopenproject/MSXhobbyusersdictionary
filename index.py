Python
<!doctype py>
<py lang="ja">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MSXかんたん辞書ver.1.3β</title>
<style>
:root{--bg:#09111e;--panel:#111e30;--panel2:#172941;--line:#2b405b;--text:#edf4ff;--muted:#9fb2cc;--a:#72e6dc;--b:#8eb7ff;--warn:#ffd18a}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top right,#172d48 0,#09111e 52%);color:var(--text);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
header{padding:24px max(16px,calc((100% - 1250px)/2));border-bottom:1px solid var(--line);background:#09111edb}header small{color:var(--a);letter-spacing:.18em}h1{font-size:clamp(1.5rem,4vw,2.3rem);margin:.2rem 0}header p{margin:0;color:var(--muted)}
main{max-width:1250px;margin:auto;padding:18px 16px 45px}.panel{border:1px solid var(--line);border-radius:15px;background:#111e30ed;padding:16px;margin-bottom:14px}
.top{display:grid;grid-template-columns:minmax(200px,1fr) auto;gap:12px;align-items:center}.search{width:100%;padding:13px 14px;border:1px solid var(--line);border-radius:10px;background:#081321;color:var(--text);font:inherit}
button,.filebtn{border:1px solid var(--line);border-radius:9px;padding:9px 12px;background:var(--panel2);color:var(--text);font:inherit;font-weight:650;cursor:pointer}button:hover,.filebtn:hover{border-color:var(--a)}button.primary{background:var(--a);color:#08151a;border-color:var(--a)}.actions{display:flex;flex-wrap:wrap;gap:7px}.tabs{display:flex;gap:7px;flex-wrap:wrap;margin:14px 0}.tab.active{background:#1c4b55;border-color:var(--a);color:#dffffb}
.stats{color:var(--muted);font-size:.88rem;margin-top:8px}.stats b{color:var(--text)}.layout{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:14px;align-items:start}.list{display:grid;gap:10px}.item{border:1px solid var(--line);border-radius:13px;padding:14px;background:linear-gradient(135deg,#14243a,#101b2b)}.item h3{margin:0 0 3px;font-size:1.07rem}.meta{font-size:.82rem;color:var(--b);margin-bottom:5px}.item p{margin:7px 0;white-space:pre-wrap;overflow-wrap:anywhere}.item a{color:var(--a)}.item .rowactions{display:flex;gap:7px;margin-top:11px;flex-wrap:wrap}.muted{color:var(--muted)}label{display:block;color:var(--muted);font-size:.86rem;margin:10px 0 4px}input,select,textarea{width:100%;border:1px solid var(--line);border-radius:8px;background:#081321;color:var(--text);padding:9px 10px;font:inherit}textarea{min-height:70px;resize:vertical}.formactions{display:flex;gap:8px;margin-top:13px}.formactions>*{flex:1}.hidden{display:none!important}.empty{text-align:center;border:1px dashed var(--line);padding:40px 15px;border-radius:13px;color:var(--muted)}.notice{font-size:.82rem;color:var(--muted);margin-top:12px;border-left:3px solid var(--warn);padding-left:10px}.chip{display:inline-block;padding:2px 7px;border:1px solid var(--line);border-radius:999px;font-size:.78rem;color:var(--muted);margin:2px 3px 2px 0}
footer{max-width:1250px;margin:auto;padding:0 16px 24px;color:var(--muted);font-size:.82rem}
@media(max-width:850px){.top{grid-template-columns:1fr}.layout{grid-template-columns:1fr}.editor{order:-1}.actions>*{flex:1}.item{padding:12px}}
</style>
</head>
<body>
<header><small>MSX · CONNECTED REFERENCE</small><h1>MSXかんたん辞書ver.1.3β</h1><p>機種・部品・部品番号・互換関係をつないで調べる、個人用データベース。</p></header>
<main>
<section class="panel">
 <div class="top"><div><input id="search" class="search" placeholder="型番・部品番号・メーカー・部品名・出典などを検索…"><div class="stats">収録 <b id="count">0</b>件　／　表示 <b id="shown">0</b>件　<span id="kind"></span></div></div>
 <div class="actions"><button class="primary" id="new">＋ 新規登録</button><label class="filebtn" style="margin:0">CSV/Excel取込<input id="import" type="file" accept=".csv,.xlsx,.xls" class="hidden"></label><button id="export">現在の表をCSV書出</button><button id="backup">全データJSON保存</button><label class="filebtn" style="margin:0">JSON復元<input id="restore" type="file" accept=".json" class="hidden"></label></div></div>
 <div class="tabs" id="tabs"></div>
</section>
<div class="layout">
 <section><div id="list" class="list"></div></section>
 <aside class="panel editor" id="editor"><h2 id="formtitle" style="margin:0">新しい情報を登録</h2><p class="muted" style="font-size:.84rem">表を選んで項目を入力します。IDは関連づけに使うため、できるだけ維持してください。</p>
 <form id="form"><div id="fields"></div><div class="formactions"><button class="primary" type="submit">保存</button><button type="button" id="clear">クリア</button></div><button type="button" id="delete" class="hidden" style="width:100%;margin-top:8px">この行を削除</button></form>
 <div class="notice">試作版はこのブラウザ内に保存します。端末間同期はありません。データ消失に備え、定期的に「全データJSON保存」を使ってください。Excel取込にはインターネット接続が必要です。</div>
 </aside>
</div>
</main>
<footer>試作版 0.2 · 元データの列構成を保持する設計 · 互換関係や確度は、元資料の記載を尊重して表示します。</footer>
<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
<script>
const TABLES={
 machines:{label:"機種",file:"msx_machines.csv",cols:[["id","ID","text"],["maker","メーカー","text"],["model","型番","text"],["generation","世代","text"],["year","発売年","text"],["region","地域","text"],["predecessor","前身機種ID","text"],["power","電源","textarea"],["video_out","映像出力","textarea"],["notes","メモ","textarea"],["source_url","出典URL","url"],["source_note","出典メモ","textarea"],["source_type","出典種別","text"]]},
 parts:{label:"部品",file:"msx_parts.csv",cols:[["id","ID","text"],["category","分類","text"],["name","部品名","text"],["spec","仕様","textarea"],["typical_failure","よくある故障","textarea"],["source_url","出典URL","url"],["source_note","出典メモ","textarea"],["source_type","出典種別","text"]]},
 numbers:{label:"部品番号",file:"msx_part_numbers.csv",cols:[["part_id","部品ID","text"],["maker","メーカー","text"],["part_number","部品番号","text"],["note","備考","textarea"],["source_note","出典メモ","textarea"]]},
 equivalents:{label:"互換関係",file:"msx_part_equivalents.csv",cols:[["part_a","部品A ID","text"],["part_b","部品B ID","text"],["relation","関係","text"],["confidence","確度","text"],["note","注記","textarea"],["source_url","出典URL","url"],["source_note","出典メモ","textarea"]]},
 links:{label:"機種と部品",file:"msx_links.csv",cols:[["machine_id","機種ID","text"],["part_id","部品ID","text"],["relation","関係","text"],["confidence","確度","text"],["note","注記","textarea"],["source_url","出典URL","url"],["source_note","出典メモ","textarea"]]}
};
const KEY="msx-connected-dictionary-v2";let data={},active="machines",editing=null;
const $=id=>document.getElementById(id);
function blank(){for(const k of Object.keys(TABLES))data[k]=[]}
function norm(s){s=String(s??"").normalize("NFKC").toLowerCase().replace(/ソニー/g,"sony").replace(/パナソニック|松下/g,"panasonic").replace(/カワイ|河合/g,"kawai").replace(/ミツミ/g,"mitsumi");return s.replace(/[\s\-_‐−–ー・/]/g,"")}
function uid(prefix){return prefix+"-"+Date.now().toString(36)+"-"+Math.random().toString(36).slice(2,7)}
function save(){localStorage.setItem(KEY,JSON.stringify(data));render()}
function esc(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function renderTabs(){$("tabs").innerHTML=Object.entries(TABLES).map(([k,t])=>`<button class="tab ${k===active?"active":""}" data-tab="${k}">${t.label} <span class="chip">${data[k].length}</span></button>`).join("");document.querySelectorAll("[data-tab]").forEach(b=>b.onclick=()=>{active=b.dataset.tab;clearForm();render()})}
function labelValue(k,v){if(!v)return "";if(k.endsWith("url")||k==="source_url"){return `<a href="${esc(v)}" target="_blank" rel="noopener noreferrer">出典を開く ↗</a>`}return `<p><b>${esc(TABLES[active].cols.find(c=>c[0]===k)?.[1]||k)}：</b>${esc(v)}</p>`}
function card(row){
 const t=TABLES[active], titleKey=({machines:"model",parts:"name",numbers:"part_number",equivalents:"relation",links:"relation"})[active];
 const title=row[titleKey]||row.id||row.part_id||"（名称未設定）";
 const sub=active==="machines"?`${row.maker||""} · ${row.generation||""} · ${row.year||""}`:active==="parts"?`${row.category||""} · ID: ${row.id||""}`:active==="numbers"?`${row.maker||""} · 部品ID: ${row.part_id||""}`:active==="equivalents"?`${row.part_a||""} ↔ ${row.part_b||""} · ${row.confidence||""}`:`${row.machine_id||""} → ${row.part_id||""} · ${row.confidence||""}`;
 let keys=active==="machines"?["power","video_out","notes","source_url"]:active==="parts"?["spec","typical_failure","source_url"]:active==="numbers"?["note","source_note"]:active==="equivalents"?["note","source_url"]:["note","source_url"];
 return `<article class="item"><div class="meta">${esc(sub)}</div><h3>${esc(title)}</h3>${keys.map(k=>labelValue(k,row[k])).join("")}<div class="rowactions"><button data-edit="${esc(row.__key)}">編集</button></div></article>`;
}
function render(){
 renderTabs();const q=norm($("search").value);const rows=data[active].map((r,i)=>({...r,__key:String(i)})).filter(r=>!q||TABLES[active].cols.some(c=>norm(r[c[0]]).includes(q)));
 $("count").textContent=Object.values(data).reduce((n,a)=>n+a.length,0);$("shown").textContent=rows.length;$("kind").textContent="・"+TABLES[active].label;
 $("list").innerHTML=rows.length?rows.map(card).join(""):`<div class="empty"><div style="font-size:2rem">⌕</div><b>${q?"一致する情報がありません":TABLES[active].label+"データがありません"}</b><p>${q?"キーワードを変えて検索してください。":"CSV/Excelを取り込むか、新規登録してください。"}</p></div>`;
 document.querySelectorAll("[data-edit]").forEach(b=>b.onclick=()=>edit(+b.dataset.edit));
}
function clearForm(){editing=null;$("form").reset();$("formtitle").textContent="新しい情報を登録";$("delete").classList.add("hidden");buildFields({})}
function buildFields(row){$("fields").innerHTML=TABLES[active].cols.map(([k,l,type])=>`<label for="f_${k}">${l}${k==="id"?"（関連づけ用）":""}</label>${type==="textarea"?`<textarea id="f_${k}">${esc(row[k]||"")}</textarea>`:`<input id="f_${k}" type="${type}" value="${esc(row[k]||"")}" ${k==="id"&&editing!==null?"readonly":""}>`}`).join("")}
function edit(i){editing=i;const row=data[active][i];$("formtitle").textContent="情報を編集";$("delete").classList.remove("hidden");buildFields(row);$("editor").scrollIntoView({behavior:"smooth",block:"start"})}
$("form").onsubmit=e=>{e.preventDefault();let row={};for(const [k] of TABLES[active].cols)row[k]=$("f_"+k).value.trim();if(active==="machines"||active==="parts"){if(!row.id)row.id=uid(active==="machines"?"machine":"part")}if(active==="equivalents"||active==="links"){if(!row.part_a&&!row.machine_id){alert("関連づけるIDを入力してください");return}}
 if(active==="machines"&&!row.model){alert("型番を入力してください");return}if(active==="parts"&&!row.name){alert("部品名を入力してください");return}
 if(editing!==null){data[active][editing]=row}else data[active].unshift(row);save();clearForm()};
$("new").onclick=()=>{clearForm();$("editor").scrollIntoView({behavior:"smooth",block:"start"})};$("clear").onclick=clearForm;
$("delete").onclick=()=>{if(editing!==null&&confirm("この行を削除しますか？関連表の参照は自動削除されません。")){data[active].splice(editing,1);save();clearForm()}};
$("search").oninput=render;
function parseCSV(text){let rows=[],row=[],field="",quoted=false;for(let i=0;i<text.length;i++){const c=text[i];if(quoted){if(c==='"'&&text[i+1]==='"'){field+='"';i++}else if(c==='"')quoted=false;else field+=c}else{if(c==='"')quoted=true;else if(c===","){row.push(field);field=""}else if(c==="\n"){row.push(field.replace(/\r$/,""));rows.push(row);row=[];field=""}else field+=c}}if(field.length||row.length){row.push(field.replace(/\r$/,""));rows.push(row)}return rows}
async function fileRows(file){const buf=await file.arrayBuffer();if(/\.(xlsx|xls)$/i.test(file.name)){if(!window.XLSX)throw Error("Excelライブラリを読み込めません。CSV形式で保存してお試しください。");const wb=XLSX.read(buf,{type:"array"});return XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]],{defval:""})}const text=new TextDecoder("utf-8").decode(buf).replace(/^\uFEFF/,"");const rows=parseCSV(text);if(rows.length<2)return [];const headers=rows.shift().map(s=>s.trim());return rows.filter(r=>r.some(v=>v.trim())).map(r=>Object.fromEntries(headers.map((h,i)=>[h,r[i]??""])))}
$("import").onchange=async e=>{const f=e.target.files[0];if(!f)return;try{let rows=await fileRows(f);const t=TABLES[active];rows=rows.map(r=>{const o={};for(const [k,label] of t.cols){const match=Object.keys(r).find(h=>h.trim()===k||h.trim()===label);o[k]=match?String(r[match]??"").trim():""}return o}).filter(r=>t.cols.some(([k])=>r[k]));if(!rows.length)throw Error("列見出しが合わないか、データ行がありません。現在の表「"+t.label+"」に対応するCSVを選んでください。");if(confirm(`${t.label}を${rows.length}件追加しますか？既存データは残します。`)){data[active]=[...rows,...data[active]];save();alert("取り込みました。")} }catch(err){alert("取込失敗：\\n"+err.message)}finally{e.target.value=""}};
function download(name,content,type){const blob=new Blob([content],{type});const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
$("export").onclick=()=>{const t=TABLES[active],headers=t.cols.map(c=>c[0]);const csv=[headers,...data[active].map(r=>headers.map(h=>r[h]||""))].map(row=>row.map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(",")).join("\r\n");download(t.file,"\uFEFF"+csv,"text/csv;charset=utf-8")};
$("backup").onclick=()=>download("msx-dictionary-backup.json",JSON.stringify(data,null,2),"application/json;charset=utf-8");
$("restore").onchange=async e=>{const f=e.target.files[0];if(!f)return;try{const x=JSON.parse(await f.text());for(const k of Object.keys(TABLES))if(!Array.isArray(x[k]))throw Error("バックアップ内に必要な表がありません");if(confirm("全データをバックアップの内容で置き換えますか？")){data=x;save();clearForm();alert("復元しました")}}catch(err){alert("復元失敗：\\n"+err.message)}finally{e.target.value=""}};
blank();try{const x=JSON.parse(localStorage.getItem(KEY)||"{}");for(const k of Object.keys(TABLES))if(Array.isArray(x[k]))data[k]=x[k]}catch{}render();clearForm();
</script>
</body>
</py>
</div>
