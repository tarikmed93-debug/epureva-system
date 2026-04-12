"""
Orchestrateur principal — tourne en continu sur le serveur
Lance le scraping + envoi chaque matin automatiquement
"""
import schedule
import time
import threading
from datetime import datetime
from database import init_db, get_prospects_a_contacter, marquer_mail_envoye, get_stats
from scraper import lancer_scraping_journalier
from emails import envoyer_mail, OBJETS

# Délais entre chaque mail de la séquence (en jours)
SEQUENCE = [
    (1, 0),   # Mail 1 : J+0 (nouveaux prospects)
    (2, 5),   # Mail 2 : J+5 sans réponse
    (3, 10),  # Mail 3 : J+10 sans réponse
    (4, 16),  # Mail 4 : J+16 sans réponse
]

def job_quotidien():
    """Lance scraping + envoi chaque matin à 8h"""
    print(f"\n{'='*50}")
    print(f"🚀 Démarrage job quotidien — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*50}")
    
    # 1. Scraping nouveaux prospects
    print("\n📍 ÉTAPE 1 : Scraping Google Maps...")
    nb_nouveaux = lancer_scraping_journalier('restaurant')
    
    # 2. Envoi des mails de la séquence
    print("\n📧 ÉTAPE 2 : Envoi des mails...")
    total_envoyes = 0
    
    for numero_mail, jours_attente in SEQUENCE:
        prospects = get_prospects_a_contacter(numero_mail, jours_attente)
        
        if not prospects:
            print(f"  Mail {numero_mail} : aucun prospect à contacter")
            continue
        
        print(f"  Mail {numero_mail} : {len(prospects)} prospects à contacter")
        
        for prospect in prospects:
            succes = envoyer_mail(
                destinataire=prospect['email'],
                etablissement=prospect['etablissement'] or '',
                numero_mail=numero_mail
            )
            if succes:
                marquer_mail_envoye(
                    prospect_id=prospect['id'],
                    numero_mail=numero_mail,
                    objet=OBJETS[numero_mail]
                )
                total_envoyes += 1
            
            # Pause entre chaque mail (évite le spam)
            time.sleep(30)
    
    # 3. Résumé
    stats = get_stats()
    print(f"\n📊 RÉSUMÉ DU JOUR :")
    print(f"  Nouveaux prospects scrapés : {nb_nouveaux}")
    print(f"  Mails envoyés aujourd'hui  : {total_envoyes}")
    print(f"  Total prospects en base    : {stats['total']}")
    print(f"  Total réponses reçues      : {stats['repondus']}")
    print(f"\n✅ Job terminé — {datetime.now().strftime('%H:%M')}")

def demarrer_scheduler():
    """Lance le scheduler — tourne 24h/24"""
    init_db()
    print("⏰ Scheduler Epureva démarré")
    print("   Job quotidien programmé à 08:00 chaque matin")
    
    schedule.every(1).minutes.do(job_quotidien)
    
    # Lancer immédiatement au démarrage pour tester
    print("\n▶️  Premier lancement immédiat...")
    threading.Thread(target=job_quotidien, daemon=True).start()
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    demarrer_scheduler()
