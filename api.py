from flask import Blueprint, jsonify, request
import pymysql
import pandas as pd
from datetime import datetime

from config import MYSQL_CONFIG

def get_db_connection():
    return pymysql.connect(**MYSQL_CONFIG)

# Create a Blueprint for the API
api = Blueprint('api', __name__)

@api.route('/api/divisions', methods=['GET'])
def get_divisions():
    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        with connection.cursor() as cursor:
            cursor.execute("SELECT code, name FROM division")
            divisions = cursor.fetchall()
        print("Fetched divisions:", divisions)  # Debugging line
        return jsonify(divisions)
    except pymysql.MySQLError as e:
        return jsonify({"status": "error", "message": str(e)})
    finally:
        connection.close()

@api.route('/api/save', methods=['POST'])
def save_data():
    # Get the data from the request
    data = request.json  # This should contain both the date and modified content

    # Extract the date and modified content
    date_of_change = data.get('date')  # Get the date value
    modified_content = data.get('data', [])  # Get the modified content, default to an empty list if not provided

    # Get the year and month from the date
    year_month = datetime.strptime(date_of_change, "%Y-%m-%d").strftime("%Y-%m")

    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        with connection.cursor() as cursor:
            # Check if any rows exist for the specified month
            cursor.execute("SELECT COUNT(*) FROM sales WHERE DATE_FORMAT(date_of_change, '%%Y-%%m') = %s", (year_month,))
            count = cursor.fetchone()[0]

            if count > 0:
                # Inform the user about existing data and ask for confirmation
                return jsonify({
                    "status": "warning",
                    "message": f"Data for {year_month} already exists. Do you want to delete existing records and insert new ones?",
                    "confirm_deletion": True  # Indicate that user confirmation is needed
                })

            # If no records exist, proceed to insert new data
            for entry in modified_content:
                cursor.execute("INSERT INTO sales (product, total, division_code, date_of_change) VALUES (%s, %s, %s, %s)",
                               (entry['Product'], entry['Total'], entry['Division'], date_of_change))  # Adjust as necessary

            connection.commit()
        return jsonify({"status": "success", "message": "Data saved successfully."})

    except pymysql.MySQLError as e:
        return jsonify({"status": "error", "message": str(e)})
    
    finally:
        connection.close()

# Additional route for deletion confirmation
@api.route('/api/delete_and_save', methods=['POST'])
def delete_and_save():
    data = request.json
    date_of_change = data.get('date')
    modified_content = data.get('data', [])

    year_month = datetime.strptime(date_of_change, "%Y-%m-%d").strftime("%Y-%m")

    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        with connection.cursor() as cursor:
            # Delete existing records for the specified month
            cursor.execute("DELETE FROM sales WHERE DATE_FORMAT(date_of_change, '%%Y-%%m') = %s", (year_month,))
            connection.commit()

            # Insert new data
            for entry in modified_content:
                cursor.execute("INSERT INTO sales (product, total, division_code, date_of_change) VALUES (%s, %s, %s, %s)",
                               (entry['Product'], entry['Total'], entry['Division'], date_of_change))

            connection.commit()
        return jsonify({"status": "success", "message": "Data deleted and new data saved successfully."})

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

@api.route('/api/product_patterns', methods=['GET', 'POST'])
def manage_product_patterns():
    connection = get_db_connection()
    with connection.cursor() as cursor:
        if request.method == 'GET':
            cursor.execute("SELECT id, product, division_code FROM sales_product_paterns")
            sales_product_paterns = cursor.fetchall()
            return jsonify([{'id': pd[0], 'product': pd[1], 'division_code': pd[2]} for pd in sales_product_paterns])
        
        elif request.method == 'POST':
            new_pattern = request.json['product']
            new_division = request.json['division_code']
            cursor.execute("INSERT INTO sales_product_paterns (product, division_code) VALUES (%s, %s)", (new_pattern, new_division))
            connection.commit()
            return jsonify({'message': 'Pattern added!'}), 201