import pytest
from app import db
from app.models import Category, Transaction, User

class TestCategories:
    """Тесты управления категориями - TC-CAT-001 до TC-CAT-005"""
    
    def test_TC_CAT_001_create_category_valid(self, client, auth_token, auth_headers):
        """TC-CAT-001: Создание категории с валидным названием"""
        headers = auth_headers(auth_token)
        response = client.post('/dashboard/add_category',
                             json={'name': 'Food'},
                             headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Категория добавлена успешно'
        assert 'id' in data
    
    def test_TC_CAT_002_create_category_empty_name(self, client, auth_token, auth_headers):
        """TC-CAT-002: Создание категории с пустым названием"""
        headers = auth_headers(auth_token)
        response = client.post('/dashboard/add_category',
                             json={'name': ''},
                             headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Название категории не может быть пустым'
    
    def test_TC_CAT_003_create_category_duplicate_name(self, client, app, auth_token, auth_headers):
        """TC-CAT-003: Создание категории с существующим названием"""
        # Сначала создаем категорию
        with app.app_context():
            user = db.session.query(User).filter_by(email='test@example.com').first()
            user_id = user.id
            
            category = Category(name='Food', user_id=user_id)
            db.session.add(category)
            db.session.commit()
        
        # Пытаемся создать категорию с тем же названием
        headers = auth_headers(auth_token)
        response = client.post('/dashboard/add_category',
                             json={'name': 'Food'},
                             headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Категория с таким названием уже существует'
    
    def test_TC_CAT_004_delete_category_no_transactions(self, client, app, auth_token, auth_headers):
        """TC-CAT-004: Удаление категории без транзакций"""
        # Создаем категорию без транзакций
        with app.app_context():
            user = db.session.query(User).filter_by(email='test@example.com').first()
            user_id = user.id
            
            category = Category(name='Temp Category', user_id=user_id)
            db.session.add(category)
            db.session.commit()
            category_id = category.id
        
        headers = auth_headers(auth_token)
        response = client.delete(f'/dashboard/delete_category/{category_id}', 
                               headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Категория удалена успешно'
    
    def test_TC_CAT_005_delete_category_with_transactions(self, client, app, auth_token, auth_headers):
        """TC-CAT-005: Удаление категории с транзакциями"""
        # Создаем категорию с транзакцией
        with app.app_context():
            user = db.session.query(User).filter_by(email='test@example.com').first()
            user_id = user.id
            
            category = Category(name='Category with transactions', user_id=user_id)
            db.session.add(category)
            db.session.commit()
            
            transaction = Transaction(
                amount=50.0, 
                type='expense', 
                category_id=category.id, 
                user_id=user_id
            )
            db.session.add(transaction)
            db.session.commit()
            category_id = category.id
        
        headers = auth_headers(auth_token)
        response = client.delete(f'/dashboard/delete_category/{category_id}', 
                               headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Нельзя удалить категорию, с которой связаны транзакции'
        
        # Проверяем что категория не удалена из БД
        with app.app_context():
            category = db.session.get(Category, category_id)
            assert category is not None