from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Goal, Sale, db
from utils import get_service_types, get_service_display_name
import database_manager
from datetime import datetime, date
from sqlalchemy import func, extract
from service_config import get_service_display_name

goals_bp = Blueprint('goals', __name__, url_prefix='/goals')

@goals_bp.route('/')
@login_required
def index():
    # Get store-specific database session
    store_session = database_manager.get_store_db_session(current_user)
    
    # Get current month/year
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Get goals for current month from store database
    goals = store_session.query(Goal).filter(
        Goal.month == current_month,
        Goal.year == current_year
    ).all()
    
    # Calculate progress for each goal
    goals_with_progress = []
    for goal in goals:
        # Get sales count (points) for this goal's category in current month from store database
        sales_total = store_session.query(func.count(Sale.id)).filter(
            Sale.service_type == goal.category,
            extract('month', Sale.sale_date) == current_month,
            extract('year', Sale.sale_date) == current_year
        ).scalar() or 0
        
        progress_percentage = (sales_total / goal.target_amount * 100) if goal.target_amount > 0 else 0
        
        goals_with_progress.append({
            'goal': goal,
            'current_count': sales_total,
            'progress_percentage': min(progress_percentage, 100),
            'is_completed': sales_total >= goal.target_amount
        })
    
    # Get current store name for display
    current_store_name = database_manager.get_current_store_name(current_user)
    
    return render_template('goals_simple.html',
                         goals=goals,
                         goals_with_progress=goals_with_progress,
                         current_month=current_month,
                         current_year=current_year,
                         current_store_name=current_store_name,
                         get_service_display_name=get_service_display_name)

@goals_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    # Set database binding for user's store
    database_manager.set_model_bind_key(current_user)
    
    if request.method == 'POST':
        # Get the store-specific database session
        store_session = database_manager.get_store_db_session(current_user)
        
        goal = Goal(
            category=request.form['category'],
            target_amount=float(request.form['target_amount']),
            month=int(request.form['month']),
            year=int(request.form['year'])
        )
        
        store_session.add(goal)
        store_session.commit()
        flash('Obiettivo creato con successo!', 'success')
        return redirect(url_for('goals.index'))
    
    return render_template('goal_form.html',
                         goal=None,
                         service_types=get_service_types(),
                         get_service_display_name=get_service_display_name)

@goals_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    # Get store-specific database session
    store_session = database_manager.get_store_db_session(current_user)
    
    goal = store_session.query(Goal).get(id)
    if not goal:
        flash('Obiettivo non trovato!', 'error')
        return redirect(url_for('goals.index'))
    
    if request.method == 'POST':
        goal.category = request.form['category']
        goal.target_amount = float(request.form['target_amount'])
        goal.month = int(request.form['month'])
        goal.year = int(request.form['year'])
        
        store_session.commit()
        flash('Obiettivo aggiornato con successo!', 'success')
        return redirect(url_for('goals.index'))
    
    return render_template('goal_form.html',
                         goal=goal,
                         service_types=get_service_types(),
                         get_service_display_name=get_service_display_name)

@goals_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    # Get store-specific database session
    store_session = database_manager.get_store_db_session(current_user)
    
    goal = store_session.query(Goal).get(id)
    if not goal:
        flash('Obiettivo non trovato!', 'error')
        return redirect(url_for('goals.index'))
    
    store_session.delete(goal)
    store_session.commit()
    flash('Obiettivo eliminato con successo!', 'success')
    return redirect(url_for('goals.index'))

@goals_bp.route('/api/progress/<int:month>/<int:year>')
@login_required
def api_progress(month, year):
    """API endpoint per ottenere il progresso degli obiettivi"""
    # Set database binding for user's store
    database_manager.set_model_bind_key(current_user)
    
    goals = Goal.query.filter(
        Goal.month == month,
        Goal.year == year
    ).all()
    
    progress_data = []
    for goal in goals:
        sales_count = Sale.query.filter(
            Sale.service_type == goal.category,
            func.extract('month', Sale.sale_date) == month,
            func.extract('year', Sale.sale_date) == year
        ).count()
        
        progress_percentage = (sales_count / goal.target_amount * 100) if goal.target_amount > 0 else 0
        
        progress_data.append({
            'id': goal.id,
            'category': goal.category,
            'target': goal.target_amount,
            'current': sales_count,
            'progress': min(progress_percentage, 100),
            'completed': sales_count >= goal.target_amount
        })
    
    return jsonify(progress_data)