# Test DB1 (MySQL)
import aiomysql
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def test_db1():
    try:
        conn = await aiomysql.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            db=os.getenv('MYSQL_DATABASE')
        )
        conn.close()
        print("DB1 connected")
    except Exception as e:
        print(f"DB1 connection failed: {e}")

# Test DB2 (MSSQL)
import pyodbc

def test_db2():
    try:
        conn = pyodbc.connect(
            f"DRIVER={{SQL Server}};"
            f"SERVER={os.getenv('MSSQL_SERVER')};"
            f"DATABASE={os.getenv('MSSQL_DATABASE')};"
            f"UID={os.getenv('MSSQL_USERNAME')};"
            f"PWD={os.getenv('MSSQL_PASSWORD')}"
        )
        conn.close()
        print("DB2 connected")
    except Exception as e:
        print(f"DB2 connection failed: {e}")

# Run async tests
async def main():
    await test_db1()
    test_db2()

if __name__ == "__main__":
    asyncio.run(main())