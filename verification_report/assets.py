"""정적 자산(CSS, JS). 외부 CDN 없이 오프라인에서 열린다."""

CSS = """
:root{
  --bg:#f5f7fa; --surface:#ffffff; --text:#1b2430; --muted:#5b6675; --border:#dde2e8; --track:#e5e9ee;
  --pass:#1a7f4b; --fail:#c62828; --warn:#a85f00; --info:#2563eb; --accent:#2563eb;
  --pass-bg:#e3f4ea; --fail-bg:#fbe5e5; --warn-bg:#fff0d6; --na-bg:#eceff3;
  --sev-error:#c62828; --sev-warning:#d98200; --sev-style:#2563eb; --sev-performance:#7c3aed;
  --sev-portability:#0e8aa6; --sev-information:#6b7685;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#0f141a; --surface:#171e27; --text:#e6ebf1; --muted:#9aa6b4; --border:#2a3441; --track:#2b3542;
    --pass:#4cc38a; --fail:#ff7b7b; --warn:#f0b441; --info:#6ea8ff; --accent:#6ea8ff;
    --pass-bg:#173326; --fail-bg:#3a1c1f; --warn-bg:#3a2d12; --na-bg:#232c37;
    --sev-error:#ff7b7b; --sev-warning:#f0b441; --sev-style:#6ea8ff; --sev-performance:#a78bfa;
    --sev-portability:#38bdf8; --sev-information:#8d99a8;
  }
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 -apple-system,"Segoe UI","Malgun Gothic","Apple SD Gothic Neo",Roboto,sans-serif}
a{color:var(--accent)}
.wrap{max-width:1240px;margin:0 auto;padding:0 16px 48px}
nav.top{position:sticky;top:0;z-index:5;background:var(--surface);border-bottom:1px solid var(--border)}
nav.top .wrap{display:flex;gap:4px;flex-wrap:wrap;padding-top:8px;padding-bottom:8px}
nav.top a{display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:6px;color:var(--text);text-decoration:none;font-weight:500}
nav.top a:hover{background:var(--track)}
nav.top a[aria-current="page"]{background:var(--accent);color:#fff}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;background:var(--muted)}
.dot.pass{background:var(--pass)}.dot.fail{background:var(--fail)}
nav.top a[aria-current="page"] .dot{box-shadow:0 0 0 2px #fff}
header.page{padding:24px 0 8px}
header.page h1{margin:0 0 8px;font-size:24px}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{background:var(--surface);border:1px solid var(--border);border-radius:999px;padding:3px 12px;font-size:13px;color:var(--muted)}
.chip b{color:var(--text);font-weight:600}
.banner{display:flex;align-items:center;gap:12px;margin:16px 0;padding:14px 18px;border-radius:10px;border:1px solid var(--border);background:var(--surface);font-size:16px}
.banner.pass{background:var(--pass-bg);border-color:var(--pass)}
.banner.fail{background:var(--fail-bg);border-color:var(--fail)}
.banner.na{background:var(--na-bg)}
.badge{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:700;letter-spacing:.03em;border:1px solid currentColor}
.badge.pass{color:var(--pass);background:var(--pass-bg)}
.badge.fail{color:var(--fail);background:var(--fail-bg)}
.badge.na{color:var(--muted);background:var(--na-bg)}
.badge.warn{color:var(--warn);background:var(--warn-bg)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,440px),1fr));gap:16px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:18px;display:flex;flex-direction:column;gap:10px}
.card h2{margin:0;font-size:17px;display:flex;align-items:center;justify-content:space-between;gap:8px}
.card .headline{font-size:28px;font-weight:700;line-height:1.2}
.card .sub{color:var(--muted);margin-top:-6px}
.card .chartbox{display:flex;justify-content:center;align-items:center;min-height:120px}
.btn{display:inline-block;align-self:flex-start;margin-top:auto;padding:7px 16px;border-radius:8px;background:var(--accent);color:#fff;text-decoration:none;font-weight:600}
.btn:hover{filter:brightness(1.1)}
.btn.ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)}
section.block{margin-top:24px}
section.block>h2{font-size:18px;margin:0 0 10px}
table{width:100%;border-collapse:collapse;background:var(--surface)}
.tablewrap{overflow-x:auto;border:1px solid var(--border);border-radius:10px;background:var(--surface)}
th,td{padding:8px 12px;text-align:left;border-bottom:1px solid var(--border);vertical-align:top}
th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);white-space:nowrap}
tr:last-child td{border-bottom:none}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.mono,.mono{font-family:ui-monospace,"Cascadia Mono",Consolas,monospace;font-size:12.5px;word-break:break-all}
tr[hidden],details[hidden]{display:none}
.chart{display:block;margin:0 auto;width:100%;max-width:200px;height:auto}
.chart.wide{max-width:600px;margin:0}
.chart .track{stroke:var(--track)}
.chart .track-fill{fill:var(--track)}
.chart .big{font-size:26px;font-weight:700;fill:var(--text)}
.chart .small{font-size:11px;fill:var(--muted)}
.chart .lbl{font-size:12px;fill:var(--muted)}
.chart .val{font-size:12px;fill:var(--text);font-weight:600}
.chart .axis{stroke:var(--border);stroke-width:1}
.chart .gate-line{stroke:var(--text);stroke-width:2;stroke-dasharray:3 2}
.seg-pass{stroke:var(--pass)}.seg-fail{stroke:var(--fail)}.seg-skip{stroke:var(--warn)}
.fill-pass{fill:var(--pass)}.fill-fail{fill:var(--fail)}.fill-warn{fill:var(--warn)}.fill-info{fill:var(--info)}
.fill-error{fill:var(--sev-error)}.fill-warning{fill:var(--sev-warning)}.fill-style{fill:var(--sev-style)}
.fill-performance{fill:var(--sev-performance)}.fill-portability{fill:var(--sev-portability)}.fill-information{fill:var(--sev-information)}
.empty{color:var(--muted);margin:0}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--muted);justify-content:center}
.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px}
.toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:14px 0;padding:10px 12px;background:var(--surface);border:1px solid var(--border);border-radius:10px}
.toolbar input[type=search]{flex:1 1 220px;padding:7px 10px;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--text);font:inherit}
.toolbar button{padding:6px 12px;border:1px solid var(--border);border-radius:6px;background:var(--surface);color:var(--text);font:inherit;cursor:pointer}
.toolbar button:hover{background:var(--track)}
.toolbar label{display:inline-flex;gap:6px;align-items:center;cursor:pointer}
details.module,details.file{background:var(--surface);border:1px solid var(--border);border-radius:10px;margin:8px 0}
details.file{margin:6px 10px 10px;border-radius:8px;background:var(--bg)}
details>summary{cursor:pointer;padding:10px 14px;display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;list-style:none}
details>summary::-webkit-details-marker{display:none}
details>summary::before{content:"▸";color:var(--muted);width:1em}
details[open]>summary::before{content:"▾"}
summary .name{font-weight:600;flex:1 1 220px;word-break:break-all}
summary .kind{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-right:4px}
.pill{display:inline-block;padding:1px 9px;border-radius:999px;font-size:12px;font-weight:600;background:var(--na-bg);color:var(--muted);white-space:nowrap}
.pill.ok{background:var(--pass-bg);color:var(--pass)}
.pill.warn{background:var(--warn-bg);color:var(--warn)}
.pill.bad{background:var(--fail-bg);color:var(--fail)}
.inner{padding:0 10px 10px}
pre.msg{margin:6px 0 0;padding:8px;background:var(--fail-bg);color:var(--fail);border-radius:6px;white-space:pre-wrap;font-size:12px}
.note{color:var(--muted);font-size:13px;margin:6px 0}
h3.setname{margin:28px 0 8px;font-size:17px;display:flex;gap:10px;align-items:center}
.twocol{display:grid;grid-template-columns:minmax(180px,220px) 1fr;gap:16px;align-items:center;margin-bottom:12px}
@media (max-width:640px){.twocol{grid-template-columns:1fr}.card .headline{font-size:24px}}
footer{margin-top:36px;color:var(--muted);font-size:12px}
"""

JS = """
(function(){
  var q=document.getElementById('q'), bad=document.getElementById('bad');
  function apply(){
    var s=((q&&q.value)||'').toLowerCase().trim(), only=!!(bad&&bad.checked), filtering=!!s||only;
    document.querySelectorAll('tr[data-q]').forEach(function(tr){
      tr.hidden=!((!s||tr.dataset.q.indexOf(s)>=0)&&(!only||tr.dataset.bad==='1'));
    });
    document.querySelectorAll('details.file').forEach(function(d){
      var rows=d.querySelectorAll('tr[data-q]'), vis;
      if(rows.length){vis=d.querySelector('tr[data-q]:not([hidden])')!==null;}
      else{vis=(!s||(d.dataset.q||'').indexOf(s)>=0)&&(!only||d.dataset.bad==='1');}
      d.hidden=!vis; if(vis&&filtering){d.open=true;}
    });
    document.querySelectorAll('details.module').forEach(function(m){
      var direct=m.querySelectorAll(':scope > .inner > .tablewrap tr[data-q]');
      var vis;
      if(m.querySelector('details.file')){vis=m.querySelector('details.file:not([hidden])')!==null;}
      else if(direct.length){vis=m.querySelector('tr[data-q]:not([hidden])')!==null;}
      else{vis=(!s||(m.dataset.q||'').indexOf(s)>=0)&&(!only||m.dataset.bad==='1');}
      m.hidden=!vis; if(vis&&filtering){m.open=true;}
    });
  }
  if(q){q.addEventListener('input',apply);}
  if(bad){bad.addEventListener('change',apply);}
  document.querySelectorAll('[data-expand]').forEach(function(b){
    b.addEventListener('click',function(){
      var open=b.dataset.expand==='all';
      document.querySelectorAll('details.module,details.file').forEach(function(d){d.open=open;});
    });
  });
  apply();
})();
"""
