import pytest
import os
import tempfile
from app import create_app, db, bcrypt
from app.models import User, Category, Transaction

@pytest.fixture(scope='function')
def app():
    """Создание приложения для тестирования"""
    # Создаем временную базу данных
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app()
    
    # Конфигурация для тестирования
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['JWT_SECRET_KEY'] = 'test-jwt-secret-key'
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Тестовый клиент"""
    return app.test_client()

@pytest.fixture
def auth_token(client, app):
    """Получение JWT токена"""
    # Создаем пользователя для аутентификации через API
    response = client.post('/auth/register', 
                         json={
                             'username': 'testuser', 
                             'email': 'test@example.com', 
                             'password': 'password123'
                         })
    
    # Логинимся чтобы получить токен
    response = client.post('/auth/login', 
                         json={'email': 'test@example.com', 'password': 'password123'})
    data = response.get_json()
    return data.get('token') if data else None

@pytest.fixture
def auth_headers(auth_token):
    """Создание заголовков авторизации"""
    def _auth_headers(token=None):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        return headers
    return _auth_headers