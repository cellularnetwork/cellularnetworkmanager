#!/usr/bin/env python3
"""
Sistema di backup completo per tutti i dati del programma
Preserva clienti, vendite, contratti, compensi, obiettivi, promozioni
"""
import sqlite3
import json
import os
from datetime import datetime

def backup_all_data():
    """Backup completo di tutti i dati da tutti i database"""
    
    print("=== BACKUP COMPLETO SISTEMA ===")
    
    backup_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0',
        'source': 'complete_system_backup',
        'main_db': {},
        'stores': {}
    }
    
    # Backup database principale (utenti e negozi)
    try:
        conn = sqlite3.connect('main.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Backup utenti
        cursor.execute("SELECT * FROM user")
        users = [dict(row) for row in cursor.fetchall()]
        backup_data['main_db']['users'] = users
        print(f"✓ Backup utenti: {len(users)}")
        
        # Backup negozi
        cursor.execute("SELECT * FROM store")
        stores = [dict(row) for row in cursor.fetchall()]
        backup_data['main_db']['stores'] = stores
        print(f"✓ Backup negozi: {len(stores)}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Errore backup main.db: {e}")
        backup_data['main_db'] = {'error': str(e)}
    
    # Backup database negozi
    store_databases = ['cossa', 'avigliana', 'grappa']
    
    for store in store_databases:
        db_file = f"{store}.db"
        
        if not os.path.exists(db_file):
            print(f"⚠️ Database {db_file} non trovato")
            backup_data['stores'][store] = {'error': 'Database not found'}
            continue
            
        try:
            conn = sqlite3.connect(db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            store_data = {}
            
            # Tabelle da salvare per ogni negozio
            tables = [
                'customer',      # Clienti
                'sale',          # Vendite
                'contract',      # Contratti
                'promotion',     # Promozioni
                'goal',          # Obiettivi
                'compensation_rate'  # Rate compensi
            ]
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT * FROM {table}")
                    records = [dict(row) for row in cursor.fetchall()]
                    store_data[table] = records
                    print(f"✓ {store} - {table}: {len(records)} record")
                    
                except sqlite3.Error as e:
                    print(f"⚠️ {store} - {table}: Errore {e}")
                    store_data[table] = {'error': str(e)}
            
            backup_data['stores'][store] = store_data
            conn.close()
            
        except Exception as e:
            print(f"❌ Errore backup {store}.db: {e}")
            backup_data['stores'][store] = {'error': str(e)}
    
    # Salva backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"complete_backup_{timestamp}.json"
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📦 Backup completo salvato: {backup_file}")
    
    # Statistiche
    total_records = 0
    for store, data in backup_data['stores'].items():
        if isinstance(data, dict) and 'error' not in data:
            for table, records in data.items():
                if isinstance(records, list):
                    total_records += len(records)
    
    print(f"📊 Totale record salvati: {total_records}")
    return backup_file

def restore_all_data(backup_file):
    """Ripristina tutti i dati da backup completo"""
    
    if not os.path.exists(backup_file):
        print(f"❌ File backup {backup_file} non trovato")
        return False
    
    print(f"=== RIPRISTINO DA {backup_file} ===")
    
    with open(backup_file, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)
    
    print(f"📅 Backup del: {backup_data['timestamp']}")
    
    # Ripristina database principale
    if 'main_db' in backup_data and 'error' not in backup_data['main_db']:
        try:
            conn = sqlite3.connect('main.db')
            cursor = conn.cursor()
            
            # Ripristina utenti
            if 'users' in backup_data['main_db']:
                cursor.execute("DELETE FROM user")
                for user in backup_data['main_db']['users']:
                    cursor.execute("""
                        INSERT INTO user (id, username, email, password_hash, role, store_id, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        user['id'], user['username'], user['email'], 
                        user['password_hash'], user['role'], user['store_id'], 
                        user['created_at']
                    ))
                print(f"✓ Ripristinati {len(backup_data['main_db']['users'])} utenti")
            
            # Ripristina negozi
            if 'stores' in backup_data['main_db']:
                cursor.execute("DELETE FROM store")
                for store in backup_data['main_db']['stores']:
                    cursor.execute("""
                        INSERT INTO store (id, name, description, created_at)
                        VALUES (?, ?, ?, ?)
                    """, (
                        store['id'], store['name'], store['description'], store['created_at']
                    ))
                print(f"✓ Ripristinati {len(backup_data['main_db']['stores'])} negozi")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Errore ripristino main.db: {e}")
    
    # Ripristina database negozi
    for store, data in backup_data['stores'].items():
        if isinstance(data, dict) and 'error' not in data:
            db_file = f"{store}.db"
            
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Ripristina ogni tabella
                for table, records in data.items():
                    if isinstance(records, list) and records:
                        # Pulisci tabella
                        cursor.execute(f"DELETE FROM {table}")
                        
                        # Prepara query inserimento dinamica
                        first_record = records[0]
                        columns = list(first_record.keys())
                        placeholders = ', '.join(['?' for _ in columns])
                        
                        insert_query = f"""
                            INSERT INTO {table} ({', '.join(columns)})
                            VALUES ({placeholders})
                        """
                        
                        # Inserisci tutti i record
                        for record in records:
                            values = [record.get(col) for col in columns]
                            cursor.execute(insert_query, values)
                        
                        print(f"✓ {store} - {table}: {len(records)} record ripristinati")
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                print(f"❌ Errore ripristino {store}.db: {e}")
    
    print("✅ RIPRISTINO COMPLETATO")
    return True

def list_backups():
    """Lista tutti i backup disponibili"""
    
    backup_files = [f for f in os.listdir('.') if f.startswith('complete_backup_') and f.endswith('.json')]
    backup_files.sort(reverse=True)
    
    print("📋 Backup disponibili:")
    
    for i, backup_file in enumerate(backup_files):
        try:
            with open(backup_file, 'r') as f:
                data = json.load(f)
            
            size = os.path.getsize(backup_file)
            timestamp = data.get('timestamp', 'Unknown')
            
            # Conta record
            total_records = 0
            if 'stores' in data:
                for store_data in data['stores'].values():
                    if isinstance(store_data, dict):
                        for table_data in store_data.values():
                            if isinstance(table_data, list):
                                total_records += len(table_data)
            
            print(f"{i+1}. {backup_file}")
            print(f"   📅 {timestamp}")
            print(f"   💾 {size} bytes - {total_records} record totali")
            print()
            
        except Exception as e:
            print(f"{i+1}. {backup_file} - Errore lettura: {e}")
    
    return backup_files

def verify_data_integrity():
    """Verifica integrità dati attuali"""
    
    print("=== VERIFICA INTEGRITÀ DATI ===")
    
    # Verifica main.db
    try:
        conn = sqlite3.connect('main.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM store")
        store_count = cursor.fetchone()[0]
        
        print(f"✓ main.db: {user_count} utenti, {store_count} negozi")
        conn.close()
        
    except Exception as e:
        print(f"❌ main.db: {e}")
    
    # Verifica database negozi
    total_data = 0
    
    for store in ['cossa', 'avigliana', 'grappa']:
        db_file = f"{store}.db"
        
        if os.path.exists(db_file):
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                tables = ['customer', 'sale', 'contract', 'promotion', 'goal', 'compensation_rate']
                store_total = 0
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        store_total += count
                        
                        if count > 0:
                            print(f"  {table}: {count}")
                            
                    except sqlite3.Error:
                        pass
                
                print(f"✓ {store}.db: {store_total} record totali")
                total_data += store_total
                conn.close()
                
            except Exception as e:
                print(f"❌ {store}.db: {e}")
        else:
            print(f"⚠️ {store}.db: Non trovato")
    
    print(f"\n📊 Totale dati sistema: {total_data} record")
    return total_data

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "backup":
            backup_all_data()
        elif command == "restore" and len(sys.argv) > 2:
            restore_all_data(sys.argv[2])
        elif command == "list":
            list_backups()
        elif command == "verify":
            verify_data_integrity()
        else:
            print("Comandi disponibili:")
            print("  backup  - Crea backup completo")
            print("  restore <file> - Ripristina da backup")
            print("  list    - Lista backup disponibili")
            print("  verify  - Verifica integrità dati")
    else:
        print("=== SISTEMA BACKUP COMPLETO ===")
        print("Protegge tutti i dati: clienti, vendite, contratti, compensi, obiettivi")
        print()
        print("Uso: python complete_backup_system.py [comando]")
        print()
        print("Comandi:")
        print("  backup  - Crea backup completo di tutti i dati")
        print("  restore <file> - Ripristina tutti i dati da backup")
        print("  list    - Mostra tutti i backup disponibili")
        print("  verify  - Verifica integrità dati attuali")