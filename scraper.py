import requests
from bs4 import BeautifulSoup
import re
import time
import random
import os
from database import ajouter_prospect

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'fr-FR,fr;q=0.9',
}

REQUETES = {
    'restaurant': [
        'cafe restaurant Marrakech contact',
        'brasserie Marrakech contact mail',
        'restaurant traditionnel Marrakech email',
        'riad restaurant Marrakech email contact',
        'restaurant italien Marrakech email',
        'restaurant libanais Marrakech contact',
        'restaurant medina Marrakech email',
        'restaurant guéliz Marrakech contact email',
        'traiteur Marrakech email contact',
        'restaurant marocain Marrakech email',
    ],
    'hotel': [
        'riad Marrakech email contact',
        'hotel Marrakech contact email',
        'maison hotes Marrakech email',
    ],
    'bureau': [
        'agence immobiliere Marrakech email',
        'cabinet comptable Marrakech contact',
        'clinique dentaire Marrakech email',
    ],
    'chantier': [
        'promoteur immobilier Marrakech email',
        'architecte Marrakech contact email',
        'BTP construction Marrakech email',
    ]
}

EXCLUSIONS_SITES = [
    'facebook','instagram','tripadvisor','booking','google',
    'youtube','twitter','linkedin','pagesjaunes','yelp',
    'wikipedia','maps','trustpilot','foursquare'
]

EXCLUSIONS_EMAILS = [
    'example','test','sentry','noreply','wordpress',
    '.png','.jpg','.css','schema.org','wixpress','youremail'
]

def extraire_emails_site(url):
    emails = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Cherche emails dans le texte
        texte = soup.get_text()
        pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
        trouves = re.findall(pattern, texte)

        # Cherche dans les liens mailto
        for lien in soup.find_all('a', href=True):
            if 'mailto:' in lien['href']:
                email = lien['href'].replace('mailto:', '').split('?')[0].strip()
                if email:
                    trouves.append(email)

        emails = list(set([
            e.lower() for e in trouves
            if not any(x in e.lower() for x in EXCLUSIONS_EMAILS)
            and len(e) < 80
            and '.' in e.split('@')[-1]
        ]))
    except Exception:
        pass
    return emails

def chercher_duckduckgo(query, max_resultats=10):
    resultats = []
    try:
        url = "https://html.duckduckgo.com/html/"
        params = {'q': query, 'kl': 'fr-fr'}
        resp = requests.post(url, data=params, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')

        for r in soup.find_all('div', class_='result__body')[:max_resultats]:
            a = r.find('a', class_='result__a')
            if a:
                resultats.append({
                    'titre': a.get_text(strip=True),
                    'url': a.get('href', '')
                })
    except Exception as e:
        print(f"  Erreur DuckDuckGo: {e}")
    return resultats

def chercher_bing(query, max_resultats=10):
    """Bing comme backup si DuckDuckGo bloque"""
    resultats = []
    try:
        url = f"https://www.bing.com/search?q={requests.utils.quote(query)}&setlang=fr"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')

        for r in soup.find_all('li', class_='b_algo')[:max_resultats]:
            a = r.find('a')
            if a and a.get('href', '').startswith('http'):
                resultats.append({
                    'titre': a.get_text(strip=True),
                    'url': a['href']
                })
    except Exception as e:
        print(f"  Erreur Bing: {e}")
    return resultats

def scraper_secteur(secteur='restaurant'):
    total = 0
    requetes = REQUETES.get(secteur, REQUETES['restaurant'])

    for query in requetes:
        print(f"\n  Recherche: {query}")

        # Essaie DuckDuckGo d'abord
        resultats = chercher_duckduckgo(query, max_resultats=10)

        # Si pas de resultats, essaie Bing
        if not resultats:
            print("  DuckDuckGo vide, essai Bing...")
            resultats = chercher_bing(query, max_resultats=10)

        print(f"  {len(resultats)} sites trouves")

        for r in resultats:
            url = r['url']
            nom = r['titre']

            if any(x in url.lower() for x in EXCLUSIONS_SITES):
                continue
            if not url.startswith('http'):
                continue

            print(f"    Scanning: {nom[:45]}")
            emails = extraire_emails_site(url)

            for email in emails:
                if ajouter_prospect(
                    email=email,
                    etablissement=nom,
                    secteur=secteur,
                    site_web=url,
                ):
                    print(f"    Nouveau: {email} ({nom[:30]})")
                    total += 1

            time.sleep(random.uniform(1.5, 3.0))

        time.sleep(random.uniform(3.0, 5.0))

    print(f"\nTotal nouveaux prospects: {total}")
    return total

def nettoyer_base():
    """Supprime les emails invalides et doublons par établissement"""
    from database import get_db
    conn = get_db()

    # Supprime emails malformés
    rows = conn.execute("SELECT id, email FROM prospects").fetchall()
    invalides = []
    pattern = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
    for r in rows:
        if not pattern.match(r['email']):
            invalides.append(r['id'])
    if invalides:
        conn.execute(f"DELETE FROM prospects WHERE id IN ({','.join(map(str, invalides))})")
        print(f"  {len(invalides)} emails malformés supprimés")

    # Supprime doublons par établissement (garde le plus pro)
    rows = conn.execute("SELECT id, etablissement, email FROM prospects ORDER BY id").fetchall()
    seen = {}
    doublons = []
    for r in rows:
        etab = r['etablissement']
        if etab not in seen:
            seen[etab] = (r['id'], r['email'])
        else:
            current_email = seen[etab][1]
            if 'gmail.com' in current_email and 'gmail.com' not in r['email']:
                doublons.append(seen[etab][0])
                seen[etab] = (r['id'], r['email'])
            else:
                doublons.append(r['id'])
    if doublons:
        conn.execute(f"DELETE FROM prospects WHERE id IN ({','.join(map(str, doublons))})")
        print(f"  {len(doublons)} doublons supprimés")

    conn.commit()
    conn.close()

def lancer_scraping_journalier(secteur='restaurant'):
    print(f"\nScraping {secteur}...")
    total = scraper_secteur(secteur)
    print("\nNettoyage automatique de la base...")
    nettoyer_base()
    return total

if __name__ == '__main__':
    from database import init_db
    init_db()
    lancer_scraping_journalier('restaurant')
