from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import MYSQL_CREDENTIALS, MSSQL_CREDENTIALS, DB3_CREDENTIALS
from db_connect import MySQLDB, MSSQLDB, DB3
from chatbot_engine import ChatbotEngine
import requests
import logging
import time

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# Initialize database connections for DB3 (used directly for user management)
db1 = MySQLDB(MYSQL_CREDENTIALS)
db2 = MSSQLDB(MSSQL_CREDENTIALS)
db3 = DB3(DB3_CREDENTIALS)

# Initialize chatbot engine
chatbot = ChatbotEngine(db1, db2, db3)

# Database API base URL
DB_API_URL = "http://localhost:8001"

# Pydantic models for request validation
class RegisterRequest(BaseModel):
    name: str
    mobile: str

class VerifyOTPRequest(BaseModel):
    user_id: int
    otp: str

class ChatRequest(BaseModel):
    state: str = "start"
    input: str = ""
    user_id: int | None = None

# Helper function for API calls with retries
def call_db_api(endpoint, params=None, retries=3, backoff=1):
    url = f"{DB_API_URL}{endpoint}"
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            if not data.get("success"):
                logger.error(f"API error at {url}: {data.get('error')}")
                raise HTTPException(status_code=500, detail=data.get("error"))
            return data["data"]
        except requests.RequestException as e:
            logger.error(f"API call failed at {url}: {e}")
            if attempt == retries - 1:
                raise HTTPException(status_code=503, detail="Database API unavailable")
            time.sleep(backoff * (2 ** attempt))

@app.post("/register")
async def register(data: RegisterRequest):
    try:
        name = data.name.strip()
        mobile = data.mobile.strip()
        logger.debug('Parsed name: %s, mobile: %s', name, mobile)

        if not name or not mobile or not mobile.isdigit() or len(mobile) != 10:
            logger.error('Validation failed: name=%s, mobile=%s', name, mobile)
            raise HTTPException(status_code=400, detail="Valid name and 10-digit mobile are required")

        user_id, otp = chatbot.register_user(name, mobile, 'Unknown')
        logger.info('Registration successful for user_id: %s', user_id)
        return {"success": True, "message": "Registration successful. OTP sent", "otp": otp, "user_id": user_id}
    
    except Exception as e:
        logger.error('Error processing request: %s', str(e))
        raise HTTPException(status_code=400, detail="Invalid request format")

@app.post("/verify-otp")
async def verify_otp(data: VerifyOTPRequest):
    try:
        logger.debug('Received OTP verification data: %s', data.dict())
        if not data.user_id or not data.otp:
            logger.error('User ID or OTP missing: user_id=%s, otp=%s', data.user_id, data.otp)
            raise HTTPException(status_code=400, detail="User ID and OTP are required")
        if chatbot.verify_otp(data.user_id, data.otp):
            logger.info('OTP verified for user_id: %s', data.user_id)
            return {"success": True, "message": "OTP verified successfully", "user_id": data.user_id}
        logger.warning('Invalid OTP for user_id: %s', data.user_id)
        raise HTTPException(status_code=400, detail="Invalid OTP")
    except Exception as e:
        logger.error('Error verifying OTP: %s', str(e))
        raise HTTPException(status_code=400, detail="Invalid request format")

@app.post("/chat")
async def chat(data: ChatRequest):
    try:
        logger.debug('Received chat data: %s', data.dict())
        state = data.state
        user_input = data.input
        user_id = data.user_id

        if state == 'start':
            # Fetch cities via API
            city_options = call_db_api("/api/cities")
            logger.debug('Fetched cities: %s', city_options)
            if not city_options:
                logger.error('No cities found')
                return {"response": "No cities available. Please contact support.", "options": [], "next_state": "start"}
            return {
                "response": f"Hi, <user>! I'm TIME Instant Neural Assistant (TINA) here to assist you today.\n\nWhat city are you from?",
                "options": city_options,
                "next_state": "city_selected"
            }

        elif state == 'city_selected':
            selected_city = user_input
            # Validate city via API
            valid_cities = call_db_api("/api/cities")
            logger.debug('Valid cities: %s', valid_cities)
            if selected_city not in valid_cities:
                return {
                    "response": "Invalid city. Please select a valid city.",
                    "options": valid_cities,
                    "next_state": "city_selected"
                }
            chatbot.set_context(user_id, {'city': selected_city})
            
            # Fetch courses for city via API
            courses = call_db_api(f"/api/courses/{selected_city}")
            logger.debug('Fetched courses for %s: %s', selected_city, courses)
            if not courses:
                return {
                    "response": f"No active courses available for {selected_city}. Please select another city.",
                    "options": valid_cities,
                    "next_state": "city_selected"
                }

            return {
                "response": f"You selected {selected_city}. Which course are you looking for?",
                "options": courses,
                "next_state": "course_selected"
            }

        elif state == 'course_selected':
            selected_course = user_input
            chatbot.set_context(user_id, {'course': selected_course})
            # Fetch subcourses via API
            subcourse_options = call_db_api("/api/subcourses", params={"course": selected_course})
            return {
                "response": f"Which {selected_course} Exam year are you looking for?",
                "options": subcourse_options,
                "next_state": "subcourse_selected"
            }

        elif state == 'subcourse_selected':
            selected_subcourse = user_input
            chatbot.set_context(user_id, {'subcourse': selected_subcourse})
            # Fetch coursetypes via API
            coursetype_options = call_db_api("/api/coursetypes", params={"subcourse": selected_subcourse})
            return {
                "response": "What type of training would you like?",
                "options": coursetype_options,
                "next_state": "training_type_selected"
            }

        elif state == 'training_type_selected':
            selected_training_type = user_input
            chatbot.set_context(user_id, {'training_type': selected_training_type})
            # Fetch categories via API
            category_options = call_db_api("/api/categories")
            return {
                "response": "How can I assist you further?",
                "options": category_options,
                "next_state": "category_selected"
            }

        elif state == 'category_selected':
            if not user_input:
                category_options = call_db_api("/api/categories")
                return {
                    "response": "How can I assist you further?",
                    "options": category_options,
                    "next_state": "category_selected"
                }

            selected_category = user_input
            category_dict = call_db_api("/api/categories_dict")
            if selected_category == 'End Chat':
                return {
                    "response": "Goodbye! If you need help, feel free to reach out again.",
                    "options": [],
                    "next_state": "start"
                }
            category_id = category_dict.get(selected_category)
            if not category_id:
                category_options = call_db_api("/api/categories")
                return {
                    "response": "Invalid category. How can I assist you further?",
                    "options": category_options,
                    "next_state": "category_selected"
                }
            questions = call_db_api("/api/questions", params={"category_id": category_id})
            chatbot.set_context(user_id, {'category_id': category_id})
            return {
                "response": "Please select a question:",
                "options": questions,
                "next_state": "question_selected"
            }

        elif state == 'question_selected':
            selected_question = user_input
            context = chatbot.get_context(user_id)
            question_dict = call_db_api("/api/questions_dict", params={"category_id": context['category_id']})
            if selected_question == 'Back':
                category_options = call_db_api("/api/categories")
                return {
                    "response": "How can I assist you further?",
                    "options": category_options,
                    "next_state": "category_selected"
                }
            question_id = question_dict.get(selected_question)
            if not question_id:
                questions = call_db_api("/api/questions", params={"category_id": context['category_id']})
                return {
                    "response": "Invalid question. Please select a valid question.",
                    "options": questions,
                    "next_state": "question_selected"
                }
            answer = call_db_api("/api/answer", params={
                "question_id": question_id,
                "course": context['course'],
                "subcourse": context['subcourse'],
                "training_type": context['training_type'],
                "city": context['city']
            })
            db3.log_query(user_id, context['course'], context['subcourse'], context['training_type'], context['category_id'], question_id, answer)
            
            questions = call_db_api("/api/questions", params={"category_id": context['category_id']})
            return {
                "response": answer,
                "options": questions,
                "next_state": "question_selected"
            }

        return {
            "response": "Something went wrong. Let’s start over.",
            "options": ["Restart"],
            "next_state": "start"
        }

    except Exception as e:
        logger.error('Error processing chat request: %s', str(e))
        category_options = call_db_api("/api/categories")
        return {
            "response": "Sorry, something went wrong. Let’s get back on track. How can I assist you further?",
            "options": category_options,
            "next_state": "category_selected"
        }