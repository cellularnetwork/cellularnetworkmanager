from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Promotion, db
from utils import get_accessible_stores, filter_by_store_access
from datetime import datetime

promotions_bp = Blueprint('promotions', __name__, url_prefix='/promotions')

@promotions_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Promotion.query.filter(filter_by_store_access(Promotion, current_user))
    
    if status_filter:
        query = query.filter(Promotion.status == status_filter)
    
    promotions = query.order_by(Promotion.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('promotions.html', 
                         promotions=promotions,
                         status_filter=status_filter)

@promotions_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        # Determine store_id based on user role
        if current_user.role == 'owner':
            store_id = request.form.get('store_id', type=int)
        else:
            store_id = current_user.store_id
        
        # Get the store-specific database session
        store_session = database_manager.get_store_db_session(current_user)
        
        promotion = Promotion(
            name=request.form['name'],
            discount_percentage=float(request.form['discount_percentage']),
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date(),
            status=request.form.get('status', 'active')
        )
        
        store_session.add(promotion)
        store_session.commit()
        flash('Promotion created successfully!', 'success')
        return redirect(url_for('promotions.index'))
    
    accessible_stores = get_accessible_stores(current_user)
    return render_template('promotion_form.html', promotion=None, stores=accessible_stores)

@promotions_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    promotion = Promotion.query.filter(
        Promotion.id == id,
        filter_by_store_access(Promotion, current_user)
    ).first_or_404()
    
    if request.method == 'POST':
        # Get the store-specific database session
        store_session = database_manager.get_store_db_session(current_user)
        
        promotion.name = request.form['name']
        promotion.discount_percentage = float(request.form['discount_percentage'])
        promotion.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        promotion.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        promotion.status = request.form.get('status', 'active')
        
        store_session.commit()
        flash('Promotion updated successfully!', 'success')
        return redirect(url_for('promotions.index'))
    
    accessible_stores = get_accessible_stores(current_user)
    return render_template('promotion_form.html', promotion=promotion, stores=accessible_stores)

@promotions_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    # Set database binding for user's store
    database_manager.set_model_bind_key(current_user)
    
    promotion = Promotion.query.get_or_404(id)
    
    # Get the store-specific database session
    store_session = database_manager.get_store_db_session(current_user)
    
    store_session.delete(promotion)
    store_session.commit()
    flash('Promotion deleted successfully!', 'success')
    return redirect(url_for('promotions.index'))
