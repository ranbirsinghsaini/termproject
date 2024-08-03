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
