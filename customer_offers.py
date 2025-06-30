"""
Sistema gestione offerte multiple per clienti
Ogni cliente può avere multiple offerte con scadenze separate
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
import database_manager
from models import Customer
from sqlalchemy import text

customer_offers_bp = Blueprint('customer_offers', __name__, url_prefix='/customers/<int:customer_id>/offers')

@customer_offers_bp.route('/')
@login_required
def index(customer_id):
    """Lista offerte del cliente"""
    
    # Get customer e offerte
    bind_key = database_manager.get_store_bind_key(current_user)
    engine = database_manager.get_store_engine(bind_key)
    
    with engine.connect() as conn:
        # Verifica che il cliente esista
        customer_result = conn.execute(text("SELECT first_name, last_name FROM customer WHERE id = :id"), {'id': customer_id})
        customer = customer_result.fetchone()
        
        if not customer:
            flash('Cliente non trovato!', 'error')
            return redirect(url_for('customers.index'))
        
        # Recupera tutte le offerte del cliente
        offers_result = conn.execute(text("""
            SELECT id, offer_name, offer_type, start_date, expiry_date, status, notes, created_at
            FROM customer_offer 
            WHERE customer_id = :customer_id 
            ORDER BY expiry_date ASC
        """), {'customer_id': customer_id})
        
        offers = []
        for row in offers_result:
            offer = {
                'id': row[0],
                'offer_name': row[1],
                'offer_type': row[2],
                'start_date': row[3],
                'expiry_date': row[4],
                'status': row[5],
                'notes': row[6],
                'created_at': row[7],
                'days_until_expiry': None,
                'is_expiring_soon': False
            }
            
            # Calcola giorni alla scadenza
            if offer['expiry_date']:
                expiry_date = datetime.strptime(offer['expiry_date'], '%Y-%m-%d').date()
                today = date.today()
                days_diff = (expiry_date - today).days
                offer['days_until_expiry'] = days_diff
                offer['is_expiring_soon'] = days_diff <= 7 and days_diff >= 0
            
            offers.append(offer)
    
    return render_template('customer_offers.html', 
                         customer={'id': customer_id, 'first_name': customer[0], 'last_name': customer[1]},
                         offers=offers)

@customer_offers_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_offer(customer_id):
    """Aggiungi nuova offerta al cliente"""
    
    if request.method == 'POST':
        bind_key = database_manager.get_store_bind_key(current_user)
        engine = database_manager.get_store_engine(bind_key)
        
        # Prepara dati offerta
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date() if request.form.get('start_date') else date.today()
        expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date() if request.form.get('expiry_date') else None
        created_at = datetime.utcnow()
        
        with engine.connect() as conn:
            # Verifica che il cliente esista
            customer_check = conn.execute(text("SELECT id FROM customer WHERE id = :id"), {'id': customer_id})
            if not customer_check.fetchone():
                flash('Cliente non trovato!', 'error')
                return redirect(url_for('customers.index'))
            
            # Inserisci nuova offerta
            conn.execute(text("""
                INSERT INTO customer_offer (customer_id, offer_name, offer_type, start_date, 
                                          expiry_date, status, notes, created_at)
                VALUES (:customer_id, :offer_name, :offer_type, :start_date, 
                       :expiry_date, :status, :notes, :created_at)
            """), {
                'customer_id': customer_id,
                'offer_name': request.form['offer_name'],
                'offer_type': request.form['offer_type'],
                'start_date': start_date,
                'expiry_date': expiry_date,
                'status': request.form.get('status', 'active'),
                'notes': request.form.get('notes', ''),
                'created_at': created_at
            })
            conn.commit()
        
        flash('Offerta aggiunta con successo!', 'success')
        return redirect(url_for('customer_offers.index', customer_id=customer_id))
    
    # GET - mostra form
    bind_key = database_manager.get_store_bind_key(current_user)
    engine = database_manager.get_store_engine(bind_key)
    
    with engine.connect() as conn:
        customer_result = conn.execute(text("SELECT first_name, last_name FROM customer WHERE id = :id"), {'id': customer_id})
        customer = customer_result.fetchone()
        
        if not customer:
            flash('Cliente non trovato!', 'error')
            return redirect(url_for('customers.index'))
    
    return render_template('customer_offer_form.html', 
                         customer={'id': customer_id, 'first_name': customer[0], 'last_name': customer[1]},
                         offer=None)

@customer_offers_bp.route('/<int:offer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_offer(customer_id, offer_id):
    """Modifica offerta esistente"""
    
    bind_key = database_manager.get_store_bind_key(current_user)
    engine = database_manager.get_store_engine(bind_key)
    
    if request.method == 'POST':
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date() if request.form.get('start_date') else None
        expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date() if request.form.get('expiry_date') else None
        
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE customer_offer 
                SET offer_name = :offer_name, offer_type = :offer_type, 
                    start_date = :start_date, expiry_date = :expiry_date,
                    status = :status, notes = :notes
                WHERE id = :offer_id AND customer_id = :customer_id
            """), {
                'offer_id': offer_id,
                'customer_id': customer_id,
                'offer_name': request.form['offer_name'],
                'offer_type': request.form['offer_type'],
                'start_date': start_date,
                'expiry_date': expiry_date,
                'status': request.form.get('status', 'active'),
                'notes': request.form.get('notes', '')
            })
            conn.commit()
        
        flash('Offerta aggiornata con successo!', 'success')
        return redirect(url_for('customer_offers.index', customer_id=customer_id))
    
    # GET - mostra form con dati esistenti
    with engine.connect() as conn:
        # Get customer
        customer_result = conn.execute(text("SELECT first_name, last_name FROM customer WHERE id = :id"), {'id': customer_id})
        customer = customer_result.fetchone()
        
        # Get offerta
        offer_result = conn.execute(text("""
            SELECT offer_name, offer_type, start_date, expiry_date, status, notes
            FROM customer_offer 
            WHERE id = :offer_id AND customer_id = :customer_id
        """), {'offer_id': offer_id, 'customer_id': customer_id})
        offer_data = offer_result.fetchone()
        
        if not customer or not offer_data:
            flash('Cliente o offerta non trovati!', 'error')
            return redirect(url_for('customers.index'))
        
        offer = {
            'id': offer_id,
            'offer_name': offer_data[0],
            'offer_type': offer_data[1],
            'start_date': offer_data[2],
            'expiry_date': offer_data[3],
            'status': offer_data[4],
            'notes': offer_data[5]
        }
    
    return render_template('customer_offer_form.html',
                         customer={'id': customer_id, 'first_name': customer[0], 'last_name': customer[1]},
                         offer=offer)

@customer_offers_bp.route('/<int:offer_id>/delete', methods=['POST'])
@login_required
def delete_offer(customer_id, offer_id):
    """Elimina offerta"""
    
    bind_key = database_manager.get_store_bind_key(current_user)
    engine = database_manager.get_store_engine(bind_key)
    
    with engine.connect() as conn:
        conn.execute(text("""
            DELETE FROM customer_offer 
            WHERE id = :offer_id AND customer_id = :customer_id
        """), {'offer_id': offer_id, 'customer_id': customer_id})
        conn.commit()
    
    flash('Offerta eliminata con successo!', 'success')
    return redirect(url_for('customer_offers.index', customer_id=customer_id))

@customer_offers_bp.route('/api/expiring')
@login_required 
def api_expiring_offers():
    """API per offerte in scadenza (per notifiche)"""
    
    bind_key = database_manager.get_store_bind_key(current_user)
    engine = database_manager.get_store_engine(bind_key)
    
    with engine.connect() as conn:
        # Offerte in scadenza nei prossimi 7 giorni
        result = conn.execute(text("""
            SELECT co.id, co.offer_name, co.offer_type, co.expiry_date,
                   c.first_name, c.last_name, c.phone
            FROM customer_offer co
            JOIN customer c ON co.customer_id = c.id
            WHERE co.status = 'active' 
            AND co.expiry_date BETWEEN date('now') AND date('now', '+7 days')
            ORDER BY co.expiry_date ASC
        """))
        
        expiring_offers = []
        for row in result:
            expiry_date = datetime.strptime(row[3], '%Y-%m-%d').date()
            days_left = (expiry_date - date.today()).days
            
            expiring_offers.append({
                'offer_id': row[0],
                'offer_name': row[1],
                'offer_type': row[2],
                'expiry_date': row[3],
                'days_left': days_left,
                'customer_name': f"{row[4]} {row[5]}",
                'customer_phone': row[6]
            })
    
    return jsonify(expiring_offers)