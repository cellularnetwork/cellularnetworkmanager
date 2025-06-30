from flask import Blueprint, render_template, redirect, url_for, session, make_response
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from datetime import datetime, date, timedelta
from models import Sale, Contract, Customer, Goal, Store, db
from utils import get_accessible_stores, filter_by_store_access, get_service_display_name
import database_manager

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/switch_store/<int:store_id>')
@login_required
def switch_store(store_id):
    """Switch current store for owner"""
    if current_user.role != 'owner':
        return redirect(url_for('dashboard.index'))
    
    store = Store.query.get_or_404(store_id)
    session['current_store_id'] = store_id
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/')
@login_required
def index():
    # Get store-specific database session
    store_session = database_manager.get_store_db_session(current_user)
    
    # Current month and year
    current_month = datetime.now().month
    current_year = datetime.now().year
    today = date.today()
    
    # Daily revenue (today) from store database
    daily_revenue = store_session.query(func.sum(Sale.amount)).filter(
        Sale.sale_date == today
    ).scalar() or 0
    
    # Monthly revenue from store database
    monthly_revenue = store_session.query(func.sum(Sale.amount)).filter(
        extract('month', Sale.sale_date) == current_month,
        extract('year', Sale.sale_date) == current_year
    ).scalar() or 0
    
    # Customer count from store database
    customer_count = store_session.query(Customer).count()
    
    # Sales count (current month) from store database
    sales_count = store_session.query(Sale).filter(
        extract('month', Sale.sale_date) == current_month,
        extract('year', Sale.sale_date) == current_year
    ).count()
    
    # Active contracts count from store database
    active_contracts = store_session.query(Contract).filter(
        Contract.status == 'active'
    ).count()
    
    # Expiring contracts (next 30 days) from store database
    end_date = today + timedelta(days=30)
    expiring_contracts = store_session.query(Contract).filter(
        Contract.status == 'active',
        Contract.end_date.between(today, end_date)
    ).count()
    
    # Goals progress for current month from store database
    goals = store_session.query(Goal).filter(
        Goal.month == current_month,
        Goal.year == current_year
    ).all()
    
    goals_progress = []
    for goal in goals:
        # Per gli obiettivi contiamo il numero di vendite (punti), non l'importo
        achieved = store_session.query(func.count(Sale.id)).filter(
            Sale.service_type == goal.category,
            extract('month', Sale.sale_date) == current_month,
            extract('year', Sale.sale_date) == current_year
        ).scalar() or 0
        
        progress_percentage = (achieved / goal.target_amount * 100) if goal.target_amount > 0 else 0
        goals_progress.append({
            'goal': goal,
            'achieved': achieved,
            'percentage': min(progress_percentage, 100)
        })

    # Get customers with expiring offers from store database
    expiring_offers = store_session.query(Customer).filter(
        Customer.offer_expiry_date.isnot(None),
        Customer.offer_expiry_date >= today,
        Customer.offer_expiry_date <= today + timedelta(days=7)
    ).all()
    
    # Get current store name for display
    current_store_name = database_manager.get_current_store_name(current_user)
    
    # Close store session
    store_session.close()
    
    # Create response with aggressive anti-cache headers
    response = make_response(render_template('dashboard.html',
                         daily_revenue=daily_revenue,
                         monthly_revenue=monthly_revenue,
                         customer_count=customer_count,
                         sales_count=sales_count,
                         active_contracts=active_contracts,
                         expiring_contracts=expiring_contracts,
                         expiring_offers=expiring_offers,
                         goals_progress=goals_progress,
                         current_store_name=current_store_name,
                         current_date=today,
                         current_month=current_month,
                         current_year=current_year,
                         get_service_display_name=get_service_display_name))
    
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Last-Modified'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    return response