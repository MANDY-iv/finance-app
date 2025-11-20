import pytest
from app import db
from app.models import Transaction, Category, User

class TestDashboardAndStats:
    """Тесты дашборда и статистики - TC-STATS-001 до TC-STATS-002"""
    
    def test_TC_STATS_001_get_dashboard_data(self, client, app, auth_token, auth_headers):
        """TC-STATS-001: Получение данных для дашборда"""
        # Создаем тестовые данные
        with app.app_context():
            user = db.session.query(User).filter_by(email='test@example.com').first()
            user_id = user.id
            
            category = Category(name='Test Category', user_id=user_id)
            db.session.add(category)
            db.session.commit()
            
            transaction = Transaction(
                amount=100.0, 
                type='income', 
                category_id=category.id, 
                user_id=user_id,
                description='Test transaction'
            )
            db.session.add(transaction)
            db.session.commit()
        
        headers = auth_headers(auth_token)
        response = client.get('/dashboard/data', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Проверяем структуру ответа
        assert 'balance' in data
        assert 'transactions' in data
        assert 'categories' in data
        
        # Проверяем баланс
        assert data['balance'] == 100.0
        
        # Проверяем что есть транзакции и категории
        assert len(data['transactions']) >= 1
        assert len(data['categories']) >= 1
    
    def test_TC_STATS_002_get_category_stats(self, client, app, auth_token, auth_headers):
        """TC-STATS-002: Получение статистики по категориям"""
        # Создаем тестовые данные
        with app.app_context():
            user = db.session.query(User).filter_by(email='test@example.com').first()
            user_id = user.id
            
            category = Category(name='Test Category', user_id=user_id)
            db.session.add(category)
            db.session.commit()
            
            transaction = Transaction(
                amount=100.0, 
                type='income', 
                category_id=category.id, 
                user_id=user_id
            )
            db.session.add(transaction)
            db.session.commit()
        
        headers = auth_headers(auth_token)
        response = client.get('/dashboard/stats_data', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Проверяем структуру ответа
        assert 'labels' in data
        assert 'income' in data
        assert 'expense' in data
        
        # Проверяем что данные есть
        assert len(data['labels']) >= 1
        assert len(data['income']) >= 1
        assert len(data['expense']) >= 1