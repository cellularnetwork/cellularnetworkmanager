"""
Launcher per Cellular Network Manager
Versione Installata Localmente
"""
import sys
import os
import subprocess
import webbrowser
import time
from threading import Timer

def check_and_install_python():
    """Verifica se Python è installato"""
    try:
        import flask
        import flask_sqlalchemy
        import flask_login
        return True
    except ImportError:
        print("Installazione dipendenze Python...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True

def start_server():
    """Avvia il server Flask"""
    os.environ.setdefault("SESSION_SECRET", "cellular-network-local-install")
    
    # Imposta percorso database nella cartella utente
    data_dir = os.path.join(os.path.expanduser("~"), "CellularNetworkData")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    db_path = os.path.join(data_dir, "cellular_network.db")
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{db_path}")
    
    # Importa e avvia app
    from app import app
    
    # Inizializza database se necessario
    with app.app_context():
        from init_databases import create_store_tables
        from create_users import create_users
        
        create_store_tables()
        create_users()
    
    # Avvia server
    print("=== CELLULAR NETWORK MANAGER ===")
    print("Sistema avviato con successo!")
    print(f"Database salvato in: {data_dir}")
    print("Apertura browser automatica...")
    print("=" * 40)
    
    # Apri browser dopo 2 secondi
    Timer(2.0, lambda: webbrowser.open("http://localhost:5000")).start()
    
    app.run(host="127.0.0.1", port=5000, debug=False)

if __name__ == "__main__":
    try:
        check_and_install_python()
        start_server()
    except KeyboardInterrupt:
        print("\nServer fermato dall'utente")
    except Exception as e:
        print(f"Errore: {e}")
        input("Premi Enter per chiudere...")
