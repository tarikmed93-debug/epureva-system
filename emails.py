"""
Module d'envoi des emails via SMTP Hostinger
"""
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.hostinger.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
SMTP_USER = os.getenv('SMTP_USER', 'contact@epureva.ma')
SMTP_PASS = os.getenv('SMTP_PASS', '')

# ── OBJETS DES 4 MAILS ──
OBJETS = {
    1: "Vous gérez votre restaurant. La propreté, on s'en occupe.",
    2: "Votre cuisine est nettoyée chaque soir. Mais les hottes ? Les joints ?",
    3: "Vos sols en marbre ou zellige méritent mieux qu'un simple lavage.",
    4: "Vos chaises, rideaux, banquettes — quand les avez-vous fait nettoyer ?"
}

def charger_template(numero_mail):
    """Charge le template HTML du mail correspondant"""
    templates = {
        1: 'restaurant_mail1_femme_menage.html',
        2: 'restaurant_mail2_cuisine_profondeur.html',
        3: 'restaurant_mail3_sols_cristallisation.html',
        4: 'restaurant_mail4_textile.html',
    }
    fname = templates.get(numero_mail)
    if not fname:
        return None
    
    path = os.path.join(os.path.dirname(__file__), 'templates', fname)
    if not os.path.exists(path):
        # Fallback: cherche dans le répertoire courant
        path = os.path.join(os.path.dirname(__file__), fname)
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return None

def personnaliser_mail(html, etablissement=''):
    """Personnalise le mail avec le nom de l'établissement si dispo"""
    if etablissement:
        html = html.replace(
            'Bonjour,',
            f'Bonjour,<br><br>J\'ai vu votre établissement <strong>{etablissement}</strong> et je me permets de vous contacter directement.'
        , 1)
    return html

def envoyer_mail(destinataire, etablissement, numero_mail):
    """Envoie un mail de la séquence à un prospect"""
    if not SMTP_PASS:
        print("⚠️  SMTP_PASS non configuré dans .env")
        return False
    
    objet = OBJETS.get(numero_mail, "Epureva — Nettoyage Professionnel Marrakech")
    html = charger_template(numero_mail)
    
    if not html:
        print(f"⚠️  Template mail {numero_mail} introuvable")
        return False
    
    html = personnaliser_mail(html, etablissement)
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = objet
        msg['From'] = f"Tarik Epureva <{SMTP_USER}>"
        msg['To'] = destinataire
        msg['Reply-To'] = SMTP_USER
        msg['Bcc'] = SMTP_USER

        # Version texte simple (fallback)
        texte = f"Bonjour,\n\nJe m'appelle Tarik, je dirige Epureva — nettoyage professionnel à Marrakech.\n\nContactez-moi sur contact@epureva.ma ou +212 664-584106\n\nepureva.ma"

        msg.attach(MIMEText(texte, 'plain', 'utf-8'))
        msg.attach(MIMEText(html, 'html', 'utf-8'))

        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [destinataire, SMTP_USER], msg.as_string())
        
        print(f"  ✓ Mail {numero_mail} envoyé → {destinataire}")
        return True
        
    except Exception as e:
        print(f"  ✗ Erreur envoi vers {destinataire}: {e}")
        return False

if __name__ == '__main__':
    # Test d'envoi
    print("Test de connexion SMTP...")
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            print("✅ Connexion SMTP OK !")
    except Exception as e:
        print(f"❌ Erreur: {e}")
