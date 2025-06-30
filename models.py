from app import db
from flask_login import UserMixin
from datetime import datetime, date
from sqlalchemy import func

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='manager')  # 'owner' or 'manager'
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    store = db.relationship('Store', backref='managers')

class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model):
    __bind_key__ = None  # Will be set dynamically based on user's store
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    birth_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    # Offerta attuale
    current_offer = db.Column(db.String(200))  # Nome dell'offerta attuale
    offer_expiry_date = db.Column(db.Date)     # Data di scadenza dell'offerta
    offer_notes = db.Column(db.Text)           # Note sull'offerta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_offer_expiring_soon(self):
        """Check if customer's offer is expiring within 7 days"""
        if not self.offer_expiry_date:
            return False
        
        today = date.today()
        days_until_expiry = (self.offer_expiry_date - today).days
        return 0 <= days_until_expiry <= 7
    
    @property
    def days_until_offer_expiry(self):
        """Get number of days until offer expires"""
        if not self.offer_expiry_date:
            return None
        
        today = date.today()
        return (self.offer_expiry_date - today).days

class Contract(db.Model):
    __bind_key__ = None  # Will be set dynamically based on user's store
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, nullable=False)  # Reference to customer in same database
    manager_username = db.Column(db.String(64), nullable=False)  # Store manager username instead of ID
    service_type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # 'active', 'expired', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def is_expiring_soon(self):
        if self.end_date and self.status == 'active':
            days_until_expiry = (self.end_date - date.today()).days
            return 0 <= days_until_expiry <= 7
        return False

class Sale(db.Model):
    __bind_key__ = None  # Will be set dynamically based on user's store
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, nullable=False)  # Reference to customer in same database
    manager_username = db.Column(db.String(64), nullable=False)  # Store manager username instead of ID
    service_type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))  # 'cash', 'card', 'bank_transfer'
    notes = db.Column(db.Text)
    sale_date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Promotion(db.Model):
    __bind_key__ = None  # Will be set dynamically based on user's store
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    discount_percentage = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='active')  # 'active', 'inactive', 'expired'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def is_active(self):
        today = date.today()
        return (self.status == 'active' and 
                self.start_date <= today <= self.end_date)

class Goal(db.Model):
    __bind_key__ = None  # Will be set dynamically based on user's store
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)  # e.g., 'SIM WindTre', 'Fibra Vodafone'
    target_amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1-12
    year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CompensationRate(db.Model):
    __bind_key__ = None  # Will be set dynamically based on user's store
    id = db.Column(db.Integer, primary_key=True)
    service_type = db.Column(db.String(50), nullable=False)
    manager_username = db.Column(db.String(64), nullable=False)  # Store manager username instead of ID
    base_rate = db.Column(db.Float, nullable=False)
    threshold = db.Column(db.Integer, nullable=False)  # Number of sales needed for bonus
    bonus_rate = db.Column(db.Float, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
