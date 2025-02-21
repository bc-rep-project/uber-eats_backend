from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime

from src.config.database import db
from src.middleware.auth import token_required
from src.models.grocery_store import GroceryStore, GroceryProduct, GroceryCategory

grocery = Blueprint('grocery', __name__)

@grocery.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = list(db.grocery_categories.find().sort('order', 1))
        for category in categories:
            category['id'] = str(category['_id'])
            del category['_id']
        return jsonify(categories), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@grocery.route('/stores', methods=['GET'])
def get_stores():
    try:
        # Get query parameters
        category = request.args.get('category')
        featured = request.args.get('featured', '').lower() == 'true'
        search = request.args.get('search')
        
        # Build query
        query = {}
        if category:
            query['categories'] = category
        if featured:
            query['is_featured'] = True
        if search:
            query['$or'] = [
                {'name': {'$regex': search, '$options': 'i'}},
                {'description': {'$regex': search, '$options': 'i'}}
            ]
            
        # Get stores
        stores = list(db.grocery_stores.find(query))
        
        # Format response
        for store in stores:
            store['id'] = str(store['_id'])
            del store['_id']
            
        return jsonify(stores), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@grocery.route('/stores/<store_id>', methods=['GET'])
def get_store(store_id):
    try:
        store = db.grocery_stores.find_one({'_id': ObjectId(store_id)})
        if not store:
            return jsonify({'message': 'Store not found'}), 404
            
        store['id'] = str(store['_id'])
        del store['_id']
        
        return jsonify(store), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@grocery.route('/stores/<store_id>/products', methods=['GET'])
def get_store_products():
    try:
        # Get query parameters
        category = request.args.get('category')
        search = request.args.get('search')
        
        # Build query
        query = {'store_id': store_id}
        if category:
            query['category'] = category
        if search:
            query['$or'] = [
                {'name': {'$regex': search, '$options': 'i'}},
                {'description': {'$regex': search, '$options': 'i'}}
            ]
            
        # Get products
        products = list(db.grocery_products.find(query))
        
        # Format response
        for product in products:
            product['id'] = str(product['_id'])
            del product['_id']
            
        return jsonify(products), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@grocery.route('/stores/<store_id>/rate', methods=['POST'])
@token_required
def rate_store(current_user, store_id):
    try:
        data = request.get_json()
        rating = float(data['rating'])
        
        if not 1 <= rating <= 5:
            return jsonify({'message': 'Rating must be between 1 and 5'}), 400
            
        # Add/update rating
        db.grocery_ratings.update_one(
            {
                'user_id': current_user['_id'],
                'store_id': ObjectId(store_id)
            },
            {
                '$set': {
                    'rating': rating,
                    'updated_at': datetime.utcnow()
                }
            },
            upsert=True
        )
        
        # Update store rating
        ratings = list(db.grocery_ratings.find({'store_id': ObjectId(store_id)}))
        avg_rating = sum(r['rating'] for r in ratings) / len(ratings)
        
        db.grocery_stores.update_one(
            {'_id': ObjectId(store_id)},
            {
                '$set': {
                    'rating': round(avg_rating, 1),
                    'total_ratings': len(ratings)
                }
            }
        )
        
        return jsonify({'message': 'Rating submitted successfully'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400 