
from flask import Blueprint
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    return f"Benvenuto, {current_user.username}!"
