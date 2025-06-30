from flask import Blueprint, render_template, request, Response
from flask_login import login_required, current_user
from models import Sale, Contract, Customer, db
from utils import filter_by_store_access, get_service_display_name
from sqlalchemy import func, extract
from datetime import datetime, timedelta
import csv
import io
import database_manager

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
def index():
    from datetime import date
    return render_template('reports.html', current_date=date.today())

@reports_bp.route('/sales/export')
@login_required
def export_sales():
    # Get parameters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    format_type = request.args.get('format', 'csv')
    
    # Set database binding for user's store
    database_manager.set_model_bind_key(current_user)
    store_session = database_manager.get_store_db_session(current_user)
    
    try:
        # Build query from correct store database
        query = store_session.query(Sale)
        
        if date_from:
            query = query.filter(Sale.sale_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        
        if date_to:
            query = query.filter(Sale.sale_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        
        sales = query.order_by(Sale.sale_date.desc()).all()
        
        if format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Data', 'Cliente', 'Manager', 'Tipo Servizio', 
                'Importo', 'Metodo Pagamento', 'Negozio', 'Note'
            ])
            
            # Write data
            for sale in sales:
                # Get customer data from same session
                customer = store_session.query(Customer).filter(Customer.id == sale.customer_id).first()
                customer_name = customer.full_name if customer else 'Cliente non trovato'
                
                writer.writerow([
                    sale.sale_date.strftime('%Y-%m-%d'),
                    customer_name,
                    sale.manager_username,
                    get_service_display_name(sale.service_type),
                    sale.amount,
                    sale.payment_method or '',
                    database_manager.get_current_store_name(current_user),
                    sale.notes or ''
                ])
            
            output.seek(0)
            
            # Create response
            response = Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=vendite_{database_manager.get_current_store_name(current_user).lower()}_{datetime.now().strftime("%Y%m%d")}.csv'
                }
            )
            
            return response
    finally:
        store_session.close()

@reports_bp.route('/contracts/export')
@login_required
def export_contracts():
    # Get parameters
    status_filter = request.args.get('status', '')
    format_type = request.args.get('format', 'csv')
    
    # Build query
    query = Contract.query.filter(filter_by_store_access(Contract, current_user))
    
    if status_filter:
        query = query.filter(Contract.status == status_filter)
    
    contracts = query.order_by(Contract.created_at.desc()).all()
    
    if format_type == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Customer', 'Manager', 'Service Type', 'Amount',
            'Start Date', 'End Date', 'Status', 'Store'
        ])
        
        # Write data
        for contract in contracts:
            writer.writerow([
                contract.customer.full_name,
                contract.manager.username,
                contract.service_type,
                contract.amount,
                contract.start_date.strftime('%Y-%m-%d'),
                contract.end_date.strftime('%Y-%m-%d') if contract.end_date else '',
                contract.status,
                contract.store.name
            ])
        
        output.seek(0)
        
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=contracts_report_{datetime.now().strftime("%Y%m%d")}.csv'
            }
        )
        
        return response

@reports_bp.route('/customers/export')
@login_required
def export_customers():
    format_type = request.args.get('format', 'csv')
    
    # Set database binding for user's store
    database_manager.set_model_bind_key(current_user)
    store_session = database_manager.get_store_db_session(current_user)
    
    try:
        # Get customers from the correct store database
        customers = store_session.query(Customer).order_by(Customer.created_at.desc()).all()
        
        if format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Nome', 'Cognome', 'Telefono', 'Email',
                'Indirizzo', 'Data Nascita', 'Negozio', 'Offerta Attuale', 'Scadenza Offerta', 'Note'
            ])
            
            # Write data
            for customer in customers:
                writer.writerow([
                    customer.first_name,
                    customer.last_name,
                    customer.phone or '',
                    customer.email or '',
                    customer.address or '',
                    customer.birth_date.strftime('%Y-%m-%d') if customer.birth_date else '',
                    database_manager.get_current_store_name(current_user),
                    customer.current_offer or '',
                    customer.offer_expiry_date.strftime('%Y-%m-%d') if customer.offer_expiry_date else '',
                    customer.notes or ''
                ])
            
            output.seek(0)
            
            response = Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=clienti_{database_manager.get_current_store_name(current_user).lower().replace(" ", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            )
            
            return response
    finally:
        store_session.close()

@reports_bp.route('/monthly')
@login_required
def monthly_report():
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    
    # Get store-specific database session
    database_manager.set_model_bind_key(current_user)
    store_session = database_manager.get_store_db_session(current_user)
    
    try:
        # Sales summary
        sales_summary = store_session.query(
            func.count(Sale.id).label('total_sales'),
            func.sum(Sale.amount).label('total_revenue')
        ).filter(
            extract('month', Sale.sale_date) == month,
            extract('year', Sale.sale_date) == year
        ).first()
        
        # Sales by service type
        sales_by_service = store_session.query(
            Sale.service_type,
            func.count(Sale.id).label('count'),
            func.sum(Sale.amount).label('revenue')
        ).filter(
            extract('month', Sale.sale_date) == month,
            extract('year', Sale.sale_date) == year
        ).group_by(Sale.service_type).all()
        
        # New customers
        new_customers = store_session.query(func.count(Customer.id)).filter(
            extract('month', Customer.created_at) == month,
            extract('year', Customer.created_at) == year
        ).scalar() or 0
        
        # Active contracts
        active_contracts = store_session.query(func.count(Contract.id)).filter(
            Contract.status == 'active'
        ).scalar() or 0
        
        # Monthly names in Italian
        month_names = {
            1: 'Gennaio', 2: 'Febbraio', 3: 'Marzo', 4: 'Aprile',
            5: 'Maggio', 6: 'Giugno', 7: 'Luglio', 8: 'Agosto',
            9: 'Settembre', 10: 'Ottobre', 11: 'Novembre', 12: 'Dicembre'
        }
        
        current_store_name = database_manager.get_current_store_name(current_user)
        
    finally:
        store_session.close()
    
    return render_template('monthly_report.html',
                         month=month,
                         year=year,
                         month_name=month_names[month],
                         current_store_name=current_store_name,
                         sales_summary=sales_summary,
                         sales_by_service=sales_by_service,
                         new_customers=new_customers,
                         active_contracts=active_contracts,
                         months=range(1, 13),
                         years=range(2020, 2030),
                         get_service_display_name=get_service_display_name)

@reports_bp.route('/weekly')
@login_required
def weekly_report():
    # Get the current week
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Sales for the week
    weekly_sales = Sale.query.filter(
        filter_by_store_access(Sale, current_user),
        Sale.sale_date.between(week_start, week_end)
    ).all()
    
    # Group by day
    sales_by_day = {}
    for i in range(7):
        day = week_start + timedelta(days=i)
        sales_by_day[day] = {
            'sales': [s for s in weekly_sales if s.sale_date == day],
            'total': sum(s.amount for s in weekly_sales if s.sale_date == day)
        }
    
    total_week_revenue = sum(sale.amount for sale in weekly_sales)
    
    return render_template('weekly_report.html',
                         week_start=week_start,
                         week_end=week_end,
                         sales_by_day=sales_by_day,
                         total_week_revenue=total_week_revenue,
                         current_date=today)
