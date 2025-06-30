from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session
from flask_login import login_required, current_user
from models import Customer
from utils import get_accessible_stores, get_service_types, get_service_display_name
import database_manager
import sqlite3
import os
import re
from sqlalchemy import text
from datetime import datetime

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')

def parse_date_safe(value):
    try:
        return datetime.strptime(value, '%Y-%m-%d').date() if value else None
    except Exception:
        return None

@customers_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    current_store_id = session.get('current_store_id', current_user.store_id)
    store_db_map = {1: 'cossa', 2: 'avigliana', 3: 'grappa'}
    store_name = store_db_map.get(current_store_id, 'cossa')
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'{store_name}.db')

    customers_list = []
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if search:
            like = f'%{search}%'
            cursor.execute("""SELECT * FROM customer WHERE first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? OR email LIKE ? ORDER BY created_at DESC""", (like, like, like, like))
        else:
            cursor.execute("SELECT * FROM customer ORDER BY created_at DESC")

        rows = cursor.fetchall()
        for row in rows:
            customer = dict(row)
            customer['full_name'] = f"{customer['first_name']} {customer['last_name']}"
            customer['birth_date'] = parse_date_safe(customer.get('birth_date'))
            customer['offer_expiry_date'] = parse_date_safe(customer.get('offer_expiry_date'))
            customers_list.append(customer)

        conn.close()
    except Exception:
        pass

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
    response = make_response(render_template('customers.html', customers=customers, search=search))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@customers_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        store_id = request.form.get('store_id', type=int) if current_user.role == 'owner' else current_user.store_id
        bind_key = database_manager.get_store_bind_key_from_id(store_id) if current_user.role == 'owner' else database_manager.get_store_bind_key(current_user)
        engine = database_manager.get_store_engine(bind_key)

        with engine.connect() as conn:
            conn.execute(text("""
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
                'birth_date': parse_date_safe(request.form.get('birth_date')),
                'notes': request.form.get('notes'),
                'current_offer': request.form.get('offers[0][name]', ''),
                'offer_expiry_date': parse_date_safe(request.form.get('offers[0][expiry_date]')),
                'offer_notes': request.form.get('offers[0][notes]', ''),
                'created_at': datetime.utcnow()
            })

            customer_id = conn.execute(text("SELECT last_insert_rowid()")).scalar()

            for key in request.form.keys():
                if re.match(r'offers\[\d+\]\[name\]', key):
                    idx = re.findall(r'\d+', key)[0]
                    name = request.form.get(f'offers[{idx}][name]')
                    expiry = parse_date_safe(request.form.get(f'offers[{idx}][expiry_date]'))
                    notes = request.form.get(f'offers[{idx}][notes]', '')
                    if name:
                        conn.execute(text("""
                            INSERT INTO customer_offer (customer_id, offer_name, offer_type,
                                                        start_date, expiry_date, status, notes, created_at)
                            VALUES (:customer_id, :offer_name, 'Standard',
                                    :start_date, :expiry_date, 'active', :notes, :created_at)
                        """), {
                            'customer_id': customer_id,
                            'offer_name': name,
                            'start_date': datetime.utcnow().date(),
                            'expiry_date': expiry,
                            'notes': notes,
                            'created_at': datetime.utcnow()
                        })
            conn.commit()
        flash('Cliente creato con successo!', 'success')
        return redirect(url_for('customers.index'))

    return render_template('customer_form.html',
                           customer=None,
                           stores=get_accessible_stores(current_user),
                           service_types=get_service_types(),
                           get_service_display_name=get_service_display_name)

@customers_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    database_manager.set_model_bind_key(current_user)
    session_db = database_manager.get_store_db_session(current_user)
    customer = session_db.query(Customer).filter_by(id=id).first()

    if not customer:
        flash('Cliente non trovato!', 'error')
        return redirect(url_for('customers.index'))

    if request.method == 'POST':
        engine = database_manager.get_store_engine(database_manager.get_store_bind_key(current_user))
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE customer SET
                    first_name = :first_name,
                    last_name = :last_name,
                    phone = :phone,
                    email = :email,
                    address = :address,
                    birth_date = :birth_date,
                    notes = :notes,
                    current_offer = :current_offer,
                    offer_expiry_date = :offer_expiry_date,
                    offer_notes = :offer_notes
                WHERE id = :id
            """), {
                'id': id,
                'first_name': request.form['first_name'],
                'last_name': request.form['last_name'],
                'phone': request.form.get('phone'),
                'email': request.form.get('email'),
                'address': request.form.get('address'),
                'birth_date': parse_date_safe(request.form.get('birth_date')),
                'notes': request.form.get('notes'),
                'current_offer': request.form.get('offers[0][name]', ''),
                'offer_expiry_date': parse_date_safe(request.form.get('offers[0][expiry_date]')),
                'offer_notes': request.form.get('offers[0][notes]', '')
            })

            conn.execute(text("DELETE FROM customer_offer WHERE customer_id = :id"), {'id': id})

            for key in request.form.keys():
                if re.match(r'offers\[\d+\]\[name\]', key):
                    idx = re.findall(r'\d+', key)[0]
                    name = request.form.get(f'offers[{idx}][name]')
                    expiry = parse_date_safe(request.form.get(f'offers[{idx}][expiry_date]'))
                    notes = request.form.get(f'offers[{idx}][notes]', '')
                    if name:
                        conn.execute(text("""
                            INSERT INTO customer_offer (customer_id, offer_name, offer_type,
                                                        start_date, expiry_date, status, notes, created_at)
                            VALUES (:customer_id, :offer_name, 'Standard',
                                    :start_date, :expiry_date, 'active', :notes, :created_at)
                        """), {
                            'customer_id': id,
                            'offer_name': name,
                            'start_date': datetime.utcnow().date(),
                            'expiry_date': expiry,
                            'notes': notes,
                            'created_at': datetime.utcnow()
                        })
            conn.commit()
        flash('Cliente aggiornato con successo!', 'success')
        return redirect(url_for('customers.index'))

    return render_template('customer_form.html',
                           customer=customer,
                           stores=get_accessible_stores(current_user),
                           service_types=get_service_types(),
                           get_service_display_name=get_service_display_name)

@customers_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    try:
        database_manager.set_model_bind_key(current_user)
        session_db = database_manager.get_store_db_session(current_user)
        customer = session_db.query(Customer).filter_by(id=id).first()
        if not customer:
            flash('Cliente non trovato!', 'error')
        else:
            session_db.delete(customer)
            session_db.commit()
            flash('Cliente eliminato con successo!', 'success')
    except Exception as e:
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'error')
    finally:
        session_db.close()
    return redirect(url_for('customers.index'))
