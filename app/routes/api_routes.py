from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Transaction, Category
from app import db

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Categories
@api_bp.route('/categories', methods=['POST'])
@jwt_required()
def add_category():
    user_id = get_jwt_identity()
    data = request.get_json()
    category = Category(name=data['name'], user_id=user_id)
    db.session.add(category)
    db.session.commit()
    return jsonify({'message':'Category added', 'id':category.id})

@api_bp.route('/categories/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_category(id):
    user_id = get_jwt_identity()
    category = Category.query.filter_by(id=id, user_id=user_id).first_or_404()
    db.session.delete(category)
    db.session.commit()
    return jsonify({'message':'Category deleted'})
