from flask import Flask, request, render_template
import pandas as pd
import pymysql
from config import MYSQL_CONFIG

app = Flask(__name__)

# Global variable to store DataFrame
uploaded_df = None

def check_db_connection():
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        conn.close()
        return True
    except pymysql.MySQLError:
        return False

def read_excel(file):
    # Read the Excel file into a DataFrame
    df = pd.read_excel(file)
    return df

def query_database(data):
    results = []
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        for item in data:
            query = f"SELECT nomenklature, division_code FROM master_data WHERE nomenklature like %s"
            cursor.execute(query, (item,))
            results.extend(cursor.fetchall())

        cursor.close()
        conn.close()
    except pymysql.MySQLError as err:
        return str(err)
    
    return results

@app.route('/', methods=['GET', 'POST'])
def index():
    global uploaded_df
    message = ""
    if request.method == 'POST':
        file = request.files['file']
        
        if not check_db_connection():
            message = 'Database connection failed.'
            return render_template('index.html', status=message)

        # Read Excel content
        uploaded_df = read_excel(file)

        # Call analyze_excel with the uploaded DataFrame and the starting row
        modified_content = analyze_excel(uploaded_df)  # Replace 5 with your desired start row

        # Convert modified_content to DataFrame for rendering
        modified_df = pd.DataFrame(modified_content, columns=['Product', 'Total'])

        return render_template('index.html', 
                               status='File uploaded successfully!', 
                               uploaded_file=uploaded_df.to_html(classes='data', header="true", index=False),
                               modified_content=modified_df.to_html(classes='data', header="true", index=False))  # Pass modified content as HTML

    return render_template('index.html', status=message)

@app.route('/analyze', methods=['POST'])
def analyze_data():    
    # Analyze specific column
    # For example, analyze the 'column_name' column
    results = uploaded_df['column_name'].apply(lambda x: analyze_excel(x))
    
    # Connect to the MySQL database
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    
    # Example SQL query based on analysis results
    for result in results:
        cursor.execute("SELECT * FROM your_table WHERE your_condition = %s", (result,))
    
    query_results = cursor.fetchall()
    conn.close()

    # Process and visualize query_results
    display_result = "No results found."
    if query_results:  # Check for specific conditions
        display_result = f"Found {len(query_results)} results."

    return render_template('index.html', status="Analysis complete.", result=display_result)

import numpy as np
import pandas as pd  # Ensure pandas is imported for DataFrame operations

def analyze_excel(df):
    results = []
    start_row = 1
    stop_row = len(df) - 4  # Set stop_row to four less than the total number of rows
    count = 0

    for index in range(start_row, stop_row + 1):  # Include the last row
        if index < count:
            continue
        # Access the second and fourth columns
        second_column_content = df.iloc[index, 1]  # Second column
        fourth_column_content = df.iloc[index, 3]  # Fourth column

        # Check if the fourth column is NaN
        if pd.isna(fourth_column_content) or pd.isna(second_column_content):
            continue  # Skip this row if the any of columns is NaN

        # Check if fourth_column_content is not numeric
        if not isinstance(fourth_column_content, (int, float)) and not pd.to_numeric(fourth_column_content, errors='coerce'):
            continue  # Skip this row if fourth column is not numeric

        # Modify the second column content if necessary
        if isinstance(second_column_content, str):
            if '(' in second_column_content:
                second_column_content = second_column_content.replace('(', ' (')  # Add space before

            # Extract the substring from the second column content up to the first space
            first_space_index = second_column_content.find(' ')
            substring = second_column_content[:first_space_index] if first_space_index != -1 else second_column_content
            
            # Initialize the total sum with the current row's fourth column value
            total_sum = fourth_column_content

            # Loop through following rows to sum up the fourth column values
            for following_index in range(index + 1, stop_row + 1):
                following_content = df.iloc[following_index, 1]  # Get the second column of the following row
                
                # Check if the following content starts with the stored substring
                if isinstance(following_content, str) and following_content.startswith(substring):
                    following_fourth_column = df.iloc[following_index, 3]

                    # Only add to the total if the fourth column is valid (not NaN or 0)
                    if pd.notna(following_fourth_column) and following_fourth_column != 0:
                        total_sum += following_fourth_column  # Sum up the fourth column value
                else:
                    count = following_index
                    break  # Stop if a mismatch is found
            
            # Append the substring and total sum to results
            results.append((substring, total_sum))

    return results


if __name__ == '__main__':
    app.run(debug=True)
