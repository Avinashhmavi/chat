from fastapi import FastAPI, HTTPException
from config import MYSQL_CREDENTIALS, MSSQL_CREDENTIALS, DB3_CREDENTIALS
from db_connect import MySQLDB, MSSQLDB, DB3
import logging
import asyncio

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize database connections
db1 = MySQLDB(MYSQL_CREDENTIALS)
db2 = MSSQLDB(MSSQL_CREDENTIALS)
db3 = DB3(DB3_CREDENTIALS)

@app.on_event("startup")
async def startup_event():
    await db1.init_pool()
    await db3.init_pool()

@app.on_event("shutdown")
async def shutdown_event():
    await db1.close()
    await db3.close()
    db2.close()

@app.get("/api/cities")
async def get_cities():
    try:
        result = await db1.query("SELECT city FROM locations")
        cities = [row[0] for row in result]
        logger.debug(f"Fetched cities: {cities}")
        return {"success": True, "data": cities}
    except Exception as e:
        logger.error(f"Error fetching cities: {e}")
        return {"success": False, "error": "Failed to fetch cities"}

@app.get("/api/courses/{city}")
async def get_courses(city: str):
    try:
        logger.debug(f"Fetching courses for city: {city}")
        result = await db1.query("SELECT school_courses, college_courses FROM locations WHERE city = %s", (city,))
        if not result:
            logger.info(f"No location found for city: {city}")
            return {"success": True, "data": []}
        school_courses = result[0][0].split(',') if result[0][0] else []
        college_courses = result[0][1].split(',') if result[0][1] else []
        all_courses = list(set(school_courses + college_courses))
        all_courses = [course.strip() for course in all_courses if course.strip()]
        logger.debug(f"Raw courses for {city}: {all_courses}")
        if not all_courses:
            logger.info(f"No courses found for city: {city}")
            return {"success": True, "data": []}
        placeholders = ','.join(['%s'] * len(all_courses))
        query = f"SELECT id, title, coursename FROM courses WHERE course_status = 1 AND (title IN ({placeholders}) OR coursename IN ({placeholders}))"
        logger.debug(f"Executing course query: {query} with params: {all_courses + all_courses}")
        course_rows = await db1.query(query, all_courses + all_courses)
        valid_courses = []
        for course in all_courses:
            for row in course_rows:
                course_id, title, coursename = row
                if course == coursename:
                    valid_courses.append({"name": coursename, "id": course_id})
                    break
                elif course == title:
                    valid_courses.append({"name": course, "id": course_id})
                    break
        logger.debug(f"Valid courses for {city}: {valid_courses}")
        return {"success": True, "data": valid_courses}
    except Exception as e:
        logger.error(f"Error fetching courses for {city}: {e}")
        return {"success": False, "error": f"Failed to fetch courses: {str(e)}"}

@app.get("/api/city_data/{city}")
async def get_city_data(city: str):
    try:
        logger.debug(f"Fetching city data for: {city}")
        cities_result = await db1.query("SELECT city FROM locations")
        cities = [row[0] for row in cities_result]
        logger.debug(f"All cities: {cities}")
        valid = city in cities
        courses = []
        if valid:
            result = await db1.query("SELECT school_courses, college_courses FROM locations WHERE city = %s", (city,))
            logger.debug(f"Location query result for {city}: {result}")
            if result:
                school_courses = result[0][0].split(',') if result[0][0] else []
                college_courses = result[0][1].split(',') if result[0][1] else []
                all_courses = list(set(school_courses + college_courses))
                all_courses = [course.strip() for course in all_courses if course.strip()]
                logger.debug(f"Raw courses for {city}: {all_courses}")
                if all_courses:
                    placeholders = ','.join(['%s'] * len(all_courses))
                    query = f"SELECT id, title, coursename FROM courses WHERE course_status = 1 AND (title IN ({placeholders}) OR coursename IN ({placeholders}))"
                    logger.debug(f"Executing course query: {query} with params: {all_courses + all_courses}")
                    course_rows = await db1.query(query, all_courses + all_courses)
                    logger.debug(f"Course query result: {course_rows}")
                    for course in all_courses:
                        for row in course_rows:
                            course_id, title, coursename = row
                            if course == coursename:
                                courses.append({"name": coursename, "id": course_id})
                                break
                            elif course == title:
                                courses.append({"name": course, "id": course_id})
                                break
                else:
                    logger.info(f"No courses found for city: {city}")
            else:
                logger.info(f"No location found for city: {city}")
        else:
            logger.warning(f"Invalid city: {city}")
        # Deduplicate courses by id
        seen_ids = set()
        unique_courses = []
        for course in courses:
            if course["id"] not in seen_ids:
                unique_courses.append(course)
                seen_ids.add(course["id"])
        logger.debug(f"Deduplicated courses for {city}: {unique_courses}")
        response = {"success": True, "data": {"valid": valid, "cities": cities, "courses": unique_courses}}
        logger.debug(f"City data response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error fetching city data for {city}: {e}")
        return {"success": False, "error": f"Failed to fetch city data: {str(e)}"}

@app.get("/api/course_variants")
async def get_course_variants(course_id: int, subcourse: str):
    try:
        logger.debug(f"Fetching course variants for course_id={course_id}, subcourse={subcourse}")
        query = "SELECT Coursesubvariant FROM coursedetails WHERE Courseid = %s AND Coursesubvariant LIKE %s"
        result = await db1.query(query, (course_id, f"%{subcourse}%"))
        variants = [row[0] for row in result]
        logger.debug(f"Course variants: {variants}")
        return {"success": True, "data": variants}
    except Exception as e:
        logger.error(f"Error fetching course variants for course_id={course_id}, subcourse={subcourse}: {e}")
        return {"success": False, "error": f"Failed to fetch course variants: {str(e)}"}

@app.get("/api/subcourses")
async def get_subcourses(course: str):
    try:
        logger.debug(f"Fetching subcourses for course: {course}")
        result = await db3.query_subcourses(course)
        subcourses = [row[0] for row in result]
        logger.debug(f"Subcourses: {subcourses}")
        return {"success": True, "data": subcourses}
    except Exception as e:
        logger.error(f"Error fetching subcourses for {course}: {e}")
        return {"success": False, "error": f"Failed to fetch subcourses: {str(e)}"}

@app.get("/api/categories")
async def get_categories():
    try:
        logger.debug("Fetching categories")
        result = await db3.get_categories()
        categories = [row[1] for row in result]
        logger.debug(f"Categories: {categories}")
        return {"success": True, "data": categories}
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return {"success": False, "error": f"Failed to fetch categories: {str(e)}"}

@app.get("/api/categories_dict")
async def get_categories_dict():
    try:
        logger.debug("Fetching categories_dict")
        result = await db3.get_categories()
        category_dict = {row['name']: row['id'] for row in result}
        logger.debug(f"Categories dict: {category_dict}")
        return {"success": True, "data": category_dict}
    except Exception as e:
        logger.error(f"Error fetching categories_dict: {e}")
        return {"success": False, "error": f"Failed to fetch categories_dict: {str(e)}"}

@app.get("/api/questions")
async def get_questions(category_id: int):
    try:
        logger.debug(f"Fetching questions for category_id: {category_id}")
        result = await db3.get_questions(category_id)
        questions = [row[1] for row in result]
        logger.debug(f"Questions: {questions}")
        return {"success": True, "data": questions}
    except Exception as e:
        logger.error(f"Error fetching questions for category {category_id}: {e}")
        return {"success": False, "error": f"Failed to fetch questions: {str(e)}"}

@app.get("/api/questions_dict")
async def get_questions_dict(category_id: int):
    try:
        logger.debug(f"Fetching questions_dict for category_id: {category_id}")
        result = await db3.get_questions(category_id)
        question_dict = {row['question_text']: row['id'] for row in result}
        logger.debug(f"Questions dict: {question_dict}")
        return {"success": True, "data": question_dict}
    except Exception as e:
        logger.error(f"Error fetching questions_dict for category {category_id}: {e}")
        return {"success": False, "error": f"Failed to fetch questions_dict: {str(e)}"}

@app.get("/api/answer")
async def get_answer(question_id: int, course: str, subcourse: str, training_type: str, city: str):
    try:
        logger.debug(f"Fetching answer for question_id={question_id}, course={course}, subcourse={subcourse}, training_type={training_type}, city={city}")
        context = {"course": course, "subcourse": subcourse, "training_type": training_type, "city": city}
        answer = await db3.get_answer(question_id, context, db1, db2)
        logger.debug(f"Answer: {answer}")
        return {"success": True, "data": answer}
    except Exception as e:
        logger.error(f"Error fetching answer for question {question_id}: {e}")
        return {"success": False, "error": f"Failed to fetch answer: {str(e)}"}