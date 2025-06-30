"""
Sistema gestione magazzino per tutti e 3 i negozi
Ogni negozio ha il proprio magazzino isolato
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Inventory
from database_manager import get_store_db_session, set_model_bind_key, get_current_store_name
from datetime import datetime
import sqlite3

inventory_bp = Blueprint('inventory', __name__)

def get_inventory_data(user):
    """Ottieni dati magazzino per il negozio dell'utente"""
    set_model_bind_key(user)
    session = get_store_db_session(user)
    
    try:
        # Query per ottenere tutti i prodotti
        inventory_items = session.query(Inventory).order_by(Inventory.created_at.desc()).all()
        
        # Statistiche magazzino
        total_items = len(inventory_items)
        total_quantity = sum(item.quantity for item in inventory_items)
        total_value = sum(item.total_value for item in inventory_items)
        low_stock_items = [item for item in inventory_items if item.is_low_stock]
        
        stats = {
            'total_items': total_items,
            'total_quantity': total_quantity,
            'total_value': total_value,
            'low_stock_count': len(low_stock_items)
        }
        
        return inventory_items, stats, low_stock_items
        
    except Exception as e:
        print(f"Errore lettura magazzino: {e}")
        return [], {}, []
    finally:
        session.close()

@inventory_bp.route('/')
@login_required
def index():
    """Lista prodotti magazzino"""
    inventory_items, stats, low_stock_items = get_inventory_data(current_user)
    store_name = get_current_store_name(current_user)
    
    # Filtri per categoria e brand
    categories = list(set([item.category for item in inventory_items if item.category]))
    brands = list(set([item.brand for item in inventory_items if item.brand]))
    
    # Converti oggetti Inventory in dizionari per serializzazione JSON
    inventory_data = []
    for item in inventory_items:
        inventory_data.append({
            'id': item.id,
            'product_name': item.product_name,
            'brand': item.brand or '',
            'device_brand': item.device_brand or '',
            'model': item.model or '',
            'color': item.color or '',
            'ram': item.ram or '',
            'storage': item.storage or '',
            'category': item.category or '',
            'quantity': item.quantity,
            'price': float(item.price),
            'notes': item.notes or '',
            'created_at': item.created_at.isoformat() if item.created_at else '',
            'updated_at': item.updated_at.isoformat() if item.updated_at else ''
        })
    
    return render_template('inventory/index.html', 
                         inventory_items=inventory_data,
                         stats=stats,
                         low_stock_items=low_stock_items,
                         store_name=store_name,
                         categories=categories,
                         brands=brands)

@inventory_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Aggiungi nuovo prodotto al magazzino"""
    if request.method == 'POST':
        try:
            set_model_bind_key(current_user)
            session = get_store_db_session(current_user)
            
            new_item = Inventory(
                product_name=request.form['product_name'],
                brand=request.form.get('brand', ''),
                device_brand=request.form.get('device_brand', ''),
                model=request.form.get('model', ''),
                color=request.form.get('color', ''),
                ram=request.form.get('ram', ''),
                storage=request.form.get('storage', ''),
                quantity=int(request.form['quantity']),
                price=float(request.form['price']),
                category=request.form.get('category', ''),
                notes=request.form.get('notes', '')
            )
            
            session.add(new_item)
            session.commit()
            
            flash(f'Prodotto "{new_item.product_name}" aggiunto al magazzino!', 'success')
            return redirect(url_for('inventory.index'))
            
        except Exception as e:
            session.rollback()
            flash(f'Errore aggiunta prodotto: {str(e)}', 'error')
        finally:
            session.close()
    
    store_name = get_current_store_name(current_user)
    return render_template('inventory/new.html', store_name=store_name)

@inventory_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Modifica prodotto magazzino"""
    set_model_bind_key(current_user)
    session = get_store_db_session(current_user)
    
    try:
        item = session.query(Inventory).get(id)
        if not item:
            flash('Prodotto non trovato!', 'error')
            return redirect(url_for('inventory.index'))
        
        if request.method == 'POST':
            item.product_name = request.form['product_name']
            item.brand = request.form.get('brand', '')
            item.device_brand = request.form.get('device_brand', '')
            item.model = request.form.get('model', '')
            item.color = request.form.get('color', '')
            item.ram = request.form.get('ram', '')
            item.storage = request.form.get('storage', '')
            item.quantity = int(request.form['quantity'])
            item.price = float(request.form['price'])
            item.category = request.form.get('category', '')
            item.notes = request.form.get('notes', '')
            item.updated_at = datetime.utcnow()
            
            session.commit()
            flash(f'Prodotto "{item.product_name}" aggiornato!', 'success')
            return redirect(url_for('inventory.index'))
        
        store_name = get_current_store_name(current_user)
        return render_template('inventory/edit.html', item=item, store_name=store_name)
        
    except Exception as e:
        session.rollback()
        flash(f'Errore modifica prodotto: {str(e)}', 'error')
        return redirect(url_for('inventory.index'))
    finally:
        session.close()

@inventory_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Rimuovi prodotto dal magazzino"""
    set_model_bind_key(current_user)
    session = get_store_db_session(current_user)
    
    try:
        item = session.query(Inventory).get(id)
        if not item:
            flash('Prodotto non trovato!', 'error')
            return redirect(url_for('inventory.index'))
        
        product_name = item.product_name
        session.delete(item)
        session.commit()
        
        flash(f'Prodotto "{product_name}" rimosso dal magazzino!', 'success')
        
    except Exception as e:
        session.rollback()
        flash(f'Errore rimozione prodotto: {str(e)}', 'error')
    finally:
        session.close()
    
    return redirect(url_for('inventory.index'))

@inventory_bp.route('/adjust_stock/<int:id>', methods=['POST'])
@login_required
def adjust_stock(id):
    """Aggiusta manualmente le scorte di un prodotto"""
    set_model_bind_key(current_user)
    session = get_store_db_session(current_user)
    
    try:
        item = session.query(Inventory).get(id)
        if not item:
            return jsonify({'success': False, 'message': 'Prodotto non trovato'})
        
        adjustment = int(request.form['adjustment'])
        reason = request.form.get('reason', 'Aggiustamento manuale')
        
        old_quantity = item.quantity
        item.quantity = max(0, item.quantity + adjustment)  # Non può andare sotto 0
        item.updated_at = datetime.utcnow()
        
        # Aggiorna le note con il motivo
        if item.notes:
            item.notes += f"\n{datetime.now().strftime('%d/%m/%Y')}: {reason} ({old_quantity} → {item.quantity})"
        else:
            item.notes = f"{datetime.now().strftime('%d/%m/%Y')}: {reason} ({old_quantity} → {item.quantity})"
        
        session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Scorte aggiornate: {old_quantity} → {item.quantity}',
            'new_quantity': item.quantity
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': f'Errore: {str(e)}'})
    finally:
        session.close()

@inventory_bp.route('/api/search')
@login_required
def api_search():
    """API per cercare prodotti nel magazzino (usata nella vendita)"""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    set_model_bind_key(current_user)
    session = get_store_db_session(current_user)
    
    try:
        # Cerca nei nomi prodotto, brand, modello
        items = session.query(Inventory).filter(
            (Inventory.product_name.contains(query)) |
            (Inventory.brand.contains(query)) |
            (Inventory.model.contains(query)) |
            (Inventory.device_brand.contains(query))
        ).filter(Inventory.quantity > 0).all()
        
        results = []
        for item in items:
            results.append({
                'id': item.id,
                'name': item.product_name,
                'brand': item.brand,
                'model': item.model,
                'price': item.price,
                'quantity': item.quantity,
                'description': f"{item.brand} {item.device_brand} {item.model} - {item.color} - €{item.price:.2f}"
            })
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify([])
    finally:
        session.close()

def update_inventory_after_sale(inventory_item_id, quantity_sold, user):
    """Aggiorna automaticamente il magazzino dopo una vendita"""
    if not inventory_item_id:
        return True  # Vendita senza prodotto magazzino
        
    set_model_bind_key(user)
    session = get_store_db_session(user)
    
    try:
        item = session.query(Inventory).get(inventory_item_id)
        if not item:
            return False
        
        if item.quantity < quantity_sold:
            return False  # Scorte insufficienti
        
        # Aggiorna le scorte
        old_quantity = item.quantity
        item.quantity -= quantity_sold
        item.updated_at = datetime.utcnow()
        
        # Aggiorna le note con la vendita
        sale_note = f"{datetime.now().strftime('%d/%m/%Y')}: Vendita -{quantity_sold} ({old_quantity} → {item.quantity})"
        if item.notes:
            item.notes += f"\n{sale_note}"
        else:
            item.notes = sale_note
        
        session.commit()
        return True
        
    except Exception as e:
        session.rollback()
        print(f"Errore aggiornamento magazzino: {e}")
        return False
    finally:
        session.close()

@inventory_bp.route('/api/products')
@login_required
def api_products():
    """API per ottenere prodotti del magazzino in formato JSON"""
    set_model_bind_key(current_user)
    session = get_store_db_session(current_user)
    
    try:
        items = session.query(Inventory).filter(Inventory.quantity > 0).all()
        
        products = []
        for item in items:
            products.append({
                'id': item.id,
                'product_name': item.product_name,
                'model': item.model,
                'brand': item.brand,
                'device_brand': item.device_brand,
                'quantity': item.quantity,
                'price': float(item.price),
                'category': item.category
            })
        
        return jsonify({'products': products})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@inventory_bp.route('/export/low-stock')
@login_required
def export_low_stock():
    """Export HTML prodotti con scorte basse (0-1) in formato tabella"""
    set_model_bind_key(current_user)
    session = get_store_db_session(current_user)
    store_name = get_current_store_name(current_user)
    
    try:
        # Query prodotti con scorte 0-1
        items = session.query(Inventory).filter(Inventory.quantity <= 1).order_by(
            Inventory.brand.asc(), Inventory.product_name.asc()
        ).all()
        
        # Organizza per brand
        products_by_brand = {
            'Vodafone': [],
            'Wind': [],
            'Fastweb': [],
            'No Brand': []
        }
        
        for item in items:
            brand = item.brand or 'No Brand'
            brand_key = 'No Brand'
            
            if 'vodafone' in brand.lower():
                brand_key = 'Vodafone'
            elif 'wind' in brand.lower():
                brand_key = 'Wind'
            elif 'fastweb' in brand.lower():
                brand_key = 'Fastweb'
            
            products_by_brand[brand_key].append(item)
        
        return render_template('inventory/export_low_stock.html',
                             products_by_brand=products_by_brand,
                             store_name=store_name,
                             export_date=datetime.now().strftime('%d/%m/%Y %H:%M'))
        
    except Exception as e:
        session.rollback()
        flash(f'Errore export: {str(e)}', 'error')
        return redirect(url_for('inventory.index'))
    finally:
        session.close()

def init_inventory_routes(app):
    """Inizializza le routes del magazzino"""
    app.register_blueprint(inventory_bp, url_prefix='/inventory')