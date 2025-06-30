#!/usr/bin/env python3
"""
Script per inizializzare i database store con le tabelle necessarie
"""
import sqlite3
import os

def create_store_tables():
    """Crea le tabelle nei database store"""
    
    # SQL per creare le tabelle
    create_customers_sql = """
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        phone VARCHAR(20),
        email VARCHAR(120),
        address TEXT,
        birth_date DATE,
        notes TEXT,
        current_offer VARCHAR(200),
        offer_expiry_date DATE,
        offer_notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    create_sales_sql = """
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        manager_username VARCHAR(64) NOT NULL,
        service_type VARCHAR(50) NOT NULL,
        amount REAL NOT NULL,
        payment_method VARCHAR(50),
        notes TEXT,
        sale_date DATE DEFAULT (date('now')),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    create_contracts_sql = """
    CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        manager_username VARCHAR(64) NOT NULL,
        service_type VARCHAR(50) NOT NULL,
        amount REAL NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE,
        status VARCHAR(20) DEFAULT 'active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    create_promotions_sql = """
    CREATE TABLE IF NOT EXISTS promotions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(200) NOT NULL,
        discount_percentage REAL NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        status VARCHAR(20) DEFAULT 'active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    create_goals_sql = """
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category VARCHAR(100) NOT NULL,
        target_amount REAL NOT NULL,
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    create_compensation_rates_sql = """
    CREATE TABLE IF NOT EXISTS compensation_rates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_type VARCHAR(50) NOT NULL,
        manager_username VARCHAR(64) NOT NULL,
        base_rate REAL NOT NULL,
        threshold INTEGER NOT NULL,
        bonus_rate REAL NOT NULL,
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Database stores
    stores = ['cossa', 'avigliana', 'grappa']
    
    for store in stores:
        db_path = f"{store}.db"
        print(f"Inizializzazione database {db_path}...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Crea tutte le tabelle
        cursor.execute(create_customers_sql)
        cursor.execute(create_sales_sql)
        cursor.execute(create_contracts_sql)
        cursor.execute(create_promotions_sql)
        cursor.execute(create_goals_sql)
        cursor.execute(create_compensation_rates_sql)
        
        conn.commit()
        conn.close()
        
        print(f"Database {db_path} inizializzato con successo!")

if __name__ == "__main__":
    create_store_tables()