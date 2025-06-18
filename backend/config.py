# config.py
from dotenv import load_dotenv
import os

load_dotenv()

MYSQL_CREDENTIALS = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE")
}