from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from app import db, bcrypt
from app.models import User
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Страница login
@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

# API: login
@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        # Валидация обязательных полей
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        if user and bcrypt.check_password_hash(user.password, data['password']):
            token = create_access_token(identity=user.id)
            return jsonify({
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }), 200
        
        return jsonify({'error': 'Invalid credentials'}), 401
        
    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500

# Страница register
@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

# API: register
@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Валидация обязательных полей
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Валидация email
        if '@' not in data['email']:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Валидация длины пароля
        if len(data['password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Валидация длины username
        if len(data['username']) < 3:
            return jsonify({'error': 'Username must be at least 3 characters long'}), 400
        
        # Проверка существования пользователя перед созданием
        existing_user = User.query.filter(
            (User.email == data['email']) | (User.username == data['username'])
        ).first()
        
        if existing_user:
            if existing_user.email == data['email']:
                return jsonify({'error': 'Email already exists'}), 400
            else:
                return jsonify({'error': 'Username already exists'}), 400
        
        hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        user = User(
            username=data['username'], 
            email=data['email'], 
            password=hashed_pw
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }), 201
        
    except IntegrityError as e:
        db.session.rollback()
        # Резервная обработка IntegrityError
        error_msg = str(e).lower()
        if 'email' in error_msg:
            return jsonify({'error': 'Email already exists'}), 400
        elif 'username' in error_msg:
            return jsonify({'error': 'Username already exists'}), 400
        else:
            return jsonify({'error': 'User already exists'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/logout')
def logout():
    """Выход из системы"""
    return redirect(url_for('auth.login_page'))