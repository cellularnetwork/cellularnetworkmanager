"""
Sistema di notifiche per offerte clienti in scadenza
Supporta sia offerte legacy che sistema offerte multiple
"""

from flask import Blueprint, jsonify, current_app
from flask_login import login_required, current_user
from datetime import date, timedelta
from models import Customer
import database_manager
from sqlalchemy import text

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notifications_bp.route('/offers-expiring')
@login_required
def offers_expiring():
    """API endpoint per ottenere le notifiche delle offerte in scadenza"""
    try:
        bind_key = database_manager.get_store_bind_key(current_user)
        engine = database_manager.get_store_engine(bind_key)
        
        notifications = []
        today = date.today()
        
        with engine.connect() as conn:
            # Offerte legacy in scadenza nei prossimi 7 giorni
            result = conn.execute(text("""
                SELECT c.id, c.first_name, c.last_name, c.phone, c.current_offer, c.offer_expiry_date
                FROM customer c
                WHERE c.offer_expiry_date IS NOT NULL
                AND c.offer_expiry_date BETWEEN date('now') AND date('now', '+7 days')
                ORDER BY c.offer_expiry_date ASC
            """))
            
            for row in result:
                expiry_date = date.fromisoformat(row[5])
                days_remaining = (expiry_date - today).days
                
                if days_remaining == 0:
                    urgency = 'critical'
                    message = f"L'offerta legacy di {row[1]} {row[2]} scade OGGI!"
                    icon = 'fas fa-exclamation-triangle'
                    color = 'text-danger'
                elif days_remaining <= 2:
                    urgency = 'high'
                    message = f"L'offerta legacy di {row[1]} {row[2]} scade tra {days_remaining} giorni"
                    icon = 'fas fa-clock'
                    color = 'text-warning'
                else:
                    urgency = 'medium'
                    message = f"L'offerta legacy di {row[1]} {row[2]} scade tra {days_remaining} giorni"
                    icon = 'fas fa-info-circle'
                    color = 'text-info'
                
                notifications.append({
                    'type': 'legacy',
                    'id': row[0],
                    'customer_name': f"{row[1]} {row[2]}",
                    'customer_phone': row[3],
                    'current_offer': row[4],
                    'expiry_date': expiry_date.strftime('%d/%m/%Y'),
                    'days_remaining': days_remaining,
                    'urgency': urgency,
                    'message': message,
                    'icon': icon,
                    'color': color,
                    'customer_url': f'/customers/{row[0]}/edit'
                })
            
            # Offerte multiple in scadenza nei prossimi 7 giorni
            try:
                result_multiple = conn.execute(text("""
                    SELECT co.id, co.offer_name, co.offer_type, co.expiry_date,
                           c.id, c.first_name, c.last_name, c.phone
                    FROM customer_offer co
                    JOIN customer c ON co.customer_id = c.id
                    WHERE co.status = 'active' 
                    AND co.expiry_date BETWEEN date('now') AND date('now', '+7 days')
                    ORDER BY co.expiry_date ASC
                """))
                
                for row in result_multiple:
                    expiry_date = date.fromisoformat(row[3])
                    days_remaining = (expiry_date - today).days
                    
                    if days_remaining == 0:
                        urgency = 'critical'
                        message = f"L'offerta '{row[1]}' di {row[5]} {row[6]} scade OGGI!"
                        icon = 'fas fa-exclamation-triangle'
                        color = 'text-danger'
                    elif days_remaining <= 2:
                        urgency = 'high'
                        message = f"L'offerta '{row[1]}' di {row[5]} {row[6]} scade tra {days_remaining} giorni"
                        icon = 'fas fa-clock'
                        color = 'text-warning'
                    else:
                        urgency = 'medium'
                        message = f"L'offerta '{row[1]}' di {row[5]} {row[6]} scade tra {days_remaining} giorni"
                        icon = 'fas fa-info-circle'
                        color = 'text-info'
                    
                    notifications.append({
                        'type': 'multiple',
                        'offer_id': row[0],
                        'offer_name': row[1],
                        'offer_type': row[2],
                        'customer_id': row[4],
                        'customer_name': f"{row[5]} {row[6]}",
                        'customer_phone': row[7],
                        'expiry_date': expiry_date.strftime('%d/%m/%Y'),
                        'days_remaining': days_remaining,
                        'urgency': urgency,
                        'message': message,
                        'icon': icon,
                        'color': color,
                        'customer_url': f'/customers/{row[4]}/offers/{row[0]}/edit'
                    })
            except Exception:
                # Tabella customer_offer non ancora creata
                pass
        
        # Ordina tutte le notifiche per urgenza e data
        notifications.sort(key=lambda x: (x['days_remaining'], x['urgency'] == 'critical'))
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'count': len(notifications)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching notifications: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Errore nel caricamento delle notifiche'
        }), 500

@notifications_bp.route('/count')
@login_required
def notifications_count():
    """API endpoint per ottenere solo il conteggio delle notifiche"""
    try:
        bind_key = database_manager.get_store_bind_key(current_user)
        engine = database_manager.get_store_engine(bind_key)
        
        total_count = 0
        
        with engine.connect() as conn:
            # Conta offerte legacy in scadenza
            result = conn.execute(text("""
                SELECT COUNT(*) FROM customer 
                WHERE offer_expiry_date IS NOT NULL
                AND offer_expiry_date BETWEEN date('now') AND date('now', '+7 days')
            """))
            
            total_count += result.fetchone()[0]
            
            # Conta offerte multiple in scadenza
            try:
                result_multiple = conn.execute(text("""
                    SELECT COUNT(*) FROM customer_offer 
                    WHERE status = 'active'
                    AND expiry_date BETWEEN date('now') AND date('now', '+7 days')
                """))
                
                total_count += result_multiple.fetchone()[0]
            except Exception:
                # Tabella customer_offer non ancora creata
                pass
        
        return jsonify({
            'success': True,
            'count': total_count
        })
        
    except Exception as e:
        current_app.logger.error(f"Error counting notifications: {str(e)}")
        return jsonify({
            'success': False,
            'count': 0
        })