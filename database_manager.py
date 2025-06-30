"""
Database Manager for Multi-Store System
Handles dynamic database binding based on user's store
"""
from flask import g, session
from flask_login import current_user
from app import db
import models
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Mapping of store names to database bind keys
STORE_DB_MAPPING = {
    'Cellular Network Cossa': 'cossa',
    'Cellular Network Avigliana': 'avigliana', 
    'Cellular Network Grappa': 'grappa'
}

# Store database engines and sessions
_store_engines = {}
_store_sessions = {}

def get_store_bind_key(user):
    """Get the database bind key for a user's store"""
    if user.role == 'owner':
        # Owner can access any store, check session for current store
        current_store_id = session.get('current_store_id')
        if current_store_id:
            store = models.Store.query.get(current_store_id)
            if store:
                return STORE_DB_MAPPING.get(store.name)
        # Default to first store if no selection
        return 'cossa'
    elif user.role == 'manager' and user.store:
        return STORE_DB_MAPPING.get(user.store.name)
    return 'cossa'  # Default

def get_store_bind_key_from_id(store_id):
    """Get the database bind key from store_id"""
    store_mapping = {
        1: 'cossa',
        2: 'avigliana', 
        3: 'grappa'
    }
    return store_mapping.get(store_id, 'cossa')

def get_store_engine(bind_key):
    """Get or create engine for store database"""
    if bind_key not in _store_engines:
        from app import app
        db_url = app.config['SQLALCHEMY_BINDS'].get(bind_key, f'sqlite:///{bind_key}.db')
        _store_engines[bind_key] = create_engine(db_url)
    return _store_engines[bind_key]

def get_store_session(bind_key):
    """Get or create session for store database"""
    if bind_key not in _store_sessions:
        engine = get_store_engine(bind_key)
        Session = sessionmaker(bind=engine)
        _store_sessions[bind_key] = Session()
    return _store_sessions[bind_key]

def set_model_bind_key(user):
    """Set the bind key for all store-specific models based on user's store"""
    bind_key = get_store_bind_key(user)
    
    # Set bind key for all store-specific models
    models.Customer.__bind_key__ = bind_key
    models.Sale.__bind_key__ = bind_key
    models.Contract.__bind_key__ = bind_key
    models.Promotion.__bind_key__ = bind_key
    models.Goal.__bind_key__ = bind_key
    models.CompensationRate.__bind_key__ = bind_key
    
    return bind_key

def get_store_db_session(user):
    """Get database session for user's store"""
    bind_key = get_store_bind_key(user)
    set_model_bind_key(user)
    return get_store_session(bind_key)

def init_store_databases():
    """Initialize all store databases with tables"""
    from app import app
    
    with app.app_context():
        # Create tables for each store database using direct engine connections
        for bind_key in ['cossa', 'avigliana', 'grappa']:
            engine = get_store_engine(bind_key)
            
            # Create all tables directly using the engine
            models.Customer.metadata.create_all(engine)
            models.Sale.metadata.create_all(engine) 
            models.Contract.metadata.create_all(engine)
            models.Promotion.metadata.create_all(engine)
            models.Goal.metadata.create_all(engine)
            models.CompensationRate.metadata.create_all(engine)

def query_with_bind(model_class, user):
    """Create a query with the correct database bind for user's store"""
    bind_key = set_model_bind_key(user)
    return model_class.query

def get_customer_by_id(customer_id, user):
    """Get customer by ID from user's store database"""
    set_model_bind_key(user)
    store_session = get_store_db_session(user)
    return store_session.query(models.Customer).filter(models.Customer.id == customer_id).first()

def get_current_store_name(user):
    """Get the current store name for display"""
    if user.role == 'owner':
        from flask import session
        current_store_id = session.get('current_store_id')
        if current_store_id:
            store = models.Store.query.get(current_store_id)
            if store:
                return store.name
        return 'Cellular Network Cossa'  # Default
    elif user.role == 'manager' and user.store:
        return user.store.name
    return 'Cellular Network Cossa'