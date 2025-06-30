import os
import logging
from datetime import datetime, timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production-clean-reset")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database - SQLite with persistent storage (absolute paths)
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'main.db')}"
app.config["SQLALCHEMY_BINDS"] = {
    'cossa': f"sqlite:///{os.path.join(BASE_DIR, 'cossa.db')}",
    'avigliana': f"sqlite:///{os.path.join(BASE_DIR, 'avigliana.db')}",
    'grappa': f"sqlite:///{os.path.join(BASE_DIR, 'grappa.db')}"
}

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

with app.app_context():
    # Import models and create tables
    import models
    
    # Backup system disattivato per evitare perdita dati clienti
    # try:
    #     from backup_manager import init_backup_system
    #     init_backup_system()
    # except Exception as e:
    #     logging.warning(f"Backup system non avviato: {e}")
    db.create_all()
    
    # Initialize store databases
    from database_manager import init_store_databases
    init_store_databases()
    
    # Create default users if they don't exist
    from models import User, Store
    from werkzeug.security import generate_password_hash
    
    # Create stores if they don't exist
    stores = [
        ('Cellular Network Cossa', 'Negozio di Cossa'),
        ('Cellular Network Avigliana', 'Negozio di Avigliana'), 
        ('Cellular Network Grappa', 'Negozio di Grappa')
    ]
    
    # Update existing stores or create new ones
    existing_stores = Store.query.all()
    if len(existing_stores) == 3:
        # Update existing stores with new names
        existing_stores[0].name = 'Cellular Network Cossa'
        existing_stores[0].description = 'Negozio di Cossa'
        existing_stores[1].name = 'Cellular Network Avigliana' 
        existing_stores[1].description = 'Negozio di Avigliana'
        existing_stores[2].name = 'Cellular Network Grappa'
        existing_stores[2].description = 'Negozio di Grappa'
    else:
        # Create new stores if they don't exist
        for store_name, description in stores:
            if not Store.query.filter_by(name=store_name).first():
                store = Store(name=store_name, description=description)
                db.session.add(store)
    
    # Create default users if they don't exist
    users_data = [
        {'username': 'titolare', 'email': 'titolare@cellularnetwork.it', 'role': 'owner', 'store_id': None},
        {'username': 'manager_cossa', 'email': 'cossa@cellularnetwork.it', 'role': 'manager', 'store_id': 1},
        {'username': 'manager_avigliana', 'email': 'avigliana@cellularnetwork.it', 'role': 'manager', 'store_id': 2},
        {'username': 'manager_grappa', 'email': 'grappa@cellularnetwork.it', 'role': 'manager', 'store_id': 3},
    ]
    
    for user_data in users_data:
        if not User.query.filter_by(username=user_data['username']).first():
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role'],
                store_id=user_data['store_id'],
                password_hash=generate_password_hash('password123')
            )
            db.session.add(user)
    
    db.session.commit()

# Register blueprints
from auth import auth_bp
from dashboard import dashboard_bp
from customers import customers_bp
from contracts import contracts_bp
from sales import sales_bp
# from promotions import promotions_bp
from compensation import compensation_bp
from notifications import notifications_bp
from reports import reports_bp
from goals import goals_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(customers_bp)
# app.register_blueprint(contracts_bp)  # Rimosso come richiesto
app.register_blueprint(sales_bp)

app.register_blueprint(compensation_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(goals_bp)

@app.context_processor
def inject_global_vars():
    """Inject global variables into all templates"""
    from models import Store
    return {
        'all_stores': Store.query.all()
    }

@app.route('/')
def index():
    from flask import redirect, url_for
    return redirect(url_for('dashboard.index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
