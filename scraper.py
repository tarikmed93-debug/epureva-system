"""
Scraper Epureva — Overpass API (OpenStreetMap) + extraction emails
Trouve les restaurants/établissements à Marrakech et extrait leurs emails
"""
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from database import ajouter_prospect

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'fr-FR,fr;q=0.9',
}

EXCLUSIONS_EMAILS = [
    'example', 'test', 'sentry', 'noreply', 'wordpress',
    '.png', '.jpg', '.css', 'schema.org', 'wixpress', 'youremail'
]

# Requêtes Overpass pour chaque secteur
OVERPASS_QUERIES = {
    'restaurant': [
        'amenity=restaurant',
        'amenity=cafe',
        'amenity=fast_food',
        'amenity=bar',
    ],
    'hotel': [
        'tourism=hotel',
        'tourism=hostel',
        'tourism=guest_house',
    ],
    'bureau': [
        'office=yes',
        'amenity=dentist',
        'amenity=pharmacy',
    ],
}

# Zone Marrakech (bounding box)
MARRAKECH_BBOX = "31.5600,−8.0800,31.6800,−7.9400"
# Format correct Overpass : sud,ouest,nord,est
MARRAKECH_AREA = "31.560,-8.080,31.680,-7.940"


def chercher_overpass(filtre, max_resultats=50):
    """Cherche des établissements via Overpass API (OpenStreetMap)"""
    resultats = []
    try:
        query = f"""
        [out:json][timeout:25];
        (
          node[{filtre}]({MARRAKECH_AREA});
          way[{filtre}]({MARRAKECH_AREA});
        );
        out body;
        """
        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=query,
            timeout=30
        )
        data = resp.json()

        for elem in data.get('elements', [])[:max_resultats]:
            tags = elem.get('tags', {})
            nom = tags.get('name', '')
            site = tags.get('website', tags.get('contact:website', ''))
            email = tags.get('email', tags.get('contact:email', ''))

            if not nom:
                continue

            resultats.append({
                'nom': nom,
                'site': site,
                'email': email,
                'adresse': tags.get('addr:street', ''),
                'telephone': tags.get('phone', tags.get('contact:phone', '')),
            })

    except Exception as e:
        print(f"  Erreur Overpass: {e}")

    return resultats


def extraire_emails_site(url):
    """Extrait les emails depuis un site web"""
    emails = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(resp.text, 'html.parser')

        texte = soup.get_text()
        pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
        trouves = re.findall(pattern, texte)

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


def scraper_secteur(secteur='restaurant'):
    total = 0
    filtres = OVERPASS_QUERIES.get(secteur, OVERPASS_QUERIES['restaurant'])

    for filtre in filtres:
        print(f"\n  Overpass: {filtre} à Marrakech...")
        etablissements = chercher_overpass(filtre, max_resultats=100)
        print(f"  {len(etablissements)} établissements trouvés")

        for etab in etablissements:
            nom = etab['nom']
            email_direct = etab['email']
            site = etab['site']

            # Email direct depuis OSM
            if email_direct and '@' in email_direct:
                if not any(x in email_direct.lower() for x in EXCLUSIONS_EMAILS):
                    if ajouter_prospect(
                        email=email_direct.lower(),
                        etablissement=nom,
                        secteur=secteur,
                        site_web=site,
                        telephone=etab['telephone'],
                        adresse=etab['adresse'],
                    ):
                        print(f"    OSM email: {email_direct} ({nom[:30]})")
                        total += 1
                continue

            # Sinon scraper le site web
            if site and site.startswith('http'):
                print(f"    Scanning site: {nom[:40]}")
                emails = extraire_emails_site(site)
                for email in emails:
                    if ajouter_prospect(
                        email=email,
                        etablissement=nom,
                        secteur=secteur,
                        site_web=site,
                        telephone=etab['telephone'],
                        adresse=etab['adresse'],
                    ):
                        print(f"    Web email: {email} ({nom[:30]})")
                        total += 1
                time.sleep(random.uniform(1.0, 2.0))

        time.sleep(random.uniform(2.0, 4.0))

    print(f"\nTotal nouveaux prospects: {total}")
    return total


def nettoyer_base():
    """Supprime les emails invalides et doublons"""
    from database import get_db
    conn = get_db()

    rows = conn.execute("SELECT id, email FROM prospects").fetchall()
    invalides = []
    pattern = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
    for r in rows:
        if not pattern.match(r['email']):
            invalides.append(r['id'])
    if invalides:
        conn.execute(f"DELETE FROM prospects WHERE id IN ({','.join(map(str, invalides))})")
        print(f"  {len(invalides)} emails malformés supprimés")

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
    print(f"\nScraping {secteur} via Overpass API...")
    total = scraper_secteur(secteur)
    print("\nNettoyage automatique de la base...")
    nettoyer_base()
    return total


if __name__ == '__main__':
    from database import init_db
    init_db()
    lancer_scraping_journalier('restaurant')
