import aiomysql
import logging
import asyncio
from contextlib import asynccontextmanager
from datetime import date
from datetime import datetime

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
                autocommit=True,
                charset='utf8mb4'
            )
            logger.info("MySQL connection pool initialized")
            return self
        except Exception as e:
            logger.error(f"Error initializing MySQL pool: {e}")
            raise

    @asynccontextmanager
    async def get_cursor(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
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

    async def get_course_price(self, variant):
        query = "SELECT Price, OfferPrice FROM coursedetails WHERE Coursesubvariant = %s"
        try:
            async with self.get_cursor() as cursor:
                await cursor.execute(query, (variant,))
                return await cursor.fetchone()
        except Exception as e:
            logger.error(f"Error fetching course price for variant {variant}: {e}")
            raise

    async def get_course_content(self, course_id, coursename):
        query = """
            SELECT Subtitle, Link
            FROM coursecontent
            WHERE Course = %s
            AND Title LIKE %s
            AND Contentstatus = 'yes'
        """
        try:
            async with self.get_cursor() as cursor:
                await cursor.execute(query, (course_id, f"%{coursename} Results%"))
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching course content: {e}")
            raise

    async def get_testimonials(self, city, course_title):
        query = """
            SELECT video_url
            FROM course_testmonials
            WHERE city = %s
            AND course LIKE %s
        """
        try:
            async with self.get_cursor() as cursor:
                await cursor.execute(query, (city, f"%{course_title}%"))
                results = await cursor.fetchall()
                if not results:
                    query = """
                        SELECT video_url
                        FROM course_testmonials
                        WHERE course LIKE %s
                    """
                    await cursor.execute(query, (f"%{course_title}%",))
                    results = await cursor.fetchall()
                return results
        except Exception as e:
            logger.error(f"Error fetching testimonials: {e}")
            raise

    async def get_bschool_selection(self, course_id):
        query = """
            SELECT Subtitle, Link
            FROM coursecontent
            WHERE Course = %s
            AND Title LIKE %s
            AND Contentstatus IN ('Yes', 'yes')
        """
        try:
            async with self.get_cursor() as cursor:
                await cursor.execute(query, (course_id, '%B-School Selection%'))
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching B-School Selection data: {e}")
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

    async def get_scholarship_exams(self, course, city):
        query = "SELECT course, city, description, ttse_rstdate, ttse_date FROM ttse_creation WHERE course = %s AND (city = %s OR city IN ('All', 'all'))"
        try:
            result = await self.query(query, (course, city))
            return result
        except Exception as e:
            logger.error(f"Error fetching scholarship exams for course {course}, city {city}: {e}")
            raise

    async def get_answer(self, question_id, context):
        query = """
            SELECT q.source_type, q.source_detail, sa.answer_text AS static_answer
            FROM questions q
            LEFT JOIN static_answers sa ON q.id = sa.question_id
            WHERE q.id = %s
        """
        try:
            async with self.get_cursor() as cursor:
                await cursor.execute(query, (question_id,))
                result = await cursor.fetchone()
                if not result:
                    return "No answer found for this question."

                source_type = result['source_type']
                source_detail = result['source_detail']

                if source_type == 'STATIC':
                    answer = result['static_answer']
                    if answer:
                        return answer.format(**context) if '{city}' in answer else answer
                    return "No static answer available."

                elif source_type == 'DB':
                    if source_detail == 'coursedetails':
                        price_info = await self.get_course_price(context.get('training_type'))
                        if price_info:
                            answer = f"The price for {context.get('training_type')} is ₹{price_info['Price']}."
                            if price_info['OfferPrice'] is not None and price_info['OfferPrice'].strip():
                                answer += f" Also, the offer price for the course is ₹{price_info['OfferPrice']}."
                            return answer
                        return "No price information available for this course variant."
                    elif source_detail == 'ttse_creation':
                        exams = await self.get_scholarship_exams(context.get('course'), context.get('city'))
                        if not exams:
                            return f"No scholarship exams available for {context.get('course')}."
                        answer = f"Scholarship exam(s) for {context.get('course')}:\n\n"
                        current_date = date.today()
                        valid_exams = False
                        for exam in exams:
                            if exam['city'].lower() == 'all':
                                test_type = 'All India'
                            else:
                                test_type = exam['city']
                            reg_date_str = exam['ttse_rstdate']
                            exam_date_str = exam['ttse_date']
                            try:
                                # Handle datetime.date objects
                                if isinstance(reg_date_str, date):
                                    reg_date = reg_date_str
                                else:
                                    try:
                                        reg_date = datetime.strptime(reg_date_str, '%Y-%m-%d').date()
                                    except ValueError:
                                        logger.error(f"Invalid date format for ttse_rstdate: {reg_date_str}")
                                        continue
                                exam_date = exam_date_str
                            except ValueError:
                                logger.error(f"Invalid date format for ttse_rstdate: {reg_date_str}")
                                continue
                            reg_text = f"Registration closed on {reg_date:%Y-%m-%d}" if reg_date < current_date else f"Registration Date: {reg_date:%Y-%m-%d}"
                            answer += (
                                f"Test: {exam['description']}\n"
                                f"Test type: {test_type}\n"
                                f"{reg_text}\n"
                                f"Exam Date: {exam_date}\n\n"
                            )
                            valid_exams = True
                        if not valid_exams:
                            return f"No scholarship exams available for {context.get('course')} in {context.get('city')}."
                        return f"<div class='scholarship-details'>{answer.strip()}</div>"
                    elif source_detail == 'exam_info':
                        query = f"SELECT {source_detail} FROM exam_info WHERE course = %s"
                        result = await self.query(query, (context.get('course'),))
                        if result:
                            return result[0][source_detail]
                    return "No answer found for this question."
        except Exception as e:
            logger.error(f"Error fetching answer for question {question_id}: {e}")
            raise

    async def log_query(self, user_id, course, subcourse, training_type, category_id, question_id, answer):
        query = """INSERT INTO query_history (user_id, course, subcourse, training_type, category_id, question_id, answer_text, queried_at)
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
            logger.info("MySQL connection pool closed")