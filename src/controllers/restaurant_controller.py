from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime

from ..config.database import db
from ..middleware.auth import token_required
from ..models.restaurant import Restaurant

restaurant = Blueprint('restaurant', __name__)

@restaurant.route('/<restaurant_id>/like', methods=['POST'])
@token_required
def toggle_like(current_user, restaurant_id):
    try:
        user_id = current_user['_id']
        
        # Check if user has already liked the restaurant
        like = db.restaurant_likes.find_one({
            'user_id': user_id,
            'restaurant_id': ObjectId(restaurant_id)
        })
        
        if like:
            # Unlike
            db.restaurant_likes.delete_one({'_id': like['_id']})
            is_liked = False
        else:
            # Like
            db.restaurant_likes.insert_one({
                'user_id': user_id,
                'restaurant_id': ObjectId(restaurant_id),
                'created_at': datetime.utcnow()
            })
            is_liked = True
            
        return jsonify({'isLiked': is_liked}), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@restaurant.route('/<restaurant_id>/rate', methods=['POST'])
@token_required
def rate_restaurant(current_user, restaurant_id):
    try:
        data = request.get_json()
        user_id = current_user['_id']
        
        # Validate rating
        rating = float(data['rating'])
        if not 1 <= rating <= 5:
            return jsonify({'message': 'Rating must be between 1 and 5'}), 400
            
        # Check if user has already rated
        existing_rating = db.restaurant_ratings.find_one({
            'user_id': user_id,
            'restaurant_id': ObjectId(restaurant_id)
        })
        
        if existing_rating:
            # Update existing rating
            db.restaurant_ratings.update_one(
                {'_id': existing_rating['_id']},
                {
                    '$set': {
                        'rating': rating,
                        'comment': data.get('comment'),
                        'updated_at': datetime.utcnow()
                    }
                }
            )
        else:
            # Create new rating
            db.restaurant_ratings.insert_one({
                'user_id': user_id,
                'restaurant_id': ObjectId(restaurant_id),
                'rating': rating,
                'comment': data.get('comment'),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
            
        # Update restaurant average rating
        ratings = list(db.restaurant_ratings.find({'restaurant_id': ObjectId(restaurant_id)}))
        avg_rating = sum(r['rating'] for r in ratings) / len(ratings)
        
        db.restaurants.update_one(
            {'_id': ObjectId(restaurant_id)},
            {'$set': {'rating': round(avg_rating, 1)}}
        )
        
        return jsonify({'message': 'Rating submitted successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@restaurant.route('/liked', methods=['GET'])
@token_required
def get_liked_restaurants(current_user):
    try:
        # Get user's liked restaurant IDs
        likes = db.restaurant_likes.find({'user_id': current_user['_id']})
        restaurant_ids = [like['restaurant_id'] for like in likes]
        
        # Get restaurant details
        restaurants = list(db.restaurants.find({'_id': {'$in': restaurant_ids}}))
        
        # Format response
        response = []
        for restaurant in restaurants:
            restaurant['id'] = str(restaurant['_id'])
            del restaurant['_id']
            restaurant['isLiked'] = True
            response.append(restaurant)
            
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@restaurant.route('/<restaurant_id>/ratings', methods=['GET'])
def get_restaurant_ratings(restaurant_id):
    try:
        # Get all ratings for the restaurant
        ratings = list(db.restaurant_ratings.aggregate([
            {'$match': {'restaurant_id': ObjectId(restaurant_id)}},
            {'$lookup': {
                'from': 'users',
                'localField': 'user_id',
                'foreignField': '_id',
                'as': 'user'
            }},
            {'$unwind': '$user'},
            {'$project': {
                'rating': 1,
                'comment': 1,
                'created_at': 1,
                'user': {
                    'firstName': '$user.first_name',
                    'lastName': '$user.last_name'
                }
            }}
        ]))
        
        # Calculate average rating
        if ratings:
            average = sum(r['rating'] for r in ratings) / len(ratings)
        else:
            average = 0
            
        return jsonify({
            'average': round(average, 1),
            'total': len(ratings),
            'ratings': ratings
        }), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@restaurant.route('/ratings', methods=['GET'])
@token_required
def get_user_ratings(current_user):
    try:
        # Get user's ratings with restaurant details
        ratings = list(db.restaurant_ratings.aggregate([
            {'$match': {'user_id': current_user['_id']}},
            {'$lookup': {
                'from': 'restaurants',
                'localField': 'restaurant_id',
                'foreignField': '_id',
                'as': 'restaurant'
            }},
            {'$unwind': '$restaurant'},
            {'$project': {
                'rating': 1,
                'restaurant': {
                    'id': {'$toString': '$restaurant._id'},
                    'name': '$restaurant.name',
                    'imageUrl': '$restaurant.image_url',
                    'cuisineType': '$restaurant.cuisine_types'
                }
            }}
        ]))
        
        return jsonify(ratings), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 400