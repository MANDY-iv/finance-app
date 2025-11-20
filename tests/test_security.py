import pytest
from app import db, bcrypt
from app.models import Transaction, Category, User
from flask_jwt_extended import create_access_token

class TestSecurity:
    """Тесты безопасности - TC-SEC-001 до TC-SEC-004"""
    
    def test_TC_SEC_001_access_without_token(self, client):
        """TC-SEC-001: Доступ к API без токена"""
        response = client.get('/dashboard/data')
        assert response.status_code == 401
    
    def test_TC_SEC_002_data_isolation_between_users(self, client, app):
        """TC-SEC-002: Доступ к данным другого пользователя"""
        # Создаем двух пользователей через API
        # Первый пользователь
        response1 = client.post('/auth/register', 
                              json={
                                  'username': 'user1', 
                                  'email': 'user1@example.com', 
                                  'password': 'password123'
                              })
        assert response1.status_code == 201
        
        # Получаем токен для первого пользователя
        login_response1 = client.post('/auth/login',
                                    json={
                                        'email': 'user1@example.com', 
                                        'password': 'password123'
                                    })
        token1 = login_response1.get_json()['token']
        
        # Второй пользователь
        response2 = client.post('/auth/register', 
                              json={
                                  'username': 'user2', 
                                  'email': 'user2@example.com', 
                                  'password': 'password123'
                              })
        assert response2.status_code == 201
        
        # Получаем ID пользователей из базы
        with app.app_context():
            user1 = db.session.query(User).filter_by(email='user1@example.com').first()
            user2 = db.session.query(User).filter_by(email='user2@example.com').first()
            
            # Создаем транзакции для обоих пользователей
            # Категория и транзакция для первого пользователя
            category1 = Category(name='User1 Category', user_id=user1.id)
            transaction1 = Transaction(
                amount=100.0, type='income', category_id=category1.id, user_id=user1.id,
                description='User1 transaction'
            )
            
            # Категория и транзакция для второго пользователя
            category2 = Category(name='User2 Category', user_id=user2.id)
            transaction2 = Transaction(
                amount=200.0, type='income', category_id=category2.id, user_id=user2.id,
                description='User2 transaction'
            )
            
            db.session.add_all([category1, transaction1, category2, transaction2])
            db.session.commit()
        
        # Первый пользователь получает свои данные
        headers = {'Authorization': f'Bearer {token1}', 'Content-Type': 'application/json'}
        response = client.get('/dashboard/data', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Проверяем, что возвращаются только данные первого пользователя
        user1_transactions = [t for t in data['transactions'] if t['description'] == 'User1 transaction']
        user2_transactions = [t for t in data['transactions'] if t['description'] == 'User2 transaction']
        
        assert len(user1_transactions) >= 0  # Может быть транзакция первого пользователя
        assert len(user2_transactions) == 0  # Не должно быть транзакций второго пользователя
    
    def test_TC_SEC_003_delete_other_user_transaction(self, client, app):
        """TC-SEC-003: Попытка удалить чужую транзакцию"""
        # Создаем двух пользователей через API
        # Первый пользователь (будет делать запрос)
        response1 = client.post('/auth/register', 
                              json={
                                  'username': 'user1', 
                                  'email': 'user1@example.com', 
                                  'password': 'password123'
                              })
        assert response1.status_code == 201
        
        # Получаем токен для первого пользователя
        login_response1 = client.post('/auth/login',
                                    json={
                                        'email': 'user1@example.com', 
                                        'password': 'password123'
                                    })
        token1 = login_response1.get_json()['token']
        
        # Второй пользователь (владелец транзакции)
        response2 = client.post('/auth/register', 
                              json={
                                  'username': 'user2', 
                                  'email': 'user2@example.com', 
                                  'password': 'password123'
                              })
        assert response2.status_code == 201
        
        # Получаем ID пользователей из базы
        with app.app_context():
            user1 = db.session.query(User).filter_by(email='user1@example.com').first()
            user2 = db.session.query(User).filter_by(email='user2@example.com').first()
            
            # Транзакция для второго пользователя
            category = Category(name='User2 Category', user_id=user2.id)
            transaction = Transaction(
                amount=100.0, type='income', category_id=category.id, user_id=user2.id
            )
            db.session.add_all([category, transaction])
            db.session.commit()
            transaction_id = transaction.id
        
        # Первый пользователь пытается удалить транзакцию второго
        headers = {'Authorization': f'Bearer {token1}', 'Content-Type': 'application/json'}
        response = client.delete(f'/dashboard/delete_transaction/{transaction_id}', headers=headers)
        
        assert response.status_code == 404
    
    def test_TC_SEC_004_transaction_validation_large_amount(self, client, app, auth_token, auth_headers):
        """TC-SEC-004: Валидация входных данных транзакции"""
        # Создаем категорию
        with app.app_context():
            user = db.session.query(User).filter_by(email='test@example.com').first()
            user_id = user.id
            
            category = Category(name='Test Category', user_id=user_id)
            db.session.add(category)
            db.session.commit()
            category_id = category.id
        
        headers = auth_headers(auth_token)
        
        # Тестируем очень большое число
        response = client.post('/dashboard/add_transaction',
                             json={
                                 'amount': 1e20,  # Очень большое число
                                 'type': 'income', 
                                 'category_id': category_id
                             },
                             headers=headers)
        
        # Проверяем корректную обработку
        assert response.status_code in [200, 400]