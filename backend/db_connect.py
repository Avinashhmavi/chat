# db_connect.py
import pymysql
import pyodbc
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MySQLDB:
    def __init__(self, credentials):
        self.conn = pymysql.connect(**credentials)
        self.cursor = self.conn.cursor()
    
    def query_courses(self, city):
        self.cursor.execute("""
        SELECT college_courses
        FROM locations
        WHERE city = %s AND college_courses IS NOT NULL
        """, (city,))
        courses = []
        for row in self.cursor.fetchall():
            courses.extend(row[0].split(','))
        result = [(course, course) for course in sorted(set(courses)) if course]
        return result
    
    def query_centerdetails(self, city):
        self.cursor.execute("""
        SELECT address, phone, email
        FROM mdl_location_centerdetails
        WHERE city = %s
        LIMIT 1
        """, (city,))
        result = self.cursor.fetchone()
        return result if result else ("Not available", "Not available", "Not available")
    
    def get_random_testimonial_video(self, course, shown_videos):
        db_course = "CAT/MBA" if course == "CAT" else course
        if shown_videos:
            query = """
            SELECT video_url
            FROM course_testmonials
            WHERE course = %s AND video_url NOT IN (%s)
            ORDER BY RAND()
            LIMIT 1
            """
            placeholders = ', '.join(['%s'] * len(shown_videos))
            query = query % ('%s', placeholders)
            params = [db_course] + shown_videos
        else:
            query = """
            SELECT video_url
            FROM course_testmonials
            WHERE course = %s
            ORDER BY RAND()
            LIMIT 1
            """
            params = [db_course]
        self.cursor.execute(query, params)
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def __del__(self):
        self.cursor.close()
        self.conn.close()

class MSSQLDB:
    def __init__(self, credentials):
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={credentials['server']};"
            f"DATABASE={credentials['database']};"
            f"UID={credentials['username']};"
            f"PWD={credentials['password']}"
        )
        self.conn = pyodbc.connect(conn_str)
        self.cursor = self.conn.cursor()
    
    def __del__(self):
        self.cursor.close()
        self.conn.close()

class DB3:
    def __init__(self, credentials):
        self.conn = pymysql.connect(**credentials)
        self.cursor = self.conn.cursor()
    
    def insert_user(self, name, mobile, city, demo_otp="5762"):
        self.cursor.execute("""
        INSERT INTO user_details (name, mobile, city, demo_otp)
        VALUES (%s, %s, %s, %s)
        """, (name, mobile, city, demo_otp))
        self.conn.commit()
        self.cursor.execute("SELECT LAST_INSERT_ID()")
        user_id = self.cursor.fetchone()[0]
        return user_id
    
    def verify_otp(self, user_id, otp):
        self.cursor.execute("SELECT demo_otp FROM user_details WHERE id = %s", (user_id,))
        stored_otp = self.cursor.fetchone()[0]
        return stored_otp == otp
        
    def log_query(self, user_id, course, subcourse, training_type, 
                 category_id, question_id, answer_text):
        self.cursor.execute("""
        INSERT INTO query_history (user_id, course, subcourse, training_type, 
                                 category_id, question_id, answer_text)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, course, subcourse, training_type, 
              category_id, question_id, answer_text))
        self.conn.commit()
    
    def get_cached_answer(self, question_id, subcourse, variant):
        self.cursor.execute("""
        SELECT answer_text
        FROM url_answer_cache
        WHERE question_id = %s 
        AND subcourse = %s 
        AND variant = %s 
        AND cached_at > %s
        """, (question_id, subcourse, variant, 
              datetime.now() - timedelta(hours=24)))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def cache_answer(self, question_id, subcourse, variant, url, answer_text):
        self.cursor.execute("""
        INSERT INTO url_answer_cache (question_id, subcourse, variant, url, answer_text)
        VALUES (%s, %s, %s, %s, %s)
        """, (question_id, subcourse, variant, url, answer_text))
        self.conn.commit()
    
    def scrape_answer(self, url, question_id):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            question_selectors = {
                6: lambda soup: soup.find('table', class_='table table-bordered table-striped table-responsive') and "\n".join(
                    f"{row.find_all('td')[0].text.strip()} : {row.find_all('td')[2].text.strip()}"
                    for row in soup.find('table', class_='table table-bordered table-striped table-responsive').find('tbody').find_all('tr')),
                7: ('div', {'class': 'course-duration'}),
                9: lambda soup: soup.find('table', class_='table table-bordered table-striped table-responsive') and "\n".join(
                    f"{row.find_all('td')[0].text.strip()} : {row.find_all('td')[1].text.strip()}"
                    for row in soup.find('table', class_='table table-bordered table-striped table-responsive').find('tbody').find_all('tr')),
                10: lambda soup: soup.find('table', class_='table table-bordered table-striped table-responsive') and "\n".join(
                    f"{row.find_all('td')[0].text.strip()} : {row.find_all('td')[3].text.strip()}"
                    for row in soup.find('table', class_='table table-bordered table-striped table-responsive').find('tbody').find_all('tr')),
                12: lambda soup: soup.find('table', class_='table table-bordered') and 
                               soup.find('table', class_='table table-bordered').find_all('tr')[1].find_all('td')[1].text.strip(),
                13: lambda soup: soup.find('table', class_='table table-bordered') and "\n".join(
                    f"{soup.find('table', class_='table table-bordered').find_all('tr')[i].find_all('td')[0].text.strip().replace('*', '')} : "
                    f"{soup.find('table', class_='table table-bordered').find_all('tr')[i].find_all('td')[1].text.strip().replace('*', '')}"
                    for i in [5, 6, 7]
                ),
                14: ('div', {'class': 'mock-alignment'}),
                15: lambda soup: "Yes" if soup.find('table', class_='table table-bordered') and any(
                    "online" in td.text.lower().split() and ("test" in td.text.lower().split() or "tests" in td.text.lower().split())
                    for row in soup.find('table', class_='table table-bordered').find('tbody').find_all('tr')
                    for td in row.find_all('td')
                ) else "No",
                16: ('div', {'class': 'mock-analysis'}),
                17: ('div', {'class': 'books-provided'}),
                18: ('div', {'class': 'mock-scope'}),
                19: ('div', {'class': 'self-mocks'}),
                20: ('div', {'class': 'other-exams'}),
                21: ('div', {'class': 'video-sessions'}),
                22: ('div', {'class': 'results'}),
                26: ('div', {'class': 'application-help'})
            }
            selector = question_selectors.get(question_id)
            if selector:
                if callable(selector):
                    return selector(soup)
                element = soup.find(*selector)
                if element:
                    return element.text.strip()
            return "No answer found on page"
        except Exception as e:
            logger.error(f"Scraping failed for {url}: {e}")
            return "Unable to retrieve answer at this time"
    
    def query_subcourses(self, course):
        self.cursor.execute("SELECT subcourse FROM subcourses WHERE course = %s AND is_active = TRUE", (course,))
        result = [(row[0], row[0]) for row in self.cursor.fetchall()]
        return result
    
    def query_coursetypes(self, subcourse):
        self.cursor.execute("SELECT coursetype FROM coursetypes WHERE course = %s AND is_active = TRUE", (subcourse,))
        result = [(row[0], row[0]) for row in self.cursor.fetchall()]
        return result
    
    def get_categories(self):
        self.cursor.execute("""
        SELECT id, name
        FROM categories
        WHERE is_active = TRUE
        ORDER BY display_order
        """)
        result = [(row[0], row[1]) for row in self.cursor.fetchall()]
        result.append(('end_chat', 'End Chat'))
        return result
    
    def get_questions(self, category_id):
        self.cursor.execute("""
        SELECT id, question_text
        FROM questions
        WHERE category_id = %s AND is_active = TRUE
        ORDER BY display_order
        """, (category_id,))
        result = [(row[0], row[1]) for row in self.cursor.fetchall()]
        result.append(('back', 'Back'))
        return result
    
    def get_answer(self, question_id, context, db1, db2):
        self.cursor.execute("""
        SELECT source_type, source_detail
        FROM questions
        WHERE id = %s
        """, (question_id,))
        source_type, source_detail = self.cursor.fetchone()
        
        if source_type == 'DB':
            if source_detail == 'coursefee':
                self.cursor.execute("""
                SELECT actual_lumpsum, instalments, first_instalment, second_instalment, third_instalment
                FROM coursefee
                WHERE course = %s AND subcourse = %s AND variant = %s AND city = %s AND is_active = TRUE
                """, (context['course'], context['subcourse'], context['training_type'], context['city']))
                result = self.cursor.fetchone()
                if result:
                    actual_lumpsum, instalments, first_instalment, second_instalment, third_instalment = result
                    self.cursor.execute("SELECT id FROM questions WHERE question_text = %s", ('What is the course fee?',))
                    course_fee_id = self.cursor.fetchone()[0]
                    self.cursor.execute("SELECT id FROM questions WHERE question_text = %s", ('Is there an installment option?',))
                    installment_id = self.cursor.fetchone()[0]
                    
                    if question_id == course_fee_id:
                        answer = f"The course fee for {context['course']} {context['subcourse']} {context['training_type']} in {context['city']} is {actual_lumpsum} for lumpsum payment."
                    elif question_id == installment_id:
                        if instalments and instalments > 0:
                            answer = (
                                f"Total Installments : {instalments}\n"
                                f"First Installment : {first_instalment}\n"
                                f"Second Installment : {second_instalment}\n"
                                f"Third Installment : {third_instalment}"
                            )
                        else:
                            answer = "There is no option for installments."
                    else:
                        answer = "Fee not available."
                else:
                    answer = "Fee not available."
                return answer
            elif source_detail == 'discounts':
                self.cursor.execute("""
                SELECT discounttype, discount_range, discount_amount
                FROM discounts
                WHERE course = %s AND subcourse = %s AND variant = %s AND city = %s AND is_active = TRUE
                """, (context['course'], context['subcourse'], context['training_type'], context['city']))
                results = self.cursor.fetchall()
                self.cursor.execute("SELECT id FROM questions WHERE question_text = %s", ('Are there any discounts?',))
                discounts_id = self.cursor.fetchone()[0]
                self.cursor.execute("SELECT id FROM questions WHERE question_text = %s", ('Is there a scholarship test?',))
                scholarship_id = self.cursor.fetchone()[0]
                
                if question_id == discounts_id:
                    if results:
                        discounts = [f"{row[0]} ({row[1] or row[2]})" for row in results]
                        answer = "Discounts available: " + ", ".join(discounts) + "."
                    else:
                        answer = "No discounts available."
                elif question_id == scholarship_id:
                    scholarship = next((row for row in results if row[0] == 'scholarship test'), None)
                    if scholarship:
                        answer = f"Yes, scholarship test available with discount range: {scholarship[1]}."
                    else:
                        answer = "No scholarship test available."
                else:
                    answer = "No discounts available."
                return answer
            elif source_detail == 'mdl_location_centerdetails':
                address, phone, email = db1.query_centerdetails(context['city'])
                self.cursor.execute("SELECT id FROM questions WHERE question_text = %s", ('Nearest branch location?',))
                nearest_branch_id = self.cursor.fetchone()[0]
                if question_id == nearest_branch_id:
                    answer = f"Nearest branch in {context['city']}: {address}"
                else:
                    answer = f"Contact details for {context['city']}: Phone: {phone}, Email: {email}"
                return answer
            elif source_detail == 'batch_sizes':
                self.cursor.execute("""
                SELECT batch_size
                FROM batch_sizes
                WHERE course = %s AND subcourse = %s AND variant = %s AND city = %s AND is_active = TRUE
                """, (context['course'], context['subcourse'], context['training_type'], context['city']))
                result = self.cursor.fetchone()
                answer = f"The batch size for {context['subcourse']} {context['training_type']} in {context['city']} is {result[0]}." if result else "Batch size not available."
                return answer
            elif source_detail == 'testimonials':
                # Placeholder response; actual video fetching is handled in chatbot_engine.py
                return "Fetching testimonial video..."
            elif source_detail in ['eligibility_criteria', 'exam_dates', 'registration_process', 'score_validity', 'top_b_schools', 'mba_advantages', 'selection_process', 'attempts_allowed']:
                field = source_detail
                self.cursor.execute(f"SELECT {field} FROM exam_info WHERE course = %s", (context['course'],))
                result = self.cursor.fetchone()
                answer = result[0] if result else "Information not available."
                return answer
            elif source_detail.startswith('tbd_'):
                answer = "Answer not available yet. Please check back later."
                return answer
        elif source_type == 'STATIC':
            self.cursor.execute("SELECT answer_text FROM static_answers WHERE question_id = %s", (question_id,))
            answer = self.cursor.fetchone()[0]
            return answer
        elif source_type == 'URL':
            self.cursor.execute("""
            SELECT url
            FROM url_answers
            WHERE question_id = %s AND subcourse = %s AND variant = %s
            """, (question_id, context['subcourse'], context['training_type']))
            result = self.cursor.fetchone()
            if result:
                url = result[0]
                cached_answer = self.get_cached_answer(question_id, context['subcourse'], context['training_type'])
                if cached_answer:
                    return cached_answer
                answer_text = self.scrape_answer(url, question_id)
                self.cache_answer(question_id, context['subcourse'], context['training_type'], url, answer_text)
                return answer_text
            answer = "Answer not available for this course and training type."
            return answer
        answer = "Answer not available."
        return answer
    
    def __del__(self):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()