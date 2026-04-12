"""
Dashboard web mobile — Flask app
Accessible via lien web, PC éteint ou allumé
"""
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
from database import get_stats, get_db
import os

app = Flask(__name__)
CORS(app)

DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0">
<title>Epureva — Dashboard</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap');
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:#0a1628;font-family:'Outfit',sans-serif;color:#e8f0ff;min-height:100vh;}

  .topbar{background:#0d1f4a;padding:16px 20px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid #1a3a7a;position:sticky;top:0;z-index:10;}
  .topbar-logo{font-size:18px;font-weight:800;letter-spacing:2px;color:#fff;}
  .topbar-logo span{color:#5ab4f0;}
  .topbar-time{font-size:11px;color:#3a5a8a;font-weight:500;}
  .refresh-btn{background:#1a3a7a;border:none;color:#5ab4f0;padding:8px 14px;border-radius:20px;font-size:12px;font-weight:600;cursor:pointer;font-family:'Outfit',sans-serif;}

  .page{padding:16px;}

  /* KPI CARDS */
  .kpi-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px;}
  .kpi{background:#0d1f4a;border-radius:14px;padding:18px 16px;border:1px solid #1a3a6a;}
  .kpi-label{font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:#3a6aaa;font-weight:600;margin-bottom:6px;}
  .kpi-value{font-size:32px;font-weight:800;line-height:1;margin-bottom:4px;}
  .kpi-sub{font-size:11px;color:#3a5a8a;}
  .kpi.blue .kpi-value{color:#5ab4f0;}
  .kpi.green .kpi-value{color:#4ade80;}
  .kpi.orange .kpi-value{color:#fb923c;}
  .kpi.purple .kpi-value{color:#c084fc;}

  /* PIPELINE */
  .section{background:#0d1f4a;border-radius:14px;padding:18px;margin-bottom:16px;border:1px solid #1a3a6a;}
  .section-title{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#3a6aaa;font-weight:700;margin-bottom:14px;}

  .pipeline{display:flex;gap:8px;}
  .pipe-step{flex:1;text-align:center;padding:12px 6px;border-radius:10px;background:#061020;}
  .pipe-step.active{background:#0d2a5a;}
  .pipe-icon{font-size:20px;margin-bottom:4px;}
  .pipe-label{font-size:9px;color:#3a5a8a;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;}
  .pipe-num{font-size:22px;font-weight:800;color:#e8f0ff;}

  /* LISTE */
  .prospect-item{padding:12px 0;border-bottom:1px solid #0a1a3a;display:flex;justify-content:space-between;align-items:center;}
  .prospect-item:last-child{border-bottom:none;}
  .prospect-nom{font-size:13px;font-weight:600;color:#c8deff;margin-bottom:2px;}
  .prospect-email{font-size:11px;color:#3a5a8a;}
  .badge{font-size:10px;font-weight:700;padding:4px 10px;border-radius:20px;white-space:nowrap;}
  .badge-mail1{background:#1a3a7a;color:#5ab4f0;}
  .badge-mail2{background:#1a4a3a;color:#4ade80;}
  .badge-mail3{background:#3a2a0a;color:#fb923c;}
  .badge-mail4{background:#2a1a4a;color:#c084fc;}
  .badge-repondu{background:#0a3a1a;color:#4ade80;}

  .empty{text-align:center;padding:20px;color:#2a4a6a;font-size:13px;}

  /* BARRE TAUX */
  .taux-row{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;}
  .taux-label{font-size:12px;color:#8ab0e0;}
  .taux-val{font-size:14px;font-weight:700;color:#5ab4f0;}
  .barre-bg{background:#061020;border-radius:4px;height:6px;margin-bottom:14px;}
  .barre-fill{background:linear-gradient(90deg,#1a4aaa,#5ab4f0);border-radius:4px;height:6px;transition:width .8s ease;}

  .loading{text-align:center;padding:40px;color:#3a5a8a;}
</style>
</head>
<body>

<div class="topbar">
  <div>
    <div class="topbar-logo">E<span>PURE</span>VA</div>
    <div class="topbar-time" id="last-update">Chargement...</div>
  </div>
  <button class="refresh-btn" onclick="chargerStats()">↺ Actualiser</button>
</div>

<div class="page">
  <div id="content"><div class="loading">Chargement des données...</div></div>
</div>

<script>
function badge(n) {
  if (n === 'repondu') return '<span class="badge badge-repondu">✓ Répondu</span>';
  const classes = ['','badge-mail1','badge-mail2','badge-mail3','badge-mail4'];
  return `<span class="badge ${classes[n] || 'badge-mail1'}">Mail ${n}</span>`;
}

function taux(n, total) {
  if (!total) return 0;
  return Math.round((n / total) * 100);
}

async function chargerStats() {
  try {
    const r = await fetch('/api/stats');
    const d = await r.json();
    
    const tx_reponse = taux(d.repondus, d.contactes);
    const now = new Date().toLocaleTimeString('fr-FR', {hour:'2-digit',minute:'2-digit'});
    document.getElementById('last-update').textContent = `Mis à jour à ${now}`;

    let envoisHtml = d.derniers_envoyes.length ? d.derniers_envoyes.map(e => `
      <div class="prospect-item">
        <div>
          <div class="prospect-nom">${e.etablissement || 'Établissement'}</div>
          <div class="prospect-email">${e.email}</div>
        </div>
        ${badge(e.numero_mail)}
      </div>`).join('') : '<div class="empty">Aucun envoi pour l\'instant</div>';

    let reponsesHtml = d.derniers_repondus.length ? d.derniers_repondus.map(e => `
      <div class="prospect-item">
        <div>
          <div class="prospect-nom">${e.etablissement || 'Établissement'}</div>
          <div class="prospect-email">${e.email}</div>
        </div>
        ${badge('repondu')}
      </div>`).join('') : '<div class="empty">Pas encore de réponses — ça va venir 💪</div>';

    document.getElementById('content').innerHTML = `
      <div class="kpi-grid">
        <div class="kpi blue">
          <div class="kpi-label">Prospects total</div>
          <div class="kpi-value">${d.total}</div>
          <div class="kpi-sub">dans la base</div>
        </div>
        <div class="kpi green">
          <div class="kpi-label">Mails envoyés</div>
          <div class="kpi-value">${d.total_envoyes}</div>
          <div class="kpi-sub">séquence active</div>
        </div>
        <div class="kpi orange">
          <div class="kpi-label">Réponses</div>
          <div class="kpi-value">${d.repondus}</div>
          <div class="kpi-sub">prospects chauds</div>
        </div>
        <div class="kpi purple">
          <div class="kpi-label">Taux réponse</div>
          <div class="kpi-value">${tx_reponse}%</div>
          <div class="kpi-sub">sur contactés</div>
        </div>
      </div>

      <div class="section">
        <div class="section-title">Pipeline prospects</div>
        <div class="pipeline">
          <div class="pipe-step">
            <div class="pipe-icon">🆕</div>
            <div class="pipe-label">Nouveau</div>
            <div class="pipe-num">${d.nouveaux}</div>
          </div>
          <div class="pipe-step active">
            <div class="pipe-icon">📧</div>
            <div class="pipe-label">Contacté</div>
            <div class="pipe-num">${d.contactes}</div>
          </div>
          <div class="pipe-step">
            <div class="pipe-icon">💬</div>
            <div class="pipe-label">Répondu</div>
            <div class="pipe-num">${d.repondus}</div>
          </div>
        </div>
      </div>

      <div class="section">
        <div class="section-title">Taux de réponse</div>
        <div class="taux-row"><div class="taux-label">Contactés → Réponses</div><div class="taux-val">${tx_reponse}%</div></div>
        <div class="barre-bg"><div class="barre-fill" style="width:${tx_reponse}%"></div></div>
      </div>

      <div class="section">
        <div class="section-title">🔥 Dernières réponses</div>
        ${reponsesHtml}
      </div>

      <div class="section">
        <div class="section-title">📧 Derniers envois</div>
        ${envoisHtml}
      </div>
    `;
  } catch(e) {
    document.getElementById('content').innerHTML = '<div class="loading">Erreur de chargement — serveur en démarrage ?</div>';
  }
}

chargerStats();
setInterval(chargerStats, 60000); // Auto-refresh toutes les minutes
</script>
</body>
</html>'''

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/stats')
def api_stats():
    return jsonify(get_stats())

@app.route('/api/repondu/<email>')
def marquer_repondu(email):
    """Endpoint pour marquer manuellement une réponse"""
    from database import marquer_reponse
    marquer_reponse(email)
    return jsonify({'ok': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
