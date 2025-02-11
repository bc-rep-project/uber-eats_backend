from flask import Blueprint, request, jsonify
from middleware.auth_middleware import token_required, admin_required
from models.tax_rule import TaxRule
from config.database import db
from bson import ObjectId
from datetime import datetime

restaurant_settings = Blueprint('restaurant_settings', __name__)

@restaurant_settings.route('/api/restaurant/settings/tax-rules', methods=['GET'])
@token_required
def get_tax_rules(current_user):
    """Get all tax rules for a restaurant"""
    try:
        restaurant_id = request.args.get('restaurant_id')
        if not restaurant_id:
            return jsonify({'error': 'Restaurant ID is required'}), 400

        tax_rules = list(db.get_db().tax_rules.find({'restaurant_id': restaurant_id}))
        return jsonify([{**rule, '_id': str(rule['_id'])} for rule in tax_rules])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@restaurant_settings.route('/api/restaurant/settings/tax-rules', methods=['POST'])
@token_required
def create_tax_rule(current_user):
    """Create a new tax rule"""
    try:
        data = request.json
        restaurant_id = data.get('restaurant_id')
        if not restaurant_id:
            return jsonify({'error': 'Restaurant ID is required'}), 400

        tax_rule = TaxRule(
            restaurant_id=restaurant_id,
            name=data['name'],
            description=data.get('description'),
            rate=data['rate'],
            is_active=data.get('isActive', True),
            applies_to_delivery=data.get('appliesToDelivery', True),
            applies_to_pickup=data.get('appliesToPickup', True),
            minimum_order_amount=data.get('minimumOrderAmount', 0.0)
        )

        result = db.get_db().tax_rules.insert_one(tax_rule.dict(by_alias=True))
        tax_rule.id = str(result.inserted_id)
        
        return jsonify(tax_rule.dict(by_alias=True)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@restaurant_settings.route('/api/restaurant/settings/tax-rules/<rule_id>', methods=['PUT'])
@token_required
def update_tax_rule(current_user, rule_id):
    """Update an existing tax rule"""
    try:
        data = request.json
        restaurant_id = data.get('restaurant_id')
        if not restaurant_id:
            return jsonify({'error': 'Restaurant ID is required'}), 400

        # Verify ownership
        existing_rule = db.get_db().tax_rules.find_one({
            '_id': ObjectId(rule_id),
            'restaurant_id': restaurant_id
        })
        if not existing_rule:
            return jsonify({'error': 'Tax rule not found'}), 404

        update_data = {
            'name': data['name'],
            'description': data.get('description'),
            'rate': data['rate'],
            'is_active': data.get('isActive', True),
            'applies_to_delivery': data.get('appliesToDelivery', True),
            'applies_to_pickup': data.get('appliesToPickup', True),
            'minimum_order_amount': data.get('minimumOrderAmount', 0.0),
            'updated_at': datetime.utcnow()
        }

        db.get_db().tax_rules.update_one(
            {'_id': ObjectId(rule_id)},
            {'$set': update_data}
        )

        updated_rule = db.get_db().tax_rules.find_one({'_id': ObjectId(rule_id)})
        return jsonify({**updated_rule, '_id': str(updated_rule['_id'])})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@restaurant_settings.route('/api/restaurant/settings/tax-rules/<rule_id>', methods=['DELETE'])
@token_required
def delete_tax_rule(current_user, rule_id):
    """Delete a tax rule"""
    try:
        restaurant_id = request.args.get('restaurant_id')
        if not restaurant_id:
            return jsonify({'error': 'Restaurant ID is required'}), 400

        # Verify ownership
        existing_rule = db.get_db().tax_rules.find_one({
            '_id': ObjectId(rule_id),
            'restaurant_id': restaurant_id
        })
        if not existing_rule:
            return jsonify({'error': 'Tax rule not found'}), 404

        db.get_db().tax_rules.delete_one({'_id': ObjectId(rule_id)})
        return jsonify({'message': 'Tax rule deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500 