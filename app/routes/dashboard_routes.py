from flask import Blueprint, render_template, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Transaction, Category, User
from app import db
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# Главная панель (рендеринг)
@dashboard_bp.route('/')
def dashboard_home():
    """Страница Dashboard"""
    return render_template('dashboard.html')

# Страница транзакций
@dashboard_bp.route('/transactions')
def transactions_page():
    """Страница управления транзакциями"""
    return render_template('transactions.html')

# Страница статистики
@dashboard_bp.route('/stats')
def stats_page():
    """Страница статистики"""
    return render_template('stats.html')

# API: получить данные для Dashboard
@dashboard_bp.route('/data')
@jwt_required()
def dashboard_data():
    user_id = get_jwt_identity()
    
    # Расчет баланса
    income_sum = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id, 
        Transaction.type == 'income'
    ).scalar() or 0
    
    expense_sum = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id, 
        Transaction.type == 'expense'
    ).scalar() or 0
    
    balance = income_sum - expense_sum
    
    # Получение транзакций
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.date.desc()).all()
    categories = Category.query.filter_by(user_id=user_id).all()

    transactions_list = [
        {
            'id': t.id,
            'amount': t.amount,
            'type': t.type,
            'category': t.category.name if t.category else None,
            'description': t.description,
            'date': t.date.strftime('%Y-%m-%d %H:%M')
        }
        for t in transactions
    ]

    categories_list = [
        {'id': c.id, 'name': c.name} for c in categories
    ]

    return jsonify({
        'balance': balance,
        'transactions': transactions_list,
        'categories': categories_list
    })

# API: добавить транзакцию
@dashboard_bp.route('/add_transaction', methods=['POST'])
@jwt_required()
def add_transaction():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Валидация данных
    if not data.get('amount') or float(data['amount']) <= 0:
        return jsonify({'error': 'Неверная сумма'}), 400
    
    transaction = Transaction(
        amount=float(data['amount']),
        type=data['type'],
        category_id=data.get('category_id'),
        description=data.get('description', ''),
        user_id=user_id
    )
    db.session.add(transaction)
    db.session.commit()
    return jsonify({'message': 'Транзакция добавлена успешно'})

# API: редактировать транзакцию
@dashboard_bp.route('/edit_transaction/<int:id>', methods=['PUT'])
@jwt_required()
def edit_transaction(id):
    user_id = get_jwt_identity()
    transaction = Transaction.query.filter_by(id=id, user_id=user_id).first_or_404()
    data = request.get_json()
    
    if 'amount' in data and float(data['amount']) <= 0:
        return jsonify({'error': 'Неверная сумма'}), 400
        
    transaction.amount = float(data.get('amount', transaction.amount))
    transaction.type = data.get('type', transaction.type)
    transaction.category_id = data.get('category_id', transaction.category_id)
    transaction.description = data.get('description', transaction.description)
    db.session.commit()
    return jsonify({'message': 'Транзакция обновлена успешно'})

# API: удалить транзакцию
@dashboard_bp.route('/delete_transaction/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_transaction(id):
    user_id = get_jwt_identity()
    transaction = Transaction.query.filter_by(id=id, user_id=user_id).first_or_404()
    db.session.delete(transaction)
    db.session.commit()
    return jsonify({'message': 'Транзакция удалена успешно'})

# API: добавить категорию
@dashboard_bp.route('/add_category', methods=['POST'])
@jwt_required()
def add_category():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('name') or len(data['name'].strip()) == 0:
        return jsonify({'error': 'Название категории не может быть пустым'}), 400
        
    # Проверка на уникальность категории
    existing_category = Category.query.filter_by(name=data['name'].strip(), user_id=user_id).first()
    if existing_category:
        return jsonify({'error': 'Категория с таким названием уже существует'}), 400
        
    category = Category(name=data['name'].strip(), user_id=user_id)
    db.session.add(category)
    db.session.commit()
    return jsonify({'message': 'Категория добавлена успешно', 'id': category.id})

# API: удалить категорию
@dashboard_bp.route('/delete_category/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_category(id):
    user_id = get_jwt_identity()
    category = Category.query.filter_by(id=id, user_id=user_id).first_or_404()
    
    # Проверяем, есть ли транзакции с этой категорией
    transactions_count = Transaction.query.filter_by(category_id=id, user_id=user_id).count()
    if transactions_count > 0:
        return jsonify({'error': 'Нельзя удалить категорию, с которой связаны транзакции'}), 400
        
    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Категория удалена успешно'})

# API: статистика по категориям
@dashboard_bp.route('/stats_data')
@jwt_required()
def dashboard_stats():
    user_id = get_jwt_identity()
    categories = Category.query.filter_by(user_id=user_id).all()
    
    labels = [c.name for c in categories]
    income = []
    expense = []
    
    for category in categories:
        category_income = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id, 
            Transaction.category_id == category.id, 
            Transaction.type == 'income'
        ).scalar() or 0
        
        category_expense = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id, 
            Transaction.category_id == category.id, 
            Transaction.type == 'expense'
        ).scalar() or 0
        
        income.append(float(category_income))
        expense.append(float(category_expense))
    
    return jsonify({
        'labels': labels, 
        'income': income, 
        'expense': expense
    })

# API: детали пользователя
@dashboard_bp.route('/profile')
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email
    })
