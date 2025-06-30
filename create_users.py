#!/usr/bin/env python3
"""
Script per creare le 4 utenze del sistema:
1 titolare e 3 dipendenti dei negozi
"""

import os
import sys
from werkzeug.security import generate_password_hash

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Store

def create_users():
    """Crea gli utenti del sistema"""
    
    with app.app_context():
        print("🔄 Creazione utenti del sistema...")
        
        # Rimuovi tutti gli utenti esistenti
        User.query.delete()
        
        # Assicurati che i negozi esistano
        stores = [
            ('Cellular Network Cossa', 'Negozio di Cossa'),
            ('Cellular Network Avigliana', 'Negozio di Avigliana'),
            ('Cellular Network Grappa', 'Negozio di Grappa')
        ]
        
        for store_name, description in stores:
            existing_store = Store.query.filter_by(name=store_name).first()
            if not existing_store:
                store = Store(name=store_name, description=description)
                db.session.add(store)
        
        db.session.commit()
        
        # Dati utenti
        users_data = [
            {
                'username': 'titolare',
                'email': 'titolare@cellularnetwork.it',
                'role': 'owner',
                'store_id': None,
                'password': 'titolare123'
            },
            {
                'username': 'manager_cossa',
                'email': 'cossa@cellularnetwork.it',
                'role': 'manager',
                'store_id': 1,
                'password': 'cossa123'
            },
            {
                'username': 'manager_avigliana',
                'email': 'avigliana@cellularnetwork.it',
                'role': 'manager',
                'store_id': 2,
                'password': 'avigliana123'
            },
            {
                'username': 'manager_grappa',
                'email': 'grappa@cellularnetwork.it',
                'role': 'manager',
                'store_id': 3,
                'password': 'grappa123'
            }
        ]
        
        # Crea gli utenti
        for user_data in users_data:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role'],
                store_id=user_data['store_id'],
                password_hash=generate_password_hash(user_data['password'])
            )
            db.session.add(user)
            
            print(f"✅ Utente creato: {user_data['username']} - {user_data['role']}")
            if user_data['store_id']:
                store = Store.query.get(user_data['store_id'])
                print(f"   Negozio assegnato: {store.name if store else 'N/A'}")
        
        db.session.commit()
        
        print("\n🎉 Sistema utenti creato con successo!")
        print("\n📋 CREDENZIALI DI ACCESSO:")
        print("=" * 50)
        print("TITOLARE:")
        print("  Username: titolare")
        print("  Password: titolare123")
        print("  Accesso: Tutti i negozi + Compensi")
        print()
        print("DIPENDENTE COSSA:")
        print("  Username: manager_cossa")
        print("  Password: cossa123")
        print("  Accesso: Solo negozio Cossa")
        print()
        print("DIPENDENTE AVIGLIANA:")
        print("  Username: manager_avigliana")
        print("  Password: avigliana123")
        print("  Accesso: Solo negozio Avigliana")
        print()
        print("DIPENDENTE GRAPPA:")
        print("  Username: manager_grappa")
        print("  Password: grappa123")
        print("  Accesso: Solo negozio Grappa")
        print("=" * 50)

if __name__ == '__main__':
    create_users()