import pytest
from app import db
from app.models import Transaction, Category, User

class TestTransactions:
    """Тесты управления транзакциями - TC-TRANS-001 до TC-TRANS-004"""
    
    def test_TC_TRANS_001_create_transaction_valid(self, client, app, auth_token, auth_headers):
        """TC-TRANS-001: Создание транзакции с валидными данными"""
        # Создаем категорию
        with app.app_context():
            user = db.session.query(User).filter_by(email='test@example.com').first()
            user_id = user.id
            
            category = Category(name='Test Category', user_id=user_id)
            db.session.add(category)
            db.session.commit()
            category_id = category.id
        
        headers = auth_headers(auth_token)
        response = client.post('/dashboard/add_transaction',
                             json={
                                 'amount': 100.0, 
                                 'type': 'income', 
                                 'category_id': category_id, 
                                 'description': 'Test transaction'
                             },
                             headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Транзакция добавлена успешно'
        
        # Проверяем создание в БД
        with app.app_context():
            transaction = db.session.query(Transaction).filter_by(description='Test transaction').first()
            assert transaction is not None
            assert transaction.amount == 100.0
            assert transaction.type == 'income'
            assert transaction.category_id == category_id
    
    def test_TC_TRANS_002_create_transaction_invalid_amount(self, client, auth_token, auth_headers):
        """TC-TRANS-002: Создание транзакции с невалидной суммой"""
        headers = auth_headers(auth_token)
        response = client.post('/dashboard/add_transaction',
                             json={
                                 'amount': -50.0, 
                                 'type': 'income'
                             },
                             headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'Неверная сумма'
    
    def test_TC_TRANS_003_get_transactions_list(self, client, app, auth_token, auth_headers):
        """TC-TRANS-003: Получение списка транзакций"""
        # Создаем тестовую транзакцию
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
        assert 'transactions' in data
        assert 'balance' in data
        assert 'categories' in data
        assert len(data['transactions']) >= 1
        # Проверяем что есть наша транзакция
        test_transactions = [t for t in data['transactions'] if t['description'] == 'Test transaction']
        assert len(test_transactions) == 1
        assert test_transactions[0]['amount'] == 100.0
        assert test_transactions[0]['type'] == 'income'
    
    def test_TC_TRANS_004_delete_transaction(self, client, app, auth_token, auth_headers):
        """TC-TRANS-004: Удаление транзакции"""
        # Создаем тестовую транзакцию
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
                description='Transaction to delete'
            )
            db.session.add(transaction)
            db.session.commit()
            transaction_id = transaction.id
        
        headers = auth_headers(auth_token)
        response = client.delete(f'/dashboard/delete_transaction/{transaction_id}', 
                               headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Транзакция удалена успешно'
        
        # Проверяем удаление из БД (используем современный метод)
        with app.app_context():
            transaction = db.session.get(Transaction, transaction_id)
            assert transaction is None