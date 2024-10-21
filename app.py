# app.py
from flask import Flask, request, render_template
import pandas as pd
import pymysql
import os

from config import MYSQL_CONFIG

app = Flask(__name__)

# Global variable to store DataFrame
uploaded_df = None

# Check MySQL connection
def check_db_connection():
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        conn.close()
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False

def read_excel(file):
    # Read the Excel file into a DataFrame
    df = pd.read_excel(file)
    return df

def analyze_excel(df):
    results = []
    # Example: Analyze first column 'Column1'
    for index, row in df.iterrows():
        content = row['Column1']
        if 'specific_condition' in content:
            results.append(content)
    return results

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
    message = ""
    df = None
    if request.method == 'POST':
        file = request.files['file']
        
        if not check_db_connection():
            message = 'Database connection failed.'
            return render_template('index.html', message=message)

        # Read and display Excel content
        df = read_excel(file)
        results = analyze_excel(df)
        query_results = query_database(results)

        return render_template('results.html', df=df.to_html(classes='data', header="true", index=False), query_results=query_results)

    return render_template('index.html', message=message)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part"
    file = request.files['file']
    if file.filename == '':
        return "No selected file"
    
    if file and file.filename.endswith('.xlsx'):
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        return render_template('index.html', status="File uploaded successfully.", uploaded_file=file.filename, result=None)
    return "Invalid file type"

@app.route('/analyze', methods=['POST'])
def analyze_data():
    # Load the uploaded file
    file_path = 'uploads/your_file.xlsx'  # Change this based on how you handle uploads
    df = pd.read_excel(file_path)
    
    # Analyze specific column
    # For example, analyze the 'column_name' column
    results = df['column_name'].apply(lambda x: your_analysis_function(x))
    
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

def your_analysis_function(value):
    # Define your analysis logic here
    return value  # Modify this based on your conditions

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
