from flask import Blueprint, jsonify, request
import pymysql

from config import MYSQL_CONFIG

def get_db_connection():
    return pymysql.connect(**MYSQL_CONFIG)

# Create a Blueprint for the API
api = Blueprint('api', __name__)

@api.route('/api/patterns', methods=['GET', 'POST'])
def manage_patterns():
    connection = get_db_connection()
    with connection.cursor() as cursor:
        if request.method == 'GET':
            cursor.execute("SELECT pattern, division FROM patterns_table")
            patterns_divisions = cursor.fetchall()
            return jsonify([{'pattern': pd[0], 'division': pd[1]} for pd in patterns_divisions])
        
        elif request.method == 'POST':
            new_pattern = request.json['pattern']
            new_division = request.json['division']
            cursor.execute("INSERT INTO patterns_table (pattern, division) VALUES (%s, %s)", (new_pattern, new_division))
            connection.commit()
            return jsonify({'message': 'Pattern added!'}), 201

@api.route('/api/patterns/<string:pattern>', methods=['PUT', 'DELETE'])
def update_delete_pattern(pattern):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        if request.method == 'PUT':
            new_division = request.json['division']
            cursor.execute("UPDATE patterns_table SET division = %s WHERE pattern = %s", (new_division, pattern))
            connection.commit()
            return jsonify({'message': 'Pattern updated!'})

        elif request.method == 'DELETE':
            cursor.execute("DELETE FROM patterns_table WHERE pattern = %s", (pattern,))
            connection.commit()
            return jsonify({'message': 'Pattern deleted!'})
