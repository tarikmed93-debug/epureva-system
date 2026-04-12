import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'epureva.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
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
    conn.close()
    print("✓ Base de données initialisée")

def prospect_existe(email):
    conn = get_db()
    row = conn.execute('SELECT id FROM prospects WHERE email = ?', (email,)).fetchone()
    conn.close()
    return row is not None

def ajouter_prospect(email, nom='', etablissement='', secteur='restaurant', 
                     telephone='', site_web='', adresse=''):
    if prospect_existe(email):
        return False
    conn = get_db()
    conn.execute('''
        INSERT INTO prospects (email, nom, etablissement, secteur, telephone, 
                               site_web, adresse, date_ajout, statut, mail_actuel)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'nouveau', 0)
    ''', (email, nom, etablissement, secteur, telephone, site_web, adresse,
          datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True

def marquer_mail_envoye(prospect_id, numero_mail, objet):
    conn = get_db()
    now = datetime.now().isoformat()
    conn.execute('''
        INSERT INTO envois (prospect_id, numero_mail, date_envoi, objet)
        VALUES (?, ?, ?, ?)
    ''', (prospect_id, numero_mail, now, objet))
    conn.execute('''
        UPDATE prospects SET mail_actuel = ?, date_dernier_mail = ?,
        statut = 'contacte' WHERE id = ?
    ''', (numero_mail, now, prospect_id))
    conn.commit()
    conn.close()

def marquer_reponse(email):
    conn = get_db()
    conn.execute('''
        UPDATE prospects SET statut = 'repondu', date_reponse = ?
        WHERE email = ?
    ''', (datetime.now().isoformat(), email))
    conn.commit()
    conn.close()

def get_prospects_a_contacter(numero_mail, jours_attente):
    """Retourne les prospects qui doivent recevoir le mail numéro X"""
    from datetime import timedelta
    conn = get_db()
    date_limite = (datetime.now() - timedelta(days=jours_attente)).isoformat()
    
    if numero_mail == 1:
        rows = conn.execute('''
            SELECT * FROM prospects 
            WHERE statut = 'nouveau' AND mail_actuel = 0
            LIMIT 50
        ''').fetchall()
    else:
        rows = conn.execute('''
            SELECT * FROM prospects 
            WHERE mail_actuel = ? 
            AND statut = 'contacte'
            AND date_dernier_mail < ?
            LIMIT 50
        ''', (numero_mail - 1, date_limite)).fetchall()
    
    conn.close()
    return rows

def get_stats():
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) as n FROM prospects').fetchone()['n']
    nouveaux = conn.execute("SELECT COUNT(*) as n FROM prospects WHERE statut='nouveau'").fetchone()['n']
    contactes = conn.execute("SELECT COUNT(*) as n FROM prospects WHERE statut='contacte'").fetchone()['n']
    repondus = conn.execute("SELECT COUNT(*) as n FROM prospects WHERE statut='repondu'").fetchone()['n']
    total_envoyes = conn.execute('SELECT COUNT(*) as n FROM envois').fetchone()['n']
    
    derniers_envoyes = conn.execute('''
        SELECT p.etablissement, p.email, p.secteur, e.date_envoi, e.numero_mail
        FROM envois e JOIN prospects p ON e.prospect_id = p.id
        ORDER BY e.date_envoi DESC LIMIT 10
    ''').fetchall()
    
    derniers_repondus = conn.execute('''
        SELECT etablissement, email, secteur, date_reponse
        FROM prospects WHERE statut = 'repondu'
        ORDER BY date_reponse DESC LIMIT 10
    ''').fetchall()
    
    conn.close()
    return {
        'total': total,
        'nouveaux': nouveaux,
        'contactes': contactes,
        'repondus': repondus,
        'total_envoyes': total_envoyes,
        'derniers_envoyes': [dict(r) for r in derniers_envoyes],
        'derniers_repondus': [dict(r) for r in derniers_repondus],
    }

if __name__ == '__main__':
    init_db()
