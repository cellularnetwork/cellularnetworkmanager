from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import CompensationRate, Sale, User, db
from utils import get_service_types, get_service_display_name
import database_manager
from datetime import datetime, date
from sqlalchemy import func, extract

compensation_bp = Blueprint('compensation', __name__, url_prefix='/compensation')

@compensation_bp.route('/')
@login_required
def index():
    # Solo il titolare può accedere alla sezione compensi
    if current_user.role != 'owner':
        flash('Accesso negato. Solo il titolare può visualizzare i compensi.', 'error')
        return redirect(url_for('dashboard.index'))
    
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    store_filter = request.args.get('store', 'all')
    
    # Raccogli dati da tutti i negozi
    all_compensation_data = []
    stores = ['cossa', 'avigliana', 'grappa']
    store_names = {
        'cossa': 'Cellular Network Cossa',
        'avigliana': 'Cellular Network Avigliana', 
        'grappa': 'Cellular Network Grappa'
    }
    
    for store_key in stores:
        if store_filter != 'all' and store_filter != store_key:
            continue
            
        # Set bind key per questo negozio
        CompensationRate.__bind_key__ = store_key
        Sale.__bind_key__ = store_key
        
        # Get compensation rates for the selected month/year
        rates = CompensationRate.query.filter(
            CompensationRate.month == month,
            CompensationRate.year == year
        ).all()
        
        # Get unique managers from compensation rates
        manager_usernames = list(set(rate.manager_username for rate in rates))
        
        for manager_username in manager_usernames:
            manager_compensation = {
                'manager_username': manager_username,
                'store_name': store_names[store_key],
                'total_base': 0,
                'total_bonus': 0,
                'total': 0,
                'details': []
            }
            
            # Get manager's rates for this month
            manager_rates = [r for r in rates if r.manager_username == manager_username]
            
            for rate in manager_rates:
                # Count sales for this service type and manager
                sales_count = db.session.query(func.count(Sale.id)).filter(
                    Sale.manager_username == manager_username,
                    Sale.service_type == rate.service_type,
                    extract('month', Sale.sale_date) == month,
                    extract('year', Sale.sale_date) == year
                ).scalar() or 0
                
                # Calculate compensation
                base_compensation = sales_count * rate.base_rate
                bonus_compensation = 0
                if sales_count >= rate.threshold:
                    bonus_compensation = (sales_count - rate.threshold) * rate.bonus_rate
                
                total_compensation = base_compensation + bonus_compensation
                
                manager_compensation['total_base'] += base_compensation
                manager_compensation['total_bonus'] += bonus_compensation
                manager_compensation['total'] += total_compensation
                
                manager_compensation['details'].append({
                    'service_type': rate.service_type,
                    'sales_count': sales_count,
                    'base_rate': rate.base_rate,
                    'threshold': rate.threshold,
                    'bonus_rate': rate.bonus_rate,
                    'base_compensation': base_compensation,
                    'bonus_compensation': bonus_compensation,
                    'total_compensation': total_compensation
                })
            
            if manager_rates:  # Solo se ci sono rate per questo manager
                all_compensation_data.append(manager_compensation)
    
    return render_template('compensation.html',
                         compensation_data=all_compensation_data,
                         month=month,
                         year=year,
                         store_filter=store_filter,
                         stores=stores,
                         current_store_name="Tutti i Negozi" if store_filter == 'all' else store_names.get(store_filter, ''),
                         months=range(1, 13),
                         years=range(2020, 2030))

@compensation_bp.route('/rates')
@login_required
def rates():
    # Solo il titolare può accedere alla sezione compensi
    if current_user.role != 'owner':
        flash('Accesso negato. Solo il titolare può visualizzare i compensi.', 'error')
        return redirect(url_for('dashboard.index'))
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    
    # Set database binding for user's store
    database_manager.set_model_bind_key(current_user)
    store_session = database_manager.get_store_db_session(current_user)
    
    rates = store_session.query(CompensationRate).filter(
        CompensationRate.month == month,
        CompensationRate.year == year
    ).all()
    
    store_session.close()
    
    # Get current store name for display
    current_store_name = database_manager.get_current_store_name(current_user)
    
    return render_template('compensation_rates.html',
                         rates=rates,
                         month=month,
                         year=year,
                         current_store_name=current_store_name,
                         months=range(1, 13),
                         years=range(2020, 2030))

@compensation_bp.route('/rates/new', methods=['GET', 'POST'])
@login_required
def new_rate():
    # Solo il titolare può accedere alla sezione compensi
    if current_user.role != 'owner':
        flash('Accesso negato. Solo il titolare può visualizzare i compensi.', 'error')
        return redirect(url_for('dashboard.index'))
    # Set database binding for user's store
    database_manager.set_model_bind_key(current_user)
    
    if request.method == 'POST':
        # Get the store-specific database session
        store_session = database_manager.get_store_db_session(current_user)
        
        rate = CompensationRate(
            service_type=request.form['service_type'],
            manager_username=request.form['manager_username'],
            base_rate=float(request.form['base_rate']),
            threshold=int(request.form['threshold']),
            bonus_rate=float(request.form['bonus_rate']),
            month=int(request.form['month']),
            year=int(request.form['year'])
        )
        
        store_session.add(rate)
        store_session.commit()
        store_session.close()
        flash('Tariffa compenso creata con successo!', 'success')
        return redirect(url_for('compensation.rates'))
    
    return render_template('compensation_rate_form.html',
                         rate=None,
                         service_types=get_service_types(),
                         months=range(1, 13),
                         years=range(2020, 2030),
                         get_service_display_name=get_service_display_name,
                         current_month=datetime.now().month)

@compensation_bp.route('/rates/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_rate(id):
    # Solo il titolare può accedere alla sezione compensi
    if current_user.role != 'owner':
        flash('Accesso negato. Solo il titolare può visualizzare i compensi.', 'error')
        return redirect(url_for('dashboard.index'))
    # Set database binding for user's store
    database_manager.set_model_bind_key(current_user)
    
    rate = CompensationRate.query.get_or_404(id)
    
    if request.method == 'POST':
        # Get the store-specific database session
        store_session = database_manager.get_store_db_session(current_user)
        
        rate.service_type = request.form['service_type']
        rate.manager_username = request.form['manager_username']
        rate.base_rate = float(request.form['base_rate'])
        rate.threshold = int(request.form['threshold'])
        rate.bonus_rate = float(request.form['bonus_rate'])
        rate.month = int(request.form['month'])
        rate.year = int(request.form['year'])
        
        store_session.commit()
        flash('Compensation rate updated successfully!', 'success')
        return redirect(url_for('compensation.rates'))
    
    return render_template('compensation_rate_form.html',
                         rate=rate,
                         service_types=get_service_types(),
                         months=range(1, 13),
                         years=range(2020, 2030))

@compensation_bp.route('/rates/<int:id>/delete', methods=['POST'])
@login_required
def delete_rate(id):
    # Solo il titolare può accedere alla sezione compensi
    if current_user.role != 'owner':
        flash('Accesso negato. Solo il titolare può visualizzare i compensi.', 'error')
        return redirect(url_for('dashboard.index'))
    # Set database binding for user's store
    database_manager.set_model_bind_key(current_user)
    
    rate = CompensationRate.query.get_or_404(id)
    
    # Get the store-specific database session
    store_session = database_manager.get_store_db_session(current_user)
    
    store_session.delete(rate)
    store_session.commit()
    flash('Compensation rate deleted successfully!', 'success')
    return redirect(url_for('compensation.rates'))