# Cellular Network Manager

Sistema gestionale multi-negozio per la gestione di clienti, vendite e magazzino per 3 negozi Cellular Network.

## Caratteristiche

- **Multi-negozio**: Gestione separata per Cossa, Avigliana e Grappa
- **Sistema utenti**: Titolare + 3 manager con accessi limitati per negozio
- **Gestione clienti**: CRUD completo con ricerca
- **Database isolati**: Ogni negozio ha il proprio database
- **Dashboard**: Statistiche in tempo reale
- **Sincronizzazione**: Sistema per sincronizzare dati tra ambienti

## Credenziali Default

- **Titolare**: `titolare` / `titolare123` (accesso completo)
- **Manager Cossa**: `manager_cossa` / `cossa123`
- **Manager Avigliana**: `manager_avigliana` / `avigliana123`
- **Manager Grappa**: `manager_grappa` / `grappa123`

## Installazione Locale

1. Installa dipendenze:
```bash
pip install -r requirements.txt
```

2. Inizializza database:
```bash
python init_databases.py
```

3. Avvia applicazione:
```bash
python main.py
```

## Deployment su Render

1. Carica codice su GitHub
2. Crea database PostgreSQL su Render
3. Crea web service collegato al repository
4. Configura variabili ambiente:
   - `DATABASE_URL`: URL database PostgreSQL
   - `SESSION_SECRET`: chiave segreta casuale
   - `FLASK_ENV`: `production`

## Struttura Database

### Main Database (users, stores)
- `users`: Utenti del sistema
- `stores`: Negozi

### Store Databases (separate per ogni negozio)
- `customer`: Clienti
- `sale`: Vendite
- `inventory`: Magazzino
- `contract`: Contratti
- `goal`: Obiettivi
- `compensation_rate`: Tariffe compensi
- `promotion`: Promozioni
- `customer_offer`: Offerte clienti

## Tecnologie

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **Frontend**: Bootstrap 5 Dark Theme, Font Awesome
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Deploy**: Render, Gunicorn