import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

# Utilise PostgreSQL si DATABASE_URL est défini, sinon SQLite
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras

def get_db():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        import sqlite3
        db_path = os.path.join(os.path.dirname(__file__), 'epureva.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

def fetchall(cursor):
    if USE_POSTGRES:
        return [dict(r) for r in cursor.fetchall()]
    else:
        return [dict(r) for r in cursor.fetchall()]

def fetchone(cursor):
    r = cursor.fetchone()
    if r is None:
        return None
    return dict(r)

def placeholder():
    return '%s' if USE_POSTGRES else '?'

def init_db():
    conn = get_db()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS prospects (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                nom TEXT,
                etablissement TEXT,
                secteur TEXT DEFAULT 'restaurant',
                telephone TEXT,
                site_web TEXT,
                adresse TEXT,
                statut TEXT DEFAULT 'nouveau',
                mail_actuel INTEGER DEFAULT 0,
                date_ajout TEXT,
                date_dernier_mail TEXT,
                date_reponse TEXT,
                notes TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS envois (
                id SERIAL PRIMARY KEY,
                prospect_id INTEGER,
                numero_mail INTEGER,
                date_envoi TEXT,
                objet TEXT,
                statut TEXT DEFAULT 'envoye',
                FOREIGN KEY(prospect_id) REFERENCES prospects(id)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS stats_journalieres (
                id SERIAL PRIMARY KEY,
                date TEXT UNIQUE,
                nb_scrapes INTEGER DEFAULT 0,
                nb_envoyes INTEGER DEFAULT 0,
                nb_reponses INTEGER DEFAULT 0,
                nb_nouveaux_prospects INTEGER DEFAULT 0
            )
        ''')
    else:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS prospects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                nom TEXT,
                etablissement TEXT,
                secteur TEXT DEFAULT 'restaurant',
                telephone TEXT,
                site_web TEXT,
                adresse TEXT,
                statut TEXT DEFAULT 'nouveau',
                mail_actuel INTEGER DEFAULT 0,
                date_ajout TEXT,
                date_dernier_mail TEXT,
                date_reponse TEXT,
                notes TEXT
            );
            CREATE TABLE IF NOT EXISTS envois (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prospect_id INTEGER,
                numero_mail INTEGER,
                date_envoi TEXT,
                objet TEXT,
                statut TEXT DEFAULT 'envoye',
                FOREIGN KEY(prospect_id) REFERENCES prospects(id)
            );
            CREATE TABLE IF NOT EXISTS stats_journalieres (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE,
                nb_scrapes INTEGER DEFAULT 0,
                nb_envoyes INTEGER DEFAULT 0,
                nb_reponses INTEGER DEFAULT 0,
                nb_nouveaux_prospects INTEGER DEFAULT 0
            );
        ''')
    conn.commit()
    cur.close() if USE_POSTGRES else None
    conn.close()
    print("✓ Base de données initialisée")

def prospect_existe(email):
    conn = get_db()
    cur = conn.cursor()
    p = placeholder()
    cur.execute(f'SELECT id FROM prospects WHERE email = {p}', (email,))
    row = fetchone(cur)
    cur.close() if USE_POSTGRES else None
    conn.close()
    return row is not None

def ajouter_prospect(email, nom='', etablissement='', secteur='restaurant',
                     telephone='', site_web='', adresse=''):
    if prospect_existe(email):
        return False
    conn = get_db()
    cur = conn.cursor()
    p = placeholder()
    cur.execute(f'''
        INSERT INTO prospects (email, nom, etablissement, secteur, telephone,
                               site_web, adresse, date_ajout, statut, mail_actuel)
        VALUES ({p},{p},{p},{p},{p},{p},{p},{p},'nouveau',0)
    ''', (email, nom, etablissement, secteur, telephone, site_web, adresse,
          datetime.now().isoformat()))
    conn.commit()
    cur.close() if USE_POSTGRES else None
    conn.close()
    return True

def marquer_mail_envoye(prospect_id, numero_mail, objet):
    conn = get_db()
    cur = conn.cursor()
    p = placeholder()
    now = datetime.now().isoformat()
    cur.execute(f'''
        INSERT INTO envois (prospect_id, numero_mail, date_envoi, objet)
        VALUES ({p},{p},{p},{p})
    ''', (prospect_id, numero_mail, now, objet))
    cur.execute(f'''
        UPDATE prospects SET mail_actuel = {p}, date_dernier_mail = {p},
        statut = 'contacte' WHERE id = {p}
    ''', (numero_mail, now, prospect_id))
    conn.commit()
    cur.close() if USE_POSTGRES else None
    conn.close()

def marquer_reponse(email):
    conn = get_db()
    cur = conn.cursor()
    p = placeholder()
    cur.execute(f'''
        UPDATE prospects SET statut = 'repondu', date_reponse = {p}
        WHERE email = {p}
    ''', (datetime.now().isoformat(), email))
    conn.commit()
    cur.close() if USE_POSTGRES else None
    conn.close()

def get_prospects_a_contacter(numero_mail, jours_attente):
    from datetime import timedelta
    conn = get_db()
    cur = conn.cursor()
    p = placeholder()
    date_limite = (datetime.now() - timedelta(days=jours_attente)).isoformat()

    if numero_mail == 1:
        cur.execute('''
            SELECT * FROM prospects
            WHERE statut = 'nouveau' AND mail_actuel = 0
            LIMIT 50
        ''')
    else:
        cur.execute(f'''
            SELECT * FROM prospects
            WHERE mail_actuel = {p}
            AND statut = 'contacte'
            AND date_dernier_mail < {p}
            LIMIT 50
        ''', (numero_mail - 1, date_limite))

    rows = fetchall(cur)
    cur.close() if USE_POSTGRES else None
    conn.close()
    return rows

def get_stats():
    conn = get_db()
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) as n FROM prospects')
    total = fetchone(cur)['n']
    cur.execute("SELECT COUNT(*) as n FROM prospects WHERE statut='nouveau'")
    nouveaux = fetchone(cur)['n']
    cur.execute("SELECT COUNT(*) as n FROM prospects WHERE statut='contacte'")
    contactes = fetchone(cur)['n']
    cur.execute("SELECT COUNT(*) as n FROM prospects WHERE statut='repondu'")
    repondus = fetchone(cur)['n']
    cur.execute('SELECT COUNT(*) as n FROM envois')
    total_envoyes = fetchone(cur)['n']

    cur.execute('''
        SELECT p.etablissement, p.email, p.secteur, e.date_envoi, e.numero_mail
        FROM envois e JOIN prospects p ON e.prospect_id = p.id
        ORDER BY e.date_envoi DESC LIMIT 10
    ''')
    derniers_envoyes = fetchall(cur)

    cur.execute('''
        SELECT etablissement, email, secteur, date_reponse
        FROM prospects WHERE statut = 'repondu'
        ORDER BY date_reponse DESC LIMIT 10
    ''')
    derniers_repondus = fetchall(cur)

    cur.close() if USE_POSTGRES else None
    conn.close()
    return {
        'total': total,
        'nouveaux': nouveaux,
        'contactes': contactes,
        'repondus': repondus,
        'total_envoyes': total_envoyes,
        'derniers_envoyes': derniers_envoyes,
        'derniers_repondus': derniers_repondus,
    }

if __name__ == '__main__':
    init_db()
