from io import BytesIO
from flask import Flask, jsonify, request, render_template, send_file, session
import pandas as pd
import pymysql
import numpy as np
import json
import locale
import os
from datetime import datetime

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

from config import MYSQL_CONFIG
from api import api  # Import the API blueprint

app = Flask(__name__)

app.register_blueprint(api)

# Set the secret key to a random bytes string
app.secret_key = os.urandom(24)  # Generates a random 24-byte key

# Global variable to store DataFrame
uploaded_df = None
# Global variable to store patterns and divisions
patterns_divisions_dict = {}
# Global const
start_row = 0
skip_rows = 3
file_total = 0
first_column_name = 'Product'
second_column_name = 'Total'
third_column_name = 'Division'

def check_db_connection():
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        conn.close()
        return True
    except pymysql.MySQLError:
        return False

def read_excel(file):
    # Read the Excel file into a DataFrame
    df = pd.read_excel(file, skiprows=skip_rows)
    return df

def read_total():
    last_row = uploaded_df.tail(1)

    # Access the value from the fourth column
    value_from_fourth_column = last_row.iloc[0, 3]  # Using index (0-based)

    print("Value from the fourth column of the last row:")
    print(value_from_fourth_column)
    return value_from_fourth_column

@app.route('/', methods=['GET', 'POST'])
def index():
    global uploaded_df
    global file_total
    message = ""
    current_year = datetime.now().year  # Get the current year
    if request.method == 'POST':
        file = request.files['file']
        
        if not check_db_connection():
            message = 'Database connection failed.'
            return render_template('index.html', current_year=current_year, status=message)

        uploaded_df = read_excel(file)
        file_total = read_total()
        # Call prepare_excel with the uploaded DataFrame
        modified_excel_df = pd.DataFrame(prepare_excel(uploaded_df) , columns=[first_column_name, second_column_name])

        modified_excel_df = modified_excel_df.sort_values(by=modified_excel_df.columns[0], ascending=True)

        # If you want to reset the index after reading
        modified_excel_df.reset_index(drop=True, inplace=True)

        # Call analyze_excel with the uploaded DataFrame
        modified_content = analyze_excel(modified_excel_df) 

        # Convert modified_content to DataFrame for rendering
        modified_df = pd.DataFrame(modified_content, columns=[first_column_name, second_column_name, third_column_name])

        json_dumps=json.dumps(modified_df.to_dict(orient='records'))

        return render_template('index.html', current_year=current_year, file_total = file_total,
                               status='File uploaded successfully!', 
                               uploaded_file=uploaded_df.to_html(classes='data', header="true", index=False),
                               modified_content_json=json_dumps)  

    return render_template('index.html', status=message)

def query_database(data):
    results = []
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        query = "SELECT division_code FROM sales_product_paterns WHERE product = '{s}' ".format(s=data)
        cursor.execute(query)  # Pass the entire content as a parameter
        if cursor.rowcount == 0:
            query = "SELECT DISTINCT division_code FROM master_data WHERE nomenklature LIKE '{s}%'".format(s=data)
            # query = "SELECT division_code FROM product WHERE name LIKE '{s}%'".format(s=data)
            cursor.execute(query)  # Pass the entire content as a parameter

        results = cursor.fetchall()  # Fetch all results

        cursor.close()
        conn.close()
    except pymysql.MySQLError as err:
        return str(err)
    
    return results

def describe_division(second_column_content):
    global patterns_divisions_dict
    # Query the database with second_column_content+SPACE
    division_code = query_database(second_column_content+" ")
    
    # If the query returns one result, return the division code
    if len(division_code) == 1:
        return division_code[0][0]  # Return the division_code
    
    # Check if the second_column_content matches any pattern
    for pattern in patterns_divisions_dict:
        if pattern in second_column_content:
            return patterns_divisions_dict[pattern]  # Return the corresponding division
    # Return "0" string if there are no results or more than one result
    return "0"

def get_patterns_from_db():
    """Fetch patterns and their corresponding divisions from the MySQL database."""
    global patterns_divisions_dict  # Declare the global variable

    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        with connection.cursor() as cursor:
            cursor.execute("SELECT pattern, code FROM division_patterns")  # Adjust query as needed
            results = cursor.fetchall()  # Fetch all results
            
            # Populate the dictionary from the fetched results
            for pattern, code in results:
                patterns_divisions_dict[pattern] = code
                
    finally:
        connection.close()

def contains_substring_no_space(s, substring):
    index = s.find(substring)
    if index == -1:
        return False
    # Check if the character before the substring is a space or if it's at the start of the string
    if index == 0 or s[index - 1] != ' ':
        return True
    return False

def prepare_exel_content(second_column_content):
    if isinstance(second_column_content, str):
        if 'ПОДОШВА ПУ ' in second_column_content:
            second_column_content = second_column_content.replace('ПОДОШВА ПУ ', '')  # replace
        if 'ПОДОШВА ТЭП ' in second_column_content:
            second_column_content = second_column_content.replace('ПОДОШВА ТЭП ', '')  # replace
        if 'ПОДОШВА ЭВА ' in second_column_content:
            second_column_content = second_column_content.replace('ПОДОШВА ЭВА ', '')  # replace
        if 'ПОДОШВА ' in second_column_content:
            second_column_content = second_column_content.replace('ПОДОШВА ', '')  # replace
        if '(' in second_column_content:
            second_column_content = second_column_content.replace('(', ' (')  # Add space before
        if 'АРТ №' in second_column_content:
            second_column_content = second_column_content.replace('АРТ №', 'АРТ.№')  # Add dot before
        if '№' in second_column_content and second_column_content.strip()[0] == '№':
            second_column_content = 'АРТ.'+second_column_content  # Add prefix before
        if second_column_content.strip() and second_column_content.strip()[0].isdigit():
            second_column_content = 'АРТ.№'+second_column_content  # Add prefix before
    else:
        return ""
    return second_column_content

def prepare_excel(df):
    results = []

    for index in range(start_row, len(df)):  # Include the last row
        # Access the second and fourth columns
        second_column_content = df.iloc[index, 1]  # Second column
        fourth_column_content = df.iloc[index, 3]  # Fourth column

        # Check if the fourth column is NaN
        if pd.isna(fourth_column_content) or pd.isna(second_column_content):
            continue  # Skip this row if the any of columns is NaN

        # Check if fourth_column_content is numeric
        if not isinstance(fourth_column_content, (int, float)) and pd.isna(pd.to_numeric(fourth_column_content, errors='coerce')):
            continue  # Skip this row if fourth column is not numeric          

        # Modify the second column content if necessary
        if isinstance(second_column_content, str):
            second_column_content = prepare_exel_content(second_column_content)
            
            # Append the substring and total sum to results
            results.append((second_column_content, fourth_column_content))

    return results
        
def analyze_excel(df):
    results = []
    count = 0
    get_patterns_from_db()

    for index in range(start_row, len(df)):  # Include the last row
        if index < count:
            continue
        # Prevent loop with last row in case it has already been added by following_index inner loop 
        if index == len(df) - 1 and following_content.startswith(substring+" "): break

        # Access the First and Second columns
        product_content = df.loc[index, first_column_name]  # First column
        number_content = df.loc[index, second_column_name]  # Second column       

        # Extract the substring from the second column content up to the first space
        first_space_index = product_content.find(' ')
        substring = product_content[:first_space_index] if first_space_index != -1 else product_content
        
        # Look up for division
        division = describe_division(substring) if substring else "0"

        # Initialize the total sum with the current row's fourth column value
        total_sum = number_content

        # Loop through following rows to sum up the fourth column values
        for following_index in range(index + 1, len(df)):
            following_content = df.loc[following_index, first_column_name]  # Get the second column of the following row

            # Check if the following content starts with the stored substring
            if isinstance(following_content, str) and following_content.startswith(substring+" "):
                following_total = df.loc[following_index, second_column_name]

                # Only add to the total if the fourth column is valid (not NaN or 0)
                if pd.notna(following_total) and following_total != 0:
                    total_sum += following_total  # Sum up the total value
            else:
                break  # Stop if a mismatch is found
     
        count = following_index
        # Append the substring and total sum to results
        results.append((substring, total_sum, division))

    return results

@app.route('/api/save', methods=['POST'])
def save_data():
    # Delegate save functionality to the API
    return api.save_data()

@app.route('/show_data', methods=['GET'])
def show_data():
    try:
        # Set locale for month names (if needed elsewhere, else can be removed)
        locale.setlocale(locale.LC_TIME, '')
        print('Current locale:', locale.getlocale(locale.LC_TIME))

        connection = pymysql.connect(**MYSQL_CONFIG)
        with connection.cursor() as cursor:
            # Fetch divisions with names, extracting month names and numbers
            query = """
                SELECT s.product, s.total, d.name AS division_name, 
                       DATE_FORMAT(s.date_of_change, '%M') AS month_name,
                       MONTH(s.date_of_change) AS month_number
                FROM sales s
                JOIN division d ON s.division_code = d.code
                ORDER BY MONTH(s.date_of_change), s.product
            """
            cursor.execute(query)
            results = cursor.fetchall()  

        # Initialize a dictionary to hold the pivoted data
        pivot_data = {}
        months_order = []
        seen_months = set()

        for row in results:
            month_name = row[3]  # Assuming month_name is at index 3
            if month_name not in seen_months:
                seen_months.add(month_name)
                months_order.append(month_name)

        # Process each row and build the pivoted data
        for row in results:
            product, total, division_name, month_name, month_number = row

            # Create a key for each product and division combination
            product_division_key = f"{product}_{division_name}"

            # Initialize the dictionary for the key if not already present
            if product_division_key not in pivot_data:
                pivot_data[product_division_key] = {
                    "Product": product,
                    "Division": division_name,
                    **{month: 0 for month in months_order}  # Initialize all months to 0
                }

            # Add the total to the corresponding month
            if month_name in pivot_data[product_division_key]:
                pivot_data[product_division_key][month_name] += total
            else:
                # Handle the case where month_name doesn't exist (though it should if months_order is correct)
                pivot_data[product_division_key][month_name] = total

        # Add a 'Total' column for each product
        for key, data in pivot_data.items():
            data["Total"] = sum(data[month] for month in months_order)

        # Convert pivot_data dictionary to a list of rows (for AG Grid)
        pivot_table_rows = list(pivot_data.values())

    except pymysql.MySQLError as e:
        return render_template('show_data.html', error=str(e), data=[], divisions=[])

    # Render the template and pass data for AG Grid
    return render_template('show_data.html', 
                           data=pivot_table_rows,  # Pass the processed data
                           months=months_order)  # Optionally, pass the months for filtering

@app.route('/export')
def export():
    try:
        # Connect to the database
        connection = pymysql.connect(**MYSQL_CONFIG)
        with connection.cursor() as cursor:
            # Fetch the complete sales data
            query = """
                SELECT s.product, s.total, d.name AS division_name, 
                       DATE_FORMAT(s.date_of_change, '%M') AS month_name,
                       MONTH(s.date_of_change) AS month_number
                FROM sales s
                JOIN division d ON s.division_code = d.code
            """
            cursor.execute(query)
            results = cursor.fetchall()

        # Convert results to DataFrame
        columns = ['Product', 'Total', 'Division', 'Month', 'Month Number']
        data = pd.DataFrame(results, columns=columns)

        # Pivot the DataFrame
        pivot_table = data.pivot_table(
            index=['Product', 'Division'],  
            columns='Month',  
            values='Total', 
            aggfunc='sum',  
            fill_value=0  
        )

        # Sort the pivot table columns based on month number
        pivot_table = pivot_table.reindex(
            sorted(pivot_table.columns, key=lambda x: data[data['Month'] == x]['Month Number'].values[0]),
            axis=1
        )

        # Convert the final pivot table to a DataFrame for export
        final_data = pivot_table.reset_index()

        # Export to Excel
        output_path = 'full_data_with_totals.xlsx'
        final_data.to_excel(output_path, index=False)

        # Return the file for download
        return send_file(output_path, as_attachment=True)

    except pymysql.MySQLError as e:
        return str(e), 500  # Database error handling

    except Exception as e:
        return str(e), 500  # General error handling


if __name__ == '__main__':
    app.run(debug=True)
