from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Contract, Customer, User, db
from utils import get_accessible_stores, filter_by_store_access
from datetime import datetime

contracts_bp = Blueprint('contracts', __name__, url_prefix='/contracts')

@contracts_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    service_filter = request.args.get('service', '')
    
    query = Contract.query.filter(filter_by_store_access(Contract, current_user))
    
    if status_filter:
        query = query.filter(Contract.status == status_filter)
    
    if service_filter:
        query = query.filter(Contract.service_type == service_filter)
    
    contracts = query.order_by(Contract.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get unique service types for filter
    service_types = db.session.query(Contract.service_type).filter(
        filter_by_store_access(Contract, current_user)
    ).distinct().all()
    service_types = [st[0] for st in service_types]
    
    return render_template('contracts.html', 
                         contracts=contracts,
                         status_filter=status_filter,
                         service_filter=service_filter,
                         service_types=service_types)

@contracts_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        # Determine store_id based on user role
        if current_user.role == 'owner':
            store_id = request.form.get('store_id', type=int)
            manager_id = request.form.get('manager_id', type=int)
        else:
            store_id = current_user.store_id
            manager_id = current_user.id
        
        # Get the store-specific database session
        store_session = database_manager.get_store_db_session(current_user)
        
        contract = Contract(
            customer_id=request.form['customer_id'],
            manager_username=current_user.username,
            service_type=request.form['service_type'],
            amount=float(request.form['amount']),
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form.get('end_date') else None,
            status=request.form.get('status', 'active')
        )
        
        store_session.add(contract)
        store_session.commit()
        flash('Contract created successfully!', 'success')
        return redirect(url_for('contracts.index'))
    
    # Get customers and managers for the form
    accessible_stores = get_accessible_stores(current_user)
    customers = Customer.query.filter(filter_by_store_access(Customer, current_user)).all()
    
    if current_user.role == 'owner':
        managers = User.query.filter(User.role == 'manager').all()
    else:
        managers = [current_user]
    
    return render_template('contract_form.html', 
                         contract=None, 
                         customers=customers,
                         managers=managers,
                         stores=accessible_stores)

@contracts_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    contract = Contract.query.filter(
        Contract.id == id,
        filter_by_store_access(Contract, current_user)
    ).first_or_404()
    
    if request.method == 'POST':
        # Get the store-specific database session
        store_session = database_manager.get_store_db_session(current_user)
        
        contract.customer_id = request.form['customer_id']
        contract.service_type = request.form['service_type']
        contract.amount = float(request.form['amount'])
        contract.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        contract.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form.get('end_date') else None
        contract.status = request.form.get('status', 'active')
        
        store_session.commit()
        flash('Contract updated successfully!', 'success')
        return redirect(url_for('contracts.index'))
    
    accessible_stores = get_accessible_stores(current_user)
    customers = Customer.query.filter(filter_by_store_access(Customer, current_user)).all()
    
    if current_user.role == 'owner':
        managers = User.query.filter(User.role == 'manager').all()
    else:
        managers = [current_user]
    
    return render_template('contract_form.html', 
                         contract=contract,
                         customers=customers,
                         managers=managers,
                         stores=accessible_stores)

@contracts_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    # Set database binding for user's store
    database_manager.set_model_bind_key(current_user)
    
    contract = Contract.query.get_or_404(id)
    
    # Get the store-specific database session
    store_session = database_manager.get_store_db_session(current_user)
    
    store_session.delete(contract)
    store_session.commit()
    flash('Contract deleted successfully!', 'success')
    return redirect(url_for('contracts.index'))
