import sqlite3
import os

# Lista dei database dei negozi
databases = ['cossa.db', 'avigliana.db', 'grappa.db']  # aggiungi altri se ne hai

# Script SQL per creare la tabella
create_table_sql = """
CREATE TABLE IF NOT EXISTS customer_offer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    offer_name TEXT,
    offer_type TEXT,
    start_date DATE,
    expiry_date DATE,
    status TEXT,
    notes TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY(customer_id) REFERENCES customer(id)
);
"""

# Esegui per ogni database
for db_name in databases:
    if os.path.exists(db_name):
        print(f"Aggiornamento di {db_name}...")
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        conn.commit()
        conn.close()
    else:
        print(f"⚠️ Database {db_name} non trovato.")
