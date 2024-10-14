from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import sqlite3
import os
import subprocess
import threading

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Get the absolute path to the directory containing this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Construct the database path
DB_PATH = os.path.join(BASE_DIR, '..', 'database', 'app.db')
# Construct the screenshots path
SCREENSHOTS_PATH = os.path.join(BASE_DIR, '..')

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/', methods=['GET'])
def hello():
    return jsonify({"message": "Hello, World!"})

@app.route('/articles', methods=['GET'])
def get_articles():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM article")
        articles = cursor.fetchall()
        return jsonify([dict(article) for article in articles])
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/article/<int:article_id>', methods=['GET'])
def get_article(article_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM article WHERE id = ?", (article_id,))
        article = cursor.fetchone()
        
        if article is None:
            return jsonify({"error": "Article not found"}), 404
        
        return jsonify(dict(article))
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

def run_background_job(command):
    subprocess.Popen(command, shell=True)

@app.route('/trigger-job', methods=['POST'])
def trigger_job():
    data = request.json
    job_command = data.get('command', '')
    
    if not job_command:
        return jsonify({"error": "No command provided"}), 400
    
    # Start the job in a separate thread
    thread = threading.Thread(target=run_background_job, args=(job_command,))
    thread.start()
    
    return jsonify({"message": "Job started successfully"}), 200

@app.route('/logs/<log_name>', methods=['GET'])
def get_logs(log_name):
    log_dir = os.path.join(BASE_DIR, '..', 'logs')
    log_path = os.path.join(log_dir, f"{log_name}.log")
    
    if not os.path.exists(log_path):
        return jsonify({"error": f"Log file {log_name}.log not found"}), 404
    
    try:
        with open(log_path, 'r') as file:
            # Read the last 100 lines
            lines = file.readlines()[-100:]
        
        return jsonify({"log_name": log_name, "lines": lines})
    except Exception as e:
        return jsonify({"error": f"Error reading log file: {str(e)}"}), 500

@app.route('/screenshot', methods=['GET'])
def get_screenshot():
    article_id = request.args.get('id')
    if not article_id:
        return jsonify({"error": "No article ID provided"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT screenshot_path FROM article WHERE id = ?", (article_id,))
        result = cursor.fetchone()
        print(result['screenshot_path'])

        if result is None or result['screenshot_path'] is None:
            return jsonify({"error": "Screenshot not found"}), 404

        screenshot_path = result['screenshot_path']
        full_path = os.path.join(SCREENSHOTS_PATH, screenshot_path)
        print(full_path)
        if not os.path.exists(full_path):
            return jsonify({"error": "Screenshot file not found"}), 404

        return send_file(full_path, mimetype='image/png')
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    print(f"Database path: {DB_PATH}")
    print(f"Screenshots path: {SCREENSHOTS_PATH}")
    app.run(debug=True)
