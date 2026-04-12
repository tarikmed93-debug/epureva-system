"""
Scraper Google Maps — trouve restaurants/hôtels/bureaux à Marrakech
et extrait leurs emails depuis leurs sites web.
100% gratuit, sans API key.
"""
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from database import ajouter_prospect

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

SECTEURS = {
    'restaurant': [
        'restaurants Marrakech',
        'café restaurant Marrakech',
        'brasserie Marrakech',
        'pizzeria Marrakech',
        'fast food Marrakech médina',
    ],
    'hotel': [
        'hôtel Marrakech',
        'riad Marrakech',
        'maison d hôtes Marrakech',
        'guest house Marrakech',
    ],
    'bureau': [
        'agence immobilière Marrakech',
        'cabinet comptable Marrakech',
        'agence communication Marrakech',
        'clinique dentaire Marrakech',
        'pharmacie Marrakech',
    ],
    'chantier': [
        'promoteur immobilier Marrakech',
        'construction immobilier Marrakech',
        'architecte Marrakech',
        'BTP Marrakech',
    ]
}

def extraire_emails_site(url):
    """Visite un site web et extrait tous les emails trouvés"""
    emails = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Cherche dans le texte brut
        texte = soup.get_text()
        pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
        trouvés = re.findall(pattern, texte)
        
        # Cherche aussi dans les liens mailto:
        for lien in soup.find_all('a', href=True):
            if 'mailto:' in lien['href']:
                email = lien['href'].replace('mailto:', '').split('?')[0].strip()
                if email:
                    trouvés.append(email)
        
        # Filtre les emails valides et pas des images/css
        exclusions = ['example', 'test', 'sentry', 'noreply', 'wordpress', 
                      '.png', '.jpg', '.css', 'schema.org']
        emails = list(set([
            e.lower() for e in trouvés 
            if not any(x in e.lower() for x in exclusions)
            and len(e) < 80
        ]))
        
    except Exception as e:
        pass
    return emails

def scraper_via_duckduckgo(query, secteur, max_resultats=15):
    """Utilise DuckDuckGo pour trouver des établissements et leurs sites"""
    nouveaux = 0
    try:
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        resultats = soup.find_all('div', class_='result__body')[:max_resultats]
        
        for result in resultats:
            try:
                titre_el = result.find('a', class_='result__a')
                snippet_el = result.find('a', class_='result__snippet')
                
                if not titre_el:
                    continue
                    
                nom = titre_el.get_text(strip=True)
                site_url = titre_el.get('href', '')
                snippet = snippet_el.get_text(strip=True) if snippet_el else ''
                
                # Filtre — on veut des vrais sites d'entreprises
                exclusions_sites = ['facebook', 'instagram', 'tripadvisor', 
                                    'booking', 'google', 'youtube', 'twitter',
                                    'linkedin', 'pages jaunes', 'yelp']
                if any(x in site_url.lower() for x in exclusions_sites):
                    continue
                
                if not site_url.startswith('http'):
                    continue
                
                print(f"  → Scanning: {nom[:40]}")
                emails = extraire_emails_site(site_url)
                
                for email in emails:
                    if ajouter_prospect(
                        email=email,
                        nom='',
                        etablissement=nom,
                        secteur=secteur,
                        site_web=site_url,
                    ):
                        print(f"    ✓ Nouveau prospect: {email} ({nom[:30]})")
                        nouveaux += 1
                
                # Pause pour ne pas se faire bloquer
                time.sleep(random.uniform(1.5, 3.0))
                
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"Erreur scraping: {e}")
    
    return nouveaux

def lancer_scraping_journalier(secteur='restaurant'):
    """Lance le scraping du jour pour un secteur donné"""
    print(f"\n🔍 Scraping {secteur}...")
    total = 0
    queries = SECTEURS.get(secteur, SECTEURS['restaurant'])
    
    for query in queries:
        print(f"\nRecherche: {query}")
        n = scraper_via_duckduckgo(query, secteur, max_resultats=10)
        total += n
        time.sleep(random.uniform(3, 6))  # Pause entre les recherches
    
    print(f"\n✅ Scraping terminé: {total} nouveaux prospects trouvés")
    return total

if __name__ == '__main__':
    from database import init_db
    init_db()
    lancer_scraping_journalier('restaurant')
