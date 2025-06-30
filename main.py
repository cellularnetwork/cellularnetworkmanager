
from flask import Flask
from flask_login import LoginManager
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from models import User

app = Flask(__name__)
app.secret_key = "myultrasecretkey123!@#"

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(username):
    return User(username)

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)

import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
