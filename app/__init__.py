from flask import Flask, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
import os

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Конфигурация
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'finance.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'your-jwt-secret-key'

    os.makedirs(app.instance_path, exist_ok=True)

    # Инициализация расширений
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.api_routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)

    # Главная страница — login
    @app.route('/')
    def index():
        return redirect(url_for('auth.login_page'))

    # Ошибки
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not Found'}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'error': 'Internal Server Error'}), 500

    # Создаём таблицы
    with app.app_context():
        db.create_all()

    return app



