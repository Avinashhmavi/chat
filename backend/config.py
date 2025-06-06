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

MSSQL_CREDENTIALS = {
    "server": os.getenv("MSSQL_SERVER"),
    "database": os.getenv("MSSQL_DATABASE"),
    "username": os.getenv("MSSQL_USERNAME"),
    "password": os.getenv("MSSQL_PASSWORD")
}

DB3_CREDENTIALS = {
    "host": os.getenv("DB3_HOST"),
    "user": os.getenv("DB3_USER"),
    "password": os.getenv("DB3_PASSWORD"),
    "database": os.getenv("DB3_DATABASE")
}