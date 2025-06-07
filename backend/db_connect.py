import aiomysql
import pyodbc
import logging
import asyncio
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MySQLDB:
    def __init__(self, credentials):
        self.credentials = credentials
        self.pool = None

    async def init_pool(self):
        try:
            self.pool = await aiomysql.create_pool(
                host=self.credentials['host'],
                user=self.credentials['user'],
                password=self.credentials['password'],
                db=self.credentials['database'],
                autocommit=True
            )
            logger.info("MySQL connection pool initialized")
            return self
        except Exception as e:
            logger.error(f"Error initializing MySQL pool: {e}")
            raise

    @asynccontextmanager
    async def get_cursor(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                yield cursor

    async def query(self, query, params=None):
        try:
            async with self.get_cursor() as cursor:
                await cursor.execute(query, params)
                if query.strip().upper().startswith("SELECT"):
                    return await cursor.fetchall()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"MySQL query error: {e}, query: {query}")
            raise

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("MySQL connection pool closed")

class MSSQLDB:
    def __init__(self, credentials):
        self.credentials = credentials
        self.conn = None
        self.cursor = None
        try:
            conn_str = (
                f"DRIVER={{SQL Server}};"
                f"SERVER={self.credentials['server']};"
                f"DATABASE={self.credentials['database']};"
                f"UID={self.credentials['username']};"
                f"PWD={self.credentials['password']}"
            )
            self.conn = pyodbc.connect(conn_str)
            self.cursor = self.conn.cursor()
            logger.info("MSSQL connection established")
        except Exception as e:
            logger.error(f"Error connecting to MSSQL: {e}")
            raise

    def execute_query(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            if query.strip().upper().startswith("SELECT"):
                return self.cursor.fetchall()
            self.conn.commit()
            return self.cursor.rowcount
        except Exception as e:
            logger.error(f"MSSQL query error: {e}, query: {query}")
            raise

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("MSSQL connection closed")

class DB3:
    def __init__(self, credentials):
        self.credentials = credentials
        self.pool = None

    async def init_pool(self):
        try:
            self.pool = await aiomysql.create_pool(
                host=self.credentials['host'],
                user=self.credentials['user'],
                password=self.credentials['password'],
                db=self.credentials['database'],
                autocommit=True
            )
            logger.info("DB3 connection pool initialized")
            return self
        except Exception as e:
            logger.error(f"Error initializing DB3 pool: {e}")
            raise

    @asynccontextmanager
    async def get_cursor(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                yield cursor

    async def query(self, query, params=None):
        try:
            async with self.get_cursor() as cursor:
                await cursor.execute(query, params)
                if query.strip().upper().startswith("SELECT"):
                    return await cursor.fetchall()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"DB3 query error: {e}, query: {query}")
            raise

    async def insert_user(self, name, mobile, city, otp):
        query = "INSERT INTO user_details (name, mobile, city, demo_otp, created_at) VALUES (%s, %s, %s, %s, NOW())"
        try:
            async with self.get_cursor() as cursor:
                await cursor.execute(query, (name, mobile, city, otp))
                user_id = cursor.lastrowid
                return user_id
        except Exception as e:
            logger.error(f"Error inserting user: {e}")
            raise

    async def verify_otp(self, user_id, otp):
        query = "SELECT id FROM user_details WHERE id = %s AND demo_otp = %s"
        try:
            async with self.get_cursor() as cursor:
                await cursor.execute(query, (user_id, otp))
                result = await cursor.fetchone()
                if result:
                    await cursor.execute("UPDATE user_details SET demo_otp = NULL WHERE id = %s", (user_id,))
                    return True
                return False
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            raise

    async def query_subcourses(self, course):
        query = "SELECT DISTINCT subcourse FROM subcourses WHERE course = %s"
        return await self.query(query, (course,))

    async def get_categories(self):
        query = "SELECT id, name FROM categories WHERE is_active = TRUE"
        return await self.query(query)

    async def get_questions(self, category_id):
        query = "SELECT id, question_text FROM questions WHERE category_id = %s AND is_active = TRUE"
        return await self.query(query, (category_id,))

    async def get_answer(self, question_id, context, db1, db2):
        query = "SELECT answer_text FROM answers WHERE question_id = %s"
        try:
            async with self.get_cursor() as cursor:
                await cursor.execute(query, (question_id,))
                result = await cursor.fetchone()
                if result:
                    answer = result[0]
                    if "{course}" in answer:
                        answer = answer.format(**context)
                    return answer
                return "No answer found for this question."
        except Exception as e:
            logger.error(f"Error fetching answer: {e}")
            raise

    async def log_query(self, user_id, course, subcourse, training_type, category_id, question_id, answer):
        query = """INSERT INTO query_logs (user_id, course, subcourse, training_type, category_id, question_id, answer, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())"""
        try:
            await self.query(query, (user_id, course, subcourse, training_type, category_id, question_id, answer))
        except Exception as e:
            logger.error(f"Error logging query: {e}")
            raise

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("DB3 connection pool closed")