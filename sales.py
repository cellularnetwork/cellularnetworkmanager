from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Sale, Customer, User, db
from utils import get_accessible_stores, filter_by_store_access, get_service_types, get_payment_methods, get_service_display_name
import database_manager
from datetime import datetime, date
from inventory import update_inventory_after_sale

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

@sales_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    service_filter = request.args.get('service', '')
    
    # Set database binding for user's store
    database_manager.set_model_bind_key(current_user)
    store_session = database_manager.get_store_db_session(current_user)
    
    query = store_session.query(Sale)
    
    if date_from:
        query = query.filter(Sale.sale_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    
    if date_to:
        query = query.filter(Sale.sale_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    if service_filter:
        query = query.filter(Sale.service_type == service_filter)
    
    # Execute query and get results manually for pagination
    all_sales = query.order_by(Sale.created_at.desc()).all()
    total_sales = len(all_sales)
    
    # Manual pagination
    per_page = 20
    start = (page - 1) * per_page
    end = start + per_page
    sales_page = all_sales[start:end]
    
    # Load customer data for each sale
    for sale in sales_page:
        customer = store_session.query(Customer).filter(Customer.id == sale.customer_id).first()
        sale.customer = customer
    
    # Create a simple pagination object
    class SimplePagination:
        def __init__(self, items, total, page, per_page):
            self.items = items
            self.total = total
            self.page = page
            self.per_page = per_page
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1 if self.has_prev else None
            self.next_num = page + 1 if self.has_next else None
    
    sales = SimplePagination(sales_page, total_sales, page, per_page)
    
    # Get unique service types for filter from store session
    service_types_result = store_session.query(Sale.service_type).distinct().all()
    service_types = [st[0] for st in service_types_result]
    
    # Calculate total for current filter using same filtered sales
    total_amount = sum(sale.amount for sale in sales_page) if sales_page else 0
    
    # Get current store name
    current_store_name = database_manager.get_current_store_name(current_user)
    
    store_session.close()
    
    return render_template('sales.html',
                         sales=sales,
                         date_from=date_from,
                         date_to=date_to,
                         service_filter=service_filter,
                         service_types=service_types,
                         get_service_display_name=get_service_display_name,
                         total_amount=total_amount,
                         current_store_name=current_store_name)

@sales_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        import json
        
        # Get the store-specific database session
        database_manager.set_model_bind_key(current_user)
        store_session = database_manager.get_store_db_session(current_user)
        
        try:
            # Parse services from JSON
            services_json = request.form.get('services_json', '[]')
            services = json.loads(services_json) if services_json else []
            
            if not services:
                flash('Aggiungi almeno un servizio al carrello prima di salvare.', 'warning')
                return redirect(url_for('sales.new'))
            
            # Common sale data
            customer_id = request.form['customer_id']
            payment_method = request.form.get('payment_method')
            notes = request.form.get('notes')
            sale_date = datetime.strptime(request.form['sale_date'], '%Y-%m-%d').date() if request.form.get('sale_date') else date.today()
            
            # Create a sale record for each service
            for service in services:
                # Combine general notes with service-specific notes
                service_notes = notes
                if service.get('notes'):
                    service_notes = f"{notes}\n{service['notes']}" if notes else service['notes']
                
                sale = Sale(
                    customer_id=customer_id,
                    manager_username=current_user.username,
                    service_type=service['service_type'],
                    amount=float(service['amount']),
                    payment_method=payment_method,
                    notes=service_notes,
                    sale_date=sale_date,
                    inventory_item_id=service.get('inventory_item_id'),
                    quantity_sold=service.get('quantity_sold', 1)
                )
                
                store_session.add(sale)
                
                # Se è un prodotto dal magazzino, aggiorna le scorte
                if service.get('inventory_item_id') and service.get('quantity_sold'):
                    if not update_inventory_after_sale(
                        service['inventory_item_id'], 
                        service['quantity_sold'], 
                        current_user
                    ):
                        store_session.rollback()
                        flash(f'Errore: scorte insufficienti per il prodotto nel magazzino.', 'error')
                        return redirect(url_for('sales.new'))
            
            store_session.commit()
            
            # Success message with count
            service_count = len(services)
            total_amount = sum(float(service['amount']) for service in services)
            flash(f'Vendita salvata con successo! {service_count} servizi per un totale di €{total_amount:.2f}', 'success')
            
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            store_session.rollback()
            flash('Errore nel salvare la vendita. Verifica i dati inseriti.', 'error')
        finally:
            store_session.close()
            
        return redirect(url_for('sales.index'))
    
    # Get customers from store database
    database_manager.set_model_bind_key(current_user)
    store_session = database_manager.get_store_db_session(current_user)
    customers = store_session.query(Customer).all()
    store_session.close()
    
    accessible_stores = get_accessible_stores(current_user)
    
    if current_user.role == 'owner':
        managers = User.query.filter(User.role == 'manager').all()
    else:
        managers = [current_user]
    
    return render_template('sale_form.html',
                         sale=None,
                         customers=customers,
                         managers=managers,
                         stores=accessible_stores,
                         service_types=get_service_types(),
                         payment_methods=get_payment_methods(),
                         get_service_display_name=get_service_display_name,
                         today=date.today())

@sales_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    import sqlite3
    
    # Get store database path
    store_bind_key = database_manager.get_store_bind_key(current_user)
    db_path = f"{store_bind_key}.db"
    
    if request.method == 'POST':
        try:
            # Direct SQL update to ensure persistence
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            customer_id = request.form['customer_id']
            service_type = request.form['service_type']
            amount = float(request.form['amount'])
            payment_method = request.form.get('payment_method')
            notes = request.form.get('notes')
            sale_date = request.form['sale_date']
            
            cursor.execute("""
                UPDATE sale 
                SET customer_id = ?, service_type = ?, amount = ?, 
                    payment_method = ?, notes = ?, sale_date = ?
                WHERE id = ?
            """, (customer_id, service_type, amount, payment_method, notes, sale_date, id))
            
            conn.commit()
            conn.close()
            
            flash('Vendita aggiornata con successo!', 'success')
            return redirect(url_for('sales.index'))
            
        except Exception as e:
            flash(f'Errore nell\'aggiornamento: {str(e)}', 'error')
            return redirect(url_for('sales.edit', id=id))
    
    # GET request - load sale data
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sale WHERE id = ?", (id,))
        sale_data = cursor.fetchone()
        
        if not sale_data:
            conn.close()
            flash('Vendita non trovata.', 'error')
            return redirect(url_for('sales.index'))
        
        # Convert to dict for template
        from datetime import datetime
        
        # Convert string date to date object for template
        sale_date_str = sale_data[7]
        try:
            if isinstance(sale_date_str, str):
                sale_date_obj = datetime.strptime(sale_date_str, '%Y-%m-%d').date()
            else:
                sale_date_obj = sale_date_str
        except:
            sale_date_obj = datetime.now().date()
        
        sale = {
            'id': sale_data[0],
            'customer_id': sale_data[1],
            'manager_username': sale_data[2],
            'service_type': sale_data[3],
            'amount': sale_data[4],
            'payment_method': sale_data[5],
            'notes': sale_data[6],
            'sale_date': sale_date_obj
        }
        
        # Get customers for dropdown
        cursor.execute("SELECT * FROM customer ORDER BY first_name, last_name")
        customer_data = cursor.fetchall()
        customers = []
        for c in customer_data:
            customers.append({
                'id': c[0],
                'first_name': c[1],
                'last_name': c[2],
                'full_name': f"{c[1]} {c[2]}"
            })
        
        conn.close()
        
        accessible_stores = get_accessible_stores(current_user)
        
        if current_user.role == 'owner':
            managers = User.query.filter(User.role == 'manager').all()
        else:
            managers = [current_user]
        
        return render_template('sale_form.html',
                             sale=sale,
                             customers=customers,
                             managers=managers,
                             stores=accessible_stores,
                             service_types=get_service_types(),
                             payment_methods=get_payment_methods(),
                             get_service_display_name=get_service_display_name,
                             today=date.today())
                             
    except Exception as e:
        flash(f'Errore nel caricamento: {str(e)}', 'error')
        return redirect(url_for('sales.index'))

@sales_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    import logging
    logging.info(f"Attempting to delete sale {id} for user {current_user.username}")
    
    # Set database binding for user's store
    database_manager.set_model_bind_key(current_user)
    
    store_session = None
    try:
        # Get fresh session
        store_session = database_manager.get_store_db_session(current_user)
        logging.info(f"Got session for user {current_user.username}")
        
        # Find the sale
        sale = store_session.query(Sale).filter(Sale.id == id).first()
        logging.info(f"Found sale: {sale}")
        
        if not sale:
            flash('Vendita non trovata.', 'error')
            logging.warning(f"Sale {id} not found")
            return redirect(url_for('sales.index'))
            
        # Delete the sale
        store_session.delete(sale)
        store_session.commit()
        logging.info(f"Sale {id} deleted successfully")
        
        flash('Vendita eliminata con successo!', 'success')
        
    except Exception as e:
        logging.error(f"Error deleting sale {id}: {str(e)}")
        if store_session:
            try:
                store_session.rollback()
            except:
                pass
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'error')
    finally:
        if store_session:
            try:
                store_session.close()
            except:
                pass
    
    # Force redirect with cache prevention
    from flask import Response
    response = redirect(url_for('sales.index'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
