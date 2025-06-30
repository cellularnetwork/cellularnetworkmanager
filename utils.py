from models import Store
import database_manager

def get_accessible_stores(user):
    """Get stores accessible to the current user based on their role."""
    if user.role == 'owner':
        return Store.query.all()
    elif user.role == 'manager' and user.store_id:
        return [user.store]
    return []

def filter_by_store_access(model_class, user):
    """Create a filter condition based on user's store access.
    With separate databases, this always returns True since data is already isolated."""
    # With separate databases per store, all data in a database belongs to that store
    database_manager.set_model_bind_key(user)
    return True

def can_access_store(user, store_id):
    """Check if user can access a specific store."""
    if user.role == 'owner':
        return True
    elif user.role == 'manager':
        return user.store_id == store_id
    return False

def format_currency(amount):
    """Format amount as currency."""
    return f"€{amount:,.2f}"

def get_service_types():
    """Get list of available service types."""
    return [
        'vodafone_sim', 'vodafone_fibra', 'vodafone_outdoor', 'vodafone_indoor', 'vodafone_business',
        'wind3_sim', 'wind3_fibra', 'wind3_outdoor', 'wind3_indoor', 'wind3_business',
        'tim_sim', 'tim_fibra', 'tim_outdoor', 'tim_indoor', 'tim_business',
        'iliad_sim', 'iliad_fisso',
        'ho_sim', 'very_mobile_sim', 'sky_sim', 'fastweb_sim', 'fastweb_fisso',
        'sky_wifi', 'sky_tv', 'eolo_fisso',
        'luce', 'gas', 'iren_luce', 'iren_gas', 'iren_internet',
        'edison_luce', 'edison_gas', 'edison_vas', 'edison_internet'
    ]

def get_payment_methods():
    """Get list of available payment methods."""
    return [
        'contanti',
        'carta',
        'bonifico',
        'assegno',
        'paypal'
    ]

def get_contract_statuses():
    """Get list of contract statuses."""
    return [
        'attivo',
        'scaduto',
        'cancellato',
        'in_attesa'
    ]

def get_promotion_statuses():
    """Get list of promotion statuses."""
    return [
        'attiva',
        'inattiva',
        'scaduta'
    ]

def get_service_display_name(service_code):
    """Ottieni il nome visualizzato per un servizio"""
    from service_config import SERVICE_TRANSLATIONS
    return SERVICE_TRANSLATIONS.get(service_code, service_code.replace('_', ' ').title())

def get_service_icon(service_code):
    """Ottieni l'icona per un servizio"""
    from service_config import SERVICE_ICONS
    return SERVICE_ICONS.get(service_code, 'circle')

def get_services_by_category():
    """Ottieni servizi raggruppati per categoria"""
    from service_config import SERVICE_CATEGORIES
    return SERVICE_CATEGORIES
