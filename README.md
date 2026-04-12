# 🧹 Epureva — Système de Prospection Automatique

## Ce que fait ce système
- Scrape chaque matin des restaurants/hôtels/bureaux à Marrakech
- Envoie automatiquement une séquence de 4 mails ciblés
- Anti-doublons : jamais deux fois le même email
- Dashboard mobile accessible via un lien web, même PC éteint

---

## 🚀 Installation en 3 étapes

### ÉTAPE 1 — Préparer tes infos

1. Duplique le fichier `.env.example` et renomme-le `.env`
2. Ouvre `.env` et remplis ton mot de passe SMTP :
```
SMTP_HOST=smtp.hostinger.com
SMTP_PORT=465
SMTP_USER=contact@epureva.ma
SMTP_PASS=TON_MOT_DE_PASSE_ICI
```

Pour trouver ton mot de passe : Hostinger → Emails → Gérer → Configuration manuelle

---

### ÉTAPE 2 — Déployer sur Render (gratuit, tourne 24h/24)

1. Va sur **render.com** → créer un compte gratuit
2. Crée un nouveau dépôt sur **github.com** :
   - Nouveau repo → "epureva-system" → Public
   - Upload tous les fichiers de ce dossier
3. Sur Render → **New Web Service**
   - Connect GitHub → sélectionne "epureva-system"
   - Runtime : **Python 3**
   - Build command : `pip install -r requirements.txt`
   - Start command : `python main.py`
4. Dans **Environment Variables** sur Render, ajoute :
   - `SMTP_PASS` = ton mot de passe Hostinger
   - `SMTP_USER` = contact@epureva.ma
5. Clique **Deploy** → attends 2 minutes

Tu reçois un lien type : `https://epureva-system.onrender.com`
→ C'est ton dashboard, ouvre-le sur mobile !

---

### ÉTAPE 3 — Tester

Sur ton PC avec Claude Code :
```bash
pip install -r requirements.txt
cp .env.example .env
# Édite .env avec ton vrai mot de passe
python emails.py   # Test connexion SMTP
python main.py     # Lance tout
```

---

## 📊 Dashboard mobile

Ouvre le lien Render sur ton téléphone :
- **Prospects total** — nombre d'emails trouvés
- **Mails envoyés** — séquence en cours
- **Réponses** — prospects chauds
- **Pipeline** — Nouveau → Contacté → Répondu

---

## 🔄 Séquence automatique

| Mail | Timing | Sujet |
|------|--------|-------|
| Mail 1 | J+0 | Femme de ménage dédiée |
| Mail 2 | J+5 | Cuisine en profondeur |
| Mail 3 | J+10 | Cristallisation des sols |
| Mail 4 | J+16 | Nettoyage textile |

Si quelqu'un répond → séquence stoppée automatiquement

---

## ❓ Questions

WhatsApp : +212 664-584106
Email : contact@epureva.ma
