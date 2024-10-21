# config.py
import os

MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'qr'),
    'password': os.getenv('MYSQL_PASSWORD', 'barCode128c'),
    'database': os.getenv('MYSQL_DB', 'qr'),
    'charset': 'utf8'  # Use appropriate charset
}

#    'cursorclass': pymysql.cursors.DictCursor,  # Optional: to get results as dictionaries