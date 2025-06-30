from flask import Blueprint, render_template, redirect, url_for, session, make_response
from flask_login import login_required, current_user
from sqlalchemy import func, extract
import datetime
from models import Sale, Contract, Customer, Goal, Store, db
from utils import get_accessible_stores, filter_by_store_access, get_service_display_name
import database_manager
import sqlite3

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
    current_store_id = session.get('current_store_id', current_user.store_id)
    current_store = Store.query.get(current_store_id)

    store_db_map = {1: 'cossa', 2: 'avigliana', 3: 'grappa'}
    store_name = store_db_map.get(current_store_id, 'cossa')

    import os
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'{store_name}.db')
    store_conn = sqlite3.connect(db_path)
    store_conn.row_factory = sqlite3.Row

    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    today = datetime.date.today()

    cursor = store_conn.cursor()
    try:
        cursor.execute("SELECT SUM(amount) FROM sale WHERE sale_date = ?", (today.strftime('%Y-%m-%d'),))
        daily_revenue = cursor.fetchone()[0] or 0
    except sqlite3.OperationalError:
        daily_revenue = 0

    try:
        cursor.execute("SELECT SUM(amount) FROM sale WHERE strftime('%m', sale_date) = ? AND strftime('%Y', sale_date) = ?", 
                       (f"{current_month:02d}", str(current_year)))
        monthly_revenue = cursor.fetchone()[0] or 0
    except sqlite3.OperationalError:
        monthly_revenue = 0

    try:
        cursor.execute("SELECT COUNT(*) FROM customer")
        customer_count = cursor.fetchone()[0] or 0
    except sqlite3.OperationalError:
        customer_count = 0

    try:
        cursor.execute("SELECT COUNT(*) FROM sale WHERE strftime('%m', sale_date) = ? AND strftime('%Y', sale_date) = ?", 
                       (f"{current_month:02d}", str(current_year)))
        sales_count = cursor.fetchone()[0] or 0
    except sqlite3.OperationalError:
        sales_count = 0

    try:
        cursor.execute("SELECT COUNT(*) FROM contract WHERE status = 'active'")
        active_contracts = cursor.fetchone()[0] or 0
    except sqlite3.OperationalError:
        active_contracts = 0

    try:
        end_date = today + datetime.timedelta(days=30)
        cursor.execute("SELECT COUNT(*) FROM contract WHERE status = 'active' AND end_date BETWEEN ? AND ?", 
                       (today.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        expiring_contracts = cursor.fetchone()[0] or 0
    except sqlite3.OperationalError:
        expiring_contracts = 0

    goals = db.session.query(Goal).filter(
        Goal.month == current_month,
        Goal.year == current_year
    ).all()

    goals_progress = []
    for goal in goals:
        try:
            cursor.execute("SELECT COUNT(id) FROM sale WHERE service_type = ? AND strftime('%m', sale_date) = ? AND strftime('%Y', sale_date) = ?", 
                           (goal.category, f"{current_month:02d}", str(current_year)))
            achieved = cursor.fetchone()[0] or 0
        except sqlite3.OperationalError:
            achieved = 0
        
        progress_percentage = (achieved / goal.target_amount * 100) if goal.target_amount > 0 else 0
        goals_progress.append({
            'goal': goal,
            'achieved': achieved,
            'percentage': min(progress_percentage, 100)
        })

    expiring_offers = []
    try:
        seven_days_ahead = (today + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute("SELECT * FROM customer WHERE offer_expiry_date IS NOT NULL AND offer_expiry_date >= ? AND offer_expiry_date <= ?", 
                       (today.strftime('%Y-%m-%d'), seven_days_ahead))
        expiring_offers_data = cursor.fetchall()
        
        for offer_data in expiring_offers_data:
            expiring_offers.append({
                'id': offer_data[0],
                'first_name': offer_data[1],
                'last_name': offer_data[2],
                'current_offer': offer_data[8],
                'offer_expiry_date': offer_data[9]
            })
    except (sqlite3.OperationalError, IndexError):
        expiring_offers = []

    current_store_name = current_store.name if current_store else 'Cossa'
    current_store_name = f"{current_store_name} ({customer_count} clienti)"

    store_conn.close()

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
    response.headers['Last-Modified'] = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    return response
