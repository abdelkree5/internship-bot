import sqlite3
import datetime
from config import DB_PATH

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            role TEXT,
            url TEXT,
            date_applied TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def has_applied(url: str, company: str, role: str) -> bool:
    """Check if an application has already been submitted for this URL or Company/Role combination."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check by URL first
    cursor.execute('SELECT 1 FROM applications WHERE url = ?', (url,))
    if cursor.fetchone():
        conn.close()
        return True
        
    # Check by Company and Role
    cursor.execute('SELECT 1 FROM applications WHERE company = ? AND role = ?', (company, role))
    if cursor.fetchone():
        conn.close()
        return True
        
    conn.close()
    return False

def record_application(company: str, role: str, url: str, status: str = "Applied"):
    """Record a new application in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    date_applied = datetime.datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO applications (company, role, url, date_applied, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (company, role, url, date_applied, status))
    conn.commit()
    conn.close()
