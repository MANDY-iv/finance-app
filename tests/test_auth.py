import pytest
from app import db, bcrypt
from app.models import User

class TestAuthentication:
    """Тесты аутентификации - TC-AUTH-001 до TC-AUTH-004"""
    
    def test_TC_AUTH_001_register_valid_user(self, client, app):
        """TC-AUTH-001: Регистрация нового пользователя с валидными данными"""
        response = client.post('/auth/register', 
                             json={
                                 'username': 'newuser', 
                                 'email': 'new@example.com', 
                                 'password': 'password123'
                             })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'User registered successfully'
        
        # Проверяем, что пользователь создан в БД
        with app.app_context():
            user = db.session.query(User).filter_by(email='new@example.com').first()
            assert user is not None
            assert user.username == 'newuser'
            # Проверяем хеширование пароля
            assert bcrypt.check_password_hash(user.password, 'password123')
    
    def test_TC_AUTH_002_register_existing_email(self, client, app):
        """TC-AUTH-002: Регистрация пользователя с существующим email"""
        # Сначала создаем пользователя через API
        response1 = client.post('/auth/register',
                              json={
                                  'username': 'admin',
                                  'email': 'admin@example.com',
                                  'password': 'password123'
                              })
        assert response1.status_code == 201
    
        # Пытаемся создать пользователя с тем же email
        response2 = client.post('/auth/register',
                              json={
                                  'username': 'newuser',
                                  'email': 'admin@example.com',
                                  'password': 'password123'
                              })
        
        # Теперь ожидаем ошибку 400
        assert response2.status_code == 400
        data = response2.get_json()
        assert data['error'] == 'Email already exists'
        
        # Проверяем, что второй пользователь не создался
        with app.app_context():
            users_with_email = db.session.query(User).filter_by(email='admin@example.com').count()
            assert users_with_email == 1  # Должен быть только один пользователь с этим email
    
    def test_TC_AUTH_003_login_valid_credentials(self, client, app):
        """TC-AUTH-003: Авторизация с корректными учетными данными"""
        # Создаем пользователя
        with app.app_context():
            hashed_pw = bcrypt.generate_password_hash('password123').decode('utf-8')
            user = User(username='testuser', email='user@example.com', password=hashed_pw)
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/auth/login',
                             json={
                                 'email': 'user@example.com', 
                                 'password': 'password123'
                             })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'token' in data
        assert isinstance(data['token'], str)
        assert len(data['token']) > 0
    
    def test_TC_AUTH_004_login_invalid_password(self, client, app):
        """TC-AUTH-004: Авторизация с неверным паролем"""
        # Создаем пользователя
        with app.app_context():
            hashed_pw = bcrypt.generate_password_hash('correctpassword').decode('utf-8')
            user = User(username='testuser', email='user@example.com', password=hashed_pw)
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/auth/login',
                             json={
                                 'email': 'user@example.com', 
                                 'password': 'wrongpassword'
                             })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Invalid credentials'
    
    def test_TC_AUTH_005_register_missing_fields(self, client):
        """TC-AUTH-005: Регистрация с отсутствующими обязательными полями"""
        # Тест без username
        response = client.post('/auth/register',
                             json={
                                 'email': 'test@example.com',
                                 'password': 'password123'
                             })
        assert response.status_code == 400
        
        # Тест без email
        response = client.post('/auth/register',
                             json={
                                 'username': 'testuser',
                                 'password': 'password123'
                             })
        assert response.status_code == 400
        
        # Тест без password
        response = client.post('/auth/register',
                             json={
                                 'username': 'testuser',
                                 'email': 'test@example.com'
                             })
        assert response.status_code == 400
    
    def test_TC_AUTH_006_register_short_password(self, client):
        """TC-AUTH-006: Регистрация с коротким паролем"""
        response = client.post('/auth/register',
                             json={
                                 'username': 'testuser',
                                 'email': 'test@example.com',
                                 'password': '123'
                             })
        assert response.status_code == 400
        data = response.get_json()
        assert 'Password must be at least 6 characters' in data['error']