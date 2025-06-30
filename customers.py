from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, make_response, session
from flask_login import login_required, current_user
from models import Customer, db
from utils import get_accessible_stores, filter_by_store_access, get_service_types, get_service_display_name
import database_manager
import sqlite3
import os
import re
from sqlalchemy import text
from datetime import datetime

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')

@customers_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    current_store_id = session.get('current_store_id', current_user.store_id)
    store_db_map = {1: 'cossa', 2: 'avigliana', 3: 'grappa'}
    store_name = store_db_map.get(current_store_id, 'cossa')

    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'{store_name}.db')
    store_conn = sqlite3.connect(db_path)
    store_conn.row_factory = sqlite3.Row
    cursor = store_conn.cursor()

    customers_data = []
    try:
        if search:
            search_filter = f'%{search}%'
            cursor.execute("""
                SELECT * FROM customer 
                WHERE first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? OR email LIKE ?
                ORDER BY created_at DESC
            """, (search_filter, search_filter, search_filter, search_filter))
        else:
            cursor.execute("SELECT * FROM customer ORDER BY created_at DESC")
        customers_data = cursor.fetchall()
    except sqlite3.OperationalError:
        customers_data = []

    customers_list = []
    for customer_data in customers_data:
        customer_dict = dict(customer_data)
        customer_dict['full_name'] = f"{customer_dict['first_name']} {customer_dict['last_name']}"

        if customer_dict.get('birth_date') and isinstance(customer_dict['birth_date'], str):
            try:
                customer_dict['birth_date'] = datetime.strptime(customer_dict['birth_date'], '%Y-%m-%d').date()
            except ValueError:
                pass

        if customer_dict.get('offer_expiry_date') and isinstance(customer_dict['offer_expiry_date'], str):
            try:
                customer_dict['offer_expiry_date'] = datetime.strptime(customer_dict['offer_expiry_date'], '%Y-%m-%d').date()
            except ValueError:
                pass

        customers_list.append(customer_dict)

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
    store_conn.close()

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
        store_id = request.form.get('store_id', type=int) if current_user.role == 'owner' else current_user.store_id
        bind_key = database_manager.get_store_bind_key_from_id(store_id) if current_user.role == 'owner' else database_manager.get_store_bind_key(current_user)
        engine = database_manager.get_store_engine(bind_key)

        birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date() if request.form.get('birth_date') else None
        offer_expiry_date = datetime.strptime(request.form['offer_expiry_date'], '%Y-%m-%d').date() if request.form.get('offer_expiry_date') else None
        created_at = datetime.utcnow()

        with engine.connect() as conn:
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
                'current_offer': request.form.get('offers[0][name]', ''),
                'offer_expiry_date': datetime.strptime(request.form['offers[0][expiry_date]'], '%Y-%m-%d').date() if request.form.get('offers[0][expiry_date]') else None,
                'offer_notes': request.form.get('offers[0][notes]', ''),
                'created_at': created_at
            })

            customer_id = conn.execute(text("SELECT last_insert_rowid()")).fetchone()[0]

            for key in request.form.keys():
                if key.startswith('offers[') and key.endswith('][name]'):
                    match = re.search(r'offers\[(\d+)\]\[name\]', key)
                    if match:
                        offer_index = match.group(1)
                        offer_name = request.form.get(f'offers[{offer_index}][name]')
                        offer_expiry = request.form.get(f'offers[{offer_index}][expiry_date]')
                        offer_notes = request.form.get(f'offers[{offer_index}][notes]', '')
                        if offer_name:
                            try:
                                conn.execute(text("""
                                    INSERT INTO customer_offer (customer_id, offer_name, offer_type, 
                                                                start_date, expiry_date, status, notes, created_at)
                                    VALUES (:customer_id, :offer_name, :offer_type, :start_date, 
                                            :expiry_date, :status, :notes, :created_at)
                                """), {
                                    'customer_id': customer_id,
                                    'offer_name': offer_name,
                                    'offer_type': 'Standard',
                                    'start_date': datetime.utcnow().date(),
                                    'expiry_date': datetime.strptime(offer_expiry, '%Y-%m-%d').date() if offer_expiry else None,
                                    'status': 'active',
                                    'notes': offer_notes,
                                    'created_at': datetime.utcnow()
                                })
                            except Exception:
                                pass
            conn.commit()
        flash('Cliente creato con successo!', 'success')
        return redirect(url_for('customers.index'))

    accessible_stores = get_accessible_stores(current_user)
    return render_template('customer_form.html',
                           customer=None,
                           stores=accessible_stores,
                           service_types=get_service_types(),
                           get_service_display_name=get_service_display_name)

@customers_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    database_manager.set_model_bind_key(current_user)
    store_session = database_manager.get_store_db_session(current_user)

    customer = store_session.query(Customer).filter(Customer.id == id).first()
    if not customer:
        flash('Cliente non trovato!', 'error')
        store_session.close()
        return redirect(url_for('customers.index'))

    if request.method == 'POST':
        bind_key = database_manager.get_store_bind_key(current_user)
        engine = database_manager.get_store_engine(bind_key)
        birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date() if request.form.get('birth_date') else None

        with engine.connect() as conn:
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
                'current_offer': request.form.get('offers[0][name]', ''),
                'offer_expiry_date': datetime.strptime(request.form['offers[0][expiry_date]'], '%Y-%m-%d').date() if request.form.get('offers[0][expiry_date]') else None,
                'offer_notes': request.form.get('offers[0][notes]', '')
            })

            try:
                conn.execute(text("DELETE FROM customer_offer WHERE customer_id = :customer_id"), {'customer_id': id})
            except Exception:
                pass

            for key in request.form.keys():
                if key.startswith('offers[') and key.endswith('][name]'):
                    match = re.search(r'offers\[(\d+)\]\[name\]', key)
                    if match:
                        offer_index = match.group(1)
                        offer_name = request.form.get(f'offers[{offer_index}][name]')
                        offer_expiry = request.form.get(f'offers[{offer_index}][expiry_date]')
                        offer_notes = request.form.get(f'offers[{offer_index}][notes]', '')
                        if offer_name:
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
                                pass
            conn.commit()

        store_session.close()
        flash('Cliente aggiornato con successo!', 'success')
        return redirect(url_for('customers.index'))

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
        database_manager.set_model_bind_key(current_user)
        store_session = database_manager.get_store_db_session(current_user)

        customer = store_session.query(Customer).filter(Customer.id == id).first()
        if not customer:
            flash('Cliente non trovato!', 'error')
            return redirect(url_for('customers.index'))
