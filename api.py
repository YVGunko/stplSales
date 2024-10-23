from flask import Blueprint, jsonify, request
import pymysql
import pandas as pd

from config import MYSQL_CONFIG

def get_db_connection():
    return pymysql.connect(**MYSQL_CONFIG)

# Create a Blueprint for the API
api = Blueprint('api', __name__)

@api.route('/api/save', methods=['POST'])
def save_data():
    # Assuming you want to save data from a specific DataFrame or received data
    data_to_save = request.json  # Or request.form depending on your needs

    # Connect to the database and insert the data
    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        with connection.cursor() as cursor:
            # Example of how to save the data (adjust according to your data structure)
            for entry in data_to_save:
                # Assuming entry is a dictionary with the required fields
                cursor.execute("INSERT INTO your_table_name (column1, column2) VALUES (%s, %s)",
                               (entry['field1'], entry['field2']))  # Adjust as necessary

            connection.commit()
        return jsonify({"status": "success", "message": "Data saved successfully."})
    except pymysql.MySQLError as e:
        return jsonify({"status": "error", "message": str(e)})
    finally:
        connection.close()

@api.route('/api/patterns', methods=['GET', 'POST'])
def manage_patterns():
    connection = get_db_connection()
    with connection.cursor() as cursor:
        if request.method == 'GET':
            cursor.execute("SELECT pattern, code FROM division_patterns")
            division_patterns = cursor.fetchall()
            return jsonify([{'pattern': pd[0], 'code': pd[1]} for pd in division_patterns])
        
        elif request.method == 'POST':
            new_pattern = request.json['pattern']
            new_division = request.json['code']
            cursor.execute("INSERT INTO division_patterns (pattern, code) VALUES (%s, %s)", (new_pattern, new_division))
            connection.commit()
            return jsonify({'message': 'Pattern added!'}), 201

@api.route('/api/patterns/<string:pattern>', methods=['PUT', 'DELETE'])
def update_delete_pattern(pattern):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        if request.method == 'PUT':
            new_division = request.json['code']
            cursor.execute("UPDATE division_patterns SET code = %s WHERE pattern = %s", (new_division, pattern))
            connection.commit()
            return jsonify({'message': 'Pattern updated!'})

        elif request.method == 'DELETE':
            cursor.execute("DELETE FROM division_patterns WHERE pattern = %s", (pattern,))
            connection.commit()
            return jsonify({'message': 'Pattern deleted!'})
