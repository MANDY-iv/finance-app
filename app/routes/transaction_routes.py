from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Transaction

transaction_bp = Blueprint('transactions', __name__, url_prefix='/transactions')

@transaction_bp.route('/', methods=['POST'])
@jwt_required()
def add_transaction():
    user_id = get_jwt_identity()
    data = request.get_json()
    transaction = Transaction(
        amount=data['amount'],
        type=data['type'],
        category_id=data.get('category_id'),
        description=data.get('description'),
        user_id=user_id
    )
    db.session.add(transaction)
    db.session.commit()
    return jsonify({'message': 'Transaction added'}), 201
