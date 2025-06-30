from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, make_response
from flask_login import login_required, current_user
from models import Customer, db
from utils import get_accessible_stores, filter_by_store_access
import database_manager
from datetime import datetime

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')

@customers_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Use the same database session approach as delete function
    database_manager.set_model_bind_key(current_user)
    store_session = database_manager.get_store_db_session(current_user)
    
    query = store_session.query(Customer)
    
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            (Customer.first_name.like(search_filter)) |
            (Customer.last_name.like(search_filter)) |
            (Customer.phone.like(search_filter)) |
            (Customer.email.like(search_filter))
        )
    
    # Get all customers for now (we'll add pagination back later)
    customers_list = query.order_by(Customer.created_at.desc()).all()
    
    # Simple pagination object
    class SimplePagination:
        def __init__(self, items):
            self.items = items
            self.page = 1
            self.pages = 1
            self.total = len(items)
            self.has_prev = False
            self.has_next = False
            self.prev_num = None
            self.next_num = None
    
    customers = SimplePagination(customers_list)
    store_session.close()
    
    # Create response with aggressive anti-cache headers
    response = make_response(render_template('customers.html', customers=customers, search=search))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Last-Modified'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    return response

@customers_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        # Determine store_id based on user role
        if current_user.role == 'owner':
            store_id = request.form.get('store_id', type=int)
        else:
            store_id = current_user.store_id
        
        # Usa direttamente l'engine del database specifico per garantire persistenza
        if current_user.role == 'owner':
            bind_key = database_manager.get_store_bind_key_from_id(store_id)
        else:
            bind_key = database_manager.get_store_bind_key(current_user)
        
        # Usa SQL diretto per garantire persistenza nei database specifici
        engine = database_manager.get_store_engine(bind_key)
        
        # Prepara i dati
        birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date() if request.form.get('birth_date') else None
        offer_expiry_date = datetime.strptime(request.form['offer_expiry_date'], '%Y-%m-%d').date() if request.form.get('offer_expiry_date') else None
        created_at = datetime.utcnow()
        
        # Inserimento SQL diretto per garantire persistenza
        from sqlalchemy import text
        with engine.connect() as conn:
            # Inserisci il cliente
            result = conn.execute(text("""
                INSERT INTO customer (first_name, last_name, phone, email, address, birth_date, 
                                    notes, current_offer, offer_expiry_date, offer_notes, created_at)
                VALUES (:first_name, :last_name, :phone, :email, :address, :birth_date, 
                       :notes, :current_offer, :offer_expiry_date, :offer_notes, :created_at)
            """), {
                'first_name': request.form['first_name'],
                'last_name': request.form['last_name'], 
                'phone': request.form.get('phone'),
                'email': request.form.get('email'),
                'address': request.form.get('address'),
                'birth_date': birth_date,
                'notes': request.form.get('notes'),
                'current_offer': request.form.get('offers[0][name]', ''),  # Prima offerta come legacy
                'offer_expiry_date': datetime.strptime(request.form['offers[0][expiry_date]'], '%Y-%m-%d').date() if request.form.get('offers[0][expiry_date]') else None,
                'offer_notes': request.form.get('offers[0][notes]', ''),
                'created_at': created_at
            })
            
            # Ottieni l'ID del cliente appena creato
            customer_id = conn.execute(text("SELECT last_insert_rowid()")).fetchone()[0]
            
            # Salva tutte le offerte nella tabella customer_offer
            for key in request.form.keys():
                if key.startswith('offers[') and key.endswith('][name]'):
                    # Estrai l'indice dell'offerta
                    import re
                    match = re.search(r'offers\[(\d+)\]\[name\]', key)
                    if match:
                        offer_index = match.group(1)
                        offer_name = request.form.get(f'offers[{offer_index}][name]')
                        offer_expiry = request.form.get(f'offers[{offer_index}][expiry_date]')
                        offer_notes = request.form.get(f'offers[{offer_index}][notes]', '')
                        
                        if offer_name:  # Solo se è stata selezionata un'offerta
                            try:
                                conn.execute(text("""
                                    INSERT INTO customer_offer (customer_id, offer_name, offer_type, 
                                                               start_date, expiry_date, status, notes, created_at)
                                    VALUES (:customer_id, :offer_name, :offer_type, :start_date, 
                                           :expiry_date, :status, :notes, :created_at)
                                """), {
                                    'customer_id': customer_id,
                                    'offer_name': offer_name,
                                    'offer_type': 'Standard',  # Tipo di default
                                    'start_date': datetime.utcnow().date(),
                                    'expiry_date': datetime.strptime(offer_expiry, '%Y-%m-%d').date() if offer_expiry else None,
                                    'status': 'active',
                                    'notes': offer_notes,
                                    'created_at': datetime.utcnow()
                                })
                            except Exception:
                                # Tabella customer_offer potrebbe non esistere ancora
                                pass
            
            conn.commit()
        flash('Cliente creato con successo!', 'success')
        return redirect(url_for('customers.index'))
    
    from utils import get_service_types, get_service_display_name
    accessible_stores = get_accessible_stores(current_user)
    return render_template('customer_form.html', 
                          customer=None, 
                          stores=accessible_stores,
                          service_types=get_service_types(),
                          get_service_display_name=get_service_display_name)

@customers_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    # Set database binding for user's store
    database_manager.set_model_bind_key(current_user)
    store_session = database_manager.get_store_db_session(current_user)
    
    customer = store_session.query(Customer).filter(Customer.id == id).first()
    if not customer:
        flash('Cliente non trovato!', 'error')
        store_session.close()
        return redirect(url_for('customers.index'))
    
    if request.method == 'POST':
        # Usa SQL diretto per garantire persistenza
        bind_key = database_manager.get_store_bind_key(current_user)
        engine = database_manager.get_store_engine(bind_key)
        
        # Prepara i dati
        birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date() if request.form.get('birth_date') else None
        
        from sqlalchemy import text
        with engine.connect() as conn:
            # Aggiorna il cliente
            conn.execute(text("""
                UPDATE customer 
                SET first_name = :first_name, last_name = :last_name, phone = :phone, 
                    email = :email, address = :address, birth_date = :birth_date, 
                    notes = :notes, current_offer = :current_offer, 
                    offer_expiry_date = :offer_expiry_date, offer_notes = :offer_notes
                WHERE id = :id
            """), {
                'id': id,
                'first_name': request.form['first_name'],
                'last_name': request.form['last_name'],
                'phone': request.form.get('phone'),
                'email': request.form.get('email'),
                'address': request.form.get('address'),
                'birth_date': birth_date,
                'notes': request.form.get('notes'),
                'current_offer': request.form.get('offers[0][name]', ''),  # Prima offerta come legacy
                'offer_expiry_date': datetime.strptime(request.form['offers[0][expiry_date]'], '%Y-%m-%d').date() if request.form.get('offers[0][expiry_date]') else None,
                'offer_notes': request.form.get('offers[0][notes]', '')
            })
            
            # Rimuovi tutte le offerte esistenti per questo cliente
            try:
                conn.execute(text("DELETE FROM customer_offer WHERE customer_id = :customer_id"), {'customer_id': id})
            except Exception:
                # Tabella customer_offer potrebbe non esistere ancora
                pass
            
            # Salva tutte le nuove offerte nella tabella customer_offer
            for key in request.form.keys():
                if key.startswith('offers[') and key.endswith('][name]'):
                    # Estrai l'indice dell'offerta
                    import re
                    match = re.search(r'offers\[(\d+)\]\[name\]', key)
                    if match:
                        offer_index = match.group(1)
                        offer_name = request.form.get(f'offers[{offer_index}][name]')
                        offer_expiry = request.form.get(f'offers[{offer_index}][expiry_date]')
                        offer_notes = request.form.get(f'offers[{offer_index}][notes]', '')
                        
                        if offer_name:  # Solo se è stata selezionata un'offerta
                            try:
                                conn.execute(text("""
                                    INSERT INTO customer_offer (customer_id, offer_name, offer_type, 
                                                               start_date, expiry_date, status, notes, created_at)
                                    VALUES (:customer_id, :offer_name, :offer_type, :start_date, 
                                           :expiry_date, :status, :notes, :created_at)
                                """), {
                                    'customer_id': id,
                                    'offer_name': offer_name,
                                    'offer_type': 'Standard',
                                    'start_date': datetime.utcnow().date(),
                                    'expiry_date': datetime.strptime(offer_expiry, '%Y-%m-%d').date() if offer_expiry else None,
                                    'status': 'active',
                                    'notes': offer_notes,
                                    'created_at': datetime.utcnow()
                                })
                            except Exception:
                                # Tabella customer_offer potrebbe non esistere ancora
                                pass
            
            conn.commit()
        
        store_session.close()
        flash('Cliente aggiornato con successo!', 'success')
        return redirect(url_for('customers.index'))
    
    from utils import get_service_types, get_service_display_name
    accessible_stores = get_accessible_stores(current_user)
    return render_template('customer_form.html', 
                          customer=customer, 
                          stores=accessible_stores,
                          service_types=get_service_types(),
                          get_service_display_name=get_service_display_name)

@customers_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    try:
        # Get the store-specific database session
        database_manager.set_model_bind_key(current_user)
        store_session = database_manager.get_store_db_session(current_user)
        
        # Get customer directly from store session
        customer = store_session.query(Customer).filter(Customer.id == id).first()
        
        if not customer:
            flash('Cliente non trovato!', 'error')
            return redirect(url_for('customers.index'))
        
        # Delete the customer
        store_session.delete(customer)
        store_session.commit()
        store_session.close()
        flash('Cliente cancellato con successo!', 'success')
        
    except Exception as e:
        if 'store_session' in locals():
            store_session.rollback()
            store_session.close()
        flash(f'Errore durante la cancellazione: {str(e)}', 'error')
    
    return redirect(url_for('customers.index'))
