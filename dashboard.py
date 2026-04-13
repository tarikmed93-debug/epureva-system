from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
from database import get_stats
import os

app = Flask(__name__)
CORS(app)

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Epureva Dashboard</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&display=swap');
*{box-sizing:border-box;margin:0;padding:0;}
body{background:#0a1628;font-family:'Outfit',sans-serif;color:#e8f0ff;min-height:100vh;}
.topbar{background:#0d1f4a;padding:16px 20px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid #1a3a7a;position:sticky;top:0;}
.logo{font-size:18px;font-weight:800;color:#fff;letter-spacing:2px;}
.logo span{color:#5ab4f0;}
.time{font-size:11px;color:#3a5a8a;}
.btn{background:#1a3a7a;border:none;color:#5ab4f0;padding:8px 14px;border-radius:20px;font-size:12px;font-weight:600;cursor:pointer;}
.page{padding:16px;}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px;}
.kpi{background:#0d1f4a;border-radius:14px;padding:18px 16px;border:1px solid #1a3a6a;}
.kpi-label{font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:#3a6aaa;font-weight:600;margin-bottom:6px;}
.kpi-val{font-size:32px;font-weight:800;line-height:1;margin-bottom:4px;}
.kpi-sub{font-size:11px;color:#3a5a8a;}
.blue .kpi-val{color:#5ab4f0;}
.green .kpi-val{color:#4ade80;}
.orange .kpi-val{color:#fb923c;}
.purple .kpi-val{color:#c084fc;}
.card{background:#0d1f4a;border-radius:14px;padding:18px;margin-bottom:16px;border:1px solid #1a3a6a;}
.card-title{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#3a6aaa;font-weight:700;margin-bottom:14px;}
.pipe{display:flex;gap:8px;}
.step{flex:1;text-align:center;padding:12px 6px;border-radius:10px;background:#061020;}
.step-icon{font-size:14px;font-weight:800;color:#3a6aaa;margin-bottom:4px;}
.step-label{font-size:9px;color:#3a5a8a;text-transform:uppercase;margin-bottom:4px;}
.step-num{font-size:22px;font-weight:800;}
.item{padding:12px 0;border-bottom:1px solid #0a1a3a;display:flex;justify-content:space-between;align-items:center;}
.item:last-child{border-bottom:none;}
.item-nom{font-size:13px;font-weight:600;color:#c8deff;margin-bottom:2px;}
.item-email{font-size:11px;color:#3a5a8a;}
.badge{font-size:10px;font-weight:700;padding:4px 10px;border-radius:20px;}
.b1{background:#1a3a7a;color:#5ab4f0;}
.b2{background:#1a4a3a;color:#4ade80;}
.b3{background:#3a2a0a;color:#fb923c;}
.b4{background:#2a1a4a;color:#c084fc;}
.br{background:#0a3a1a;color:#4ade80;}
.empty{text-align:center;padding:20px;color:#2a4a6a;font-size:13px;}
.bar-bg{background:#061020;border-radius:4px;height:6px;margin-bottom:14px;}
.bar-fill{background:linear-gradient(90deg,#1a4aaa,#5ab4f0);border-radius:4px;height:6px;}
.tr{display:flex;justify-content:space-between;margin-bottom:8px;}
</style>
</head>
<body>
<div class="topbar">
  <div><div class="logo">E<span>PURE</span>VA</div><div class="time" id="t">...</div></div>
  <button class="btn" onclick="load()">Actualiser</button>
</div>
<div class="page" id="content"><div class="empty">Chargement...</div></div>
<script>
function badge(n) {
  if (n === 'repondu') return '<span class="badge br">Repondu</span>';
  var m = {1:'b1',2:'b2',3:'b3',4:'b4'};
  return '<span class="badge ' + (m[n]||'b1') + '">Mail ' + n + '</span>';
}
function load() {
  fetch('/api/stats')
    .then(function(r) { return r.json(); })
    .then(function(d) {
      var tx = d.contactes ? Math.round(d.repondus/d.contactes*100) : 0;
      var now = new Date().toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'});
      document.getElementById('t').textContent = 'Mis a jour ' + now;
      var ei = d.derniers_envoyes && d.derniers_envoyes.length ? d.derniers_envoyes.map(function(e){
        return '<div class="item"><div><div class="item-nom">'+(e.etablissement||'Etablissement')+'</div><div class="item-email">'+e.email+'</div></div>'+badge(e.numero_mail)+'</div>';
      }).join('') : '<div class="empty">Aucun envoi</div>';
      var ri = d.derniers_repondus && d.derniers_repondus.length ? d.derniers_repondus.map(function(e){
        return '<div class="item"><div><div class="item-nom">'+(e.etablissement||'Etablissement')+'</div><div class="item-email">'+e.email+'</div></div>'+badge('repondu')+'</div>';
      }).join('') : '<div class="empty">Pas encore de reponses</div>';
      document.getElementById('content').innerHTML =
        '<div class="grid">'
        +'<div class="kpi blue"><div class="kpi-label">Prospects</div><div class="kpi-val">'+d.total+'</div><div class="kpi-sub">dans la base</div></div>'
        +'<div class="kpi green"><div class="kpi-label">Mails envoyes</div><div class="kpi-val">'+d.total_envoyes+'</div><div class="kpi-sub">sequence active</div></div>'
        +'<div class="kpi orange"><div class="kpi-label">Reponses</div><div class="kpi-val">'+d.repondus+'</div><div class="kpi-sub">prospects chauds</div></div>'
        +'<div class="kpi purple"><div class="kpi-label">Taux</div><div class="kpi-val">'+tx+'%</div><div class="kpi-sub">de reponse</div></div>'
        +'</div>'
        +'<div class="card"><div class="card-title">Pipeline</div><div class="pipe">'
        +'<div class="step"><div class="step-icon">NEW</div><div class="step-label">Nouveau</div><div class="step-num">'+d.nouveaux+'</div></div>'
        +'<div class="step"><div class="step-icon">MAIL</div><div class="step-label">Contacte</div><div class="step-num">'+d.contactes+'</div></div>'
        +'<div class="step"><div class="step-icon">REP</div><div class="step-label">Repondu</div><div class="step-num">'+d.repondus+'</div></div>'
        +'</div></div>'
        +'<div class="card"><div class="card-title">Taux de reponse</div>'
        +'<div class="tr"><span style="font-size:12px;color:#8ab0e0">Contactes vers Reponses</span><span style="font-size:14px;font-weight:700;color:#5ab4f0">'+tx+'%</span></div>'
        +'<div class="bar-bg"><div class="bar-fill" style="width:'+tx+'%"></div></div></div>'
        +'<div class="card"><div class="card-title">Dernieres reponses</div>'+ri+'</div>'
        +'<div class="card"><div class="card-title">Derniers envois</div>'+ei+'</div>';
    })
    .catch(function(e){ document.getElementById('content').innerHTML='<div class="empty">Erreur: '+e.message+'</div>'; });
}
load();
setInterval(load, 60000);
</script>
</body>
</html>"""

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/stats')
def api_stats():
    return jsonify(get_stats())

@app.route('/api/repondu/<email>')
def marquer_repondu(email):
    from database import marquer_reponse
    marquer_reponse(email)
    return jsonify({'ok': True})

if __name__ == '__main__':
    from database import init_db
    init_db()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
