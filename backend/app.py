import os
from flask import Flask, request, jsonify, render_template_string
from google.cloud import aiplatform
import google.generativeai as genai
import psycopg2
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Google GenAI API
API_KEY = "AIzaSyC9uXy92lQX2knCanapxwVfEHRixkpG8rM"
genai.configure(api_key=API_KEY)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up PostgreSQL connection using environment variables
DATABASE_URL = (
    f"dbname='{os.getenv('DB_NAME', 'myappdb')}' "
    f"user='{os.getenv('DB_USER', 'ranbir')}' "
    f"password='{os.getenv('DB_PASSWORD', 'Saini@1994')}' "
    f"host='{os.getenv('DB_HOST', '34.121.210.209')}'"
)

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("Connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"An error occurred while connecting to the database: {e}")
        raise Exception(f"An error occurred while connecting to the database: {e}")

def create_table():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            student_id TEXT NOT NULL UNIQUE,
            course TEXT NOT NULL
        );
        '''
        cursor.execute(create_table_query)
        conn.commit()
        logger.info("Table 'students' created successfully or already exists.")
    except Exception as e:
        logger.error(f"An error occurred while creating the table: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/generate', methods=['POST'])
def generate_text():
    prompt = request.json.get('prompt')
    if not prompt:
        return jsonify({'error': 'Prompt is required'})
    
    try:
        response = genai.generate_text(prompt=prompt)
        generated_text = response.result if hasattr(response, 'result') else 'No result found in response'
        return jsonify({'response': generated_text})
    except Exception as e:
        logger.error(f"An error occurred while generating text: {e}")
        return jsonify({'error': str(e)})

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    name = data.get('name')
    student_id = data.get('id')
    course = data.get('course')
    
    if not name or not student_id or not course:
        return jsonify({'error': 'Missing required fields'})

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        insert_query = "INSERT INTO students (name, student_id, course) VALUES (%s, %s, %s);"
        cursor.execute(insert_query, (name, student_id, course))
        conn.commit()
        logger.info("Student information inserted into the database")
        return jsonify({'message': 'Student information inserted successfully', 'name': name, 'id': student_id, 'course': course})
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"An error occurred while inserting student information into the database: {e}")
        return jsonify({'error': 'An error occurred while inserting student information into the database'})
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/')
def index():
    return render_template_string(HTML_CONTENT)

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Combined App</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            background-color: #f4f4f4;
            height: 100vh;
            justify-content: center;
        }
        .container {
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            width: 300px;
            text-align: center;
        }
        textarea, input {
            width: 100%;
            padding: 10px;
            border-radius: 4px;
            border: 1px solid #ccc;
            margin-bottom: 10px;
        }
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            background-color: #007bff;
            color: #fff;
            cursor: pointer;
            width: 100%;
        }
        button:hover {
            background-color: #0056b3;
        }
        .response {
            margin-top: 20px;
        }
        .hidden {
            display: none;
        }
        .selection-box {
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="selection-box">
            <label for="appSelection">Choose an app:</label>
            <select id="appSelection" onchange="toggleApp()">
                <option value="">--Select an app--</option>
                <option value="textGen">Text Generation</option>
                <option value="studentInfo">Student Information</option>
            </select>
        </div>

        <div id="textGenApp" class="hidden">
            <h1>Text Generation</h1>
            <textarea id="prompt" placeholder="Enter your prompt here..."></textarea>
            <button onclick="generateText()">Generate</button>
            <div class="response" id="response"></div>
        </div>

        <div id="studentInfoApp" class="hidden">
            <h1>Enter Student Information</h1>
            <form id="studentForm">
                <label for="name">Name:</label>
                <input type="text" id="name" name="name" required>
                <br><br>
                <label for="id">ID:</label>
                <input type="text" id="id" name="id" required>
                <br><br>
                <label for="course">Course:</label>
                <input type="text" id="course" name="course" required>
                <br><br>
                <button type="button" onclick="submitForm()">Submit</button>
            </form>
        </div>
    </div>

    <script>
        function toggleApp() {
            const selection = document.getElementById('appSelection').value;
            document.getElementById('textGenApp').classList.add('hidden');
            document.getElementById('studentInfoApp').classList.add('hidden');

            if (selection === 'textGen') {
                document.getElementById('textGenApp').classList.remove('hidden');
            } else if (selection === 'studentInfo') {
                document.getElementById('studentInfoApp').classList.remove('hidden');
            }
        }

        async function generateText() {
            const prompt = document.getElementById('prompt').value;
            const responseDiv = document.getElementById('response');
            responseDiv.innerHTML = 'Generating...';

            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ prompt })
                });

                const data = await response.json();
                if (data.response) {
                    responseDiv.innerHTML = data.response;
                } else {
                    responseDiv.innerHTML = 'Error: ' + data.error;
                }
            } catch (error) {
                responseDiv.innerHTML = 'Error: ' + error.message;
                console.error('Error:', error);
            }
        }

        async function submitForm() {
            const name = document.getElementById('name').value;
            const id = document.getElementById('id').value;
            const course = document.getElementById('course').value;

            const data = {
                name: name,
                id: id,
                course: course
            };

            try {
                const response = await fetch('/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    alert('Student information submitted successfully!');
                } else {
                    alert('Failed to submit student information.');
                }
            } catch (error) {
                alert('An error occurred while submitting student information.');
                console.error('Error:', error);
            }
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    # Create the table when the application starts
    create_table()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
