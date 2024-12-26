# app/templates/api/v1/endpoints.py
from flask import Blueprint, request, jsonify

api_v1 = Blueprint('api_v1', __name__)

@api_v1.route('/initiate', methods=['GET'])
def init_convo():
    # Your existing initiate endpoint code
    user_id = request.args.get('user_id', None)
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    # Rest of your existing code
    pass