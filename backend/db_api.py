from fastapi import FastAPI, HTTPException
from config import MYSQL_CREDENTIALS, MSSQL_CREDENTIALS, DB3_CREDENTIALS
from db_connect import MySQLDB, MSSQLDB, DB3
import logging

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize database connections
db1 = MySQLDB(MYSQL_CREDENTIALS)
db2 = MSSQLDB(MSSQL_CREDENTIALS)
db3 = DB3(DB3_CREDENTIALS)

@app.get("/api/cities")
async def get_cities():
    try:
        db1.cursor.execute("SELECT city FROM locations")
        cities = [city[0] for city in db1.cursor.fetchall()]
        return {"success": True, "data": cities}
    except Exception as e:
        logger.error(f"Error fetching cities: {e}")
        return {"success": False, "error": "Failed to fetch cities"}

@app.get("/api/courses/{city}")
async def get_courses(city: str):
    try:
        db1.cursor.execute("SELECT school_courses, college_courses FROM locations WHERE city = %s", (city,))
        result = db1.cursor.fetchone()
        if not result:
            return {"success": True, "data": []}
        
        school_courses = result[0].split(',') if result[0] else []
        college_courses = result[1].split(',') if result[1] else []
        all_courses = list(set(school_courses + college_courses))
        
        valid_courses = []
        for course in all_courses:
            course = course.strip()
            if not course:
                continue
            db1.cursor.execute("SELECT course_status FROM courses WHERE title = %s OR coursename = %s", (course, course))
            course_status = db1.cursor.fetchone()
            if course_status and course_status[0] == 1:
                valid_courses.append(course)
        
        return {"success": True, "data": valid_courses}
    except Exception as e:
        logger.error(f"Error fetching courses for {city}: {e}")
        return {"success": False, "error": "Failed to fetch courses"}

@app.get("/api/subcourses")
async def get_subcourses(course: str):
    try:
        result = db3.query_subcourses(course)
        subcourses = [row[0] for row in result]
        return {"success": True, "data": subcourses}
    except Exception as e:
        logger.error(f"Error fetching subcourses for {course}: {e}")
        return {"success": False, "error": "Failed to fetch subcourses"}

@app.get("/api/coursetypes")
async def get_coursetypes(subcourse: str):
    try:
        result = db3.query_coursetypes(subcourse)
        coursetypes = [row[0] for row in result]
        return {"success": True, "data": coursetypes}
    except Exception as e:
        logger.error(f"Error fetching coursetypes for {subcourse}: {e}")
        return {"success": False, "error": "Failed to fetch coursetypes"}

@app.get("/api/categories")
async def get_categories():
    try:
        result = db3.get_categories()
        categories = [row[1] for row in result]
        return {"success": True, "data": categories}
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return {"success": False, "error": "Failed to fetch categories"}

@app.get("/api/categories_dict")
async def get_categories_dict():
    try:
        result = db3.get_categories()
        category_dict = {row[1]: row[0] for row in result}
        return {"success": True, "data": category_dict}
    except Exception as e:
        logger.error(f"Error fetching categories_dict: {e}")
        return {"success": False, "error": "Failed to fetch categories_dict"}

@app.get("/api/questions")
async def get_questions(category_id: int):
    try:
        result = db3.get_questions(category_id)
        questions = [row[1] for row in result]
        return {"success": True, "data": questions}
    except Exception as e:
        logger.error(f"Error fetching questions for category {category_id}: {e}")
        return {"success": False, "error": "Failed to fetch questions"}

@app.get("/api/questions_dict")
async def get_questions_dict(category_id: int):
    try:
        result = db3.get_questions(category_id)
        question_dict = {row[1]: row[0] for row in result}
        return {"success": True, "data": question_dict}
    except Exception as e:
        logger.error(f"Error fetching questions_dict for category {category_id}: {e}")
        return {"success": False, "error": "Failed to fetch questions_dict"}

@app.get("/api/answer")
async def get_answer(question_id: int, course: str, subcourse: str, training_type: str, city: str):
    try:
        context = {"course": course, "subcourse": subcourse, "training_type": training_type, "city": city}
        answer = db3.get_answer(question_id, context, db1, db2)
        return {"success": True, "data": answer}
    except Exception as e:
        logger.error(f"Error fetching answer for question {question_id}: {e}")
        return {"success": False, "error": "Failed to fetch answer"}