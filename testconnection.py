import aiomysql
import asyncio
import os
from dotenv import load_dotenv

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

async def main():
    await test_db1()

if __name__ == "__main__":
    asyncio.run(main())