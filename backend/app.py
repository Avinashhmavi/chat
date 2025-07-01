from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from config import MYSQL_CREDENTIALS
from db_connect import MySQLDB, get_cities, get_courses, get_subcourses, get_training_types, get_categories, save_user_details, get_qa_for_category
from chatbot_engine import ChatbotEngine
from rag_system import RAGSystem
import logging
import random
import mysql.connector
from fastapi import Depends
import hashlib
import os
import re

app = FastAPI()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

db1 = MySQLDB(MYSQL_CREDENTIALS)
chatbot = ChatbotEngine(db1)
rag_system = RAGSystem(db1)

@app.get("/")
async def read_root():
    """Serve the main HTML file"""
    return FileResponse("../frontend/index.html")

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Server is running!", "demo_mode": getattr(app.state, 'demo_mode', False)}

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

def make_node_id(label, db_id=None):
    if db_id is not None:
        return int(db_id)
    # fallback: hash the label for uniqueness
    return int(hashlib.sha256(label.encode('utf-8')).hexdigest(), 16) % (10 ** 8)

def get_path_for_state(context, state, user_input=None):
    """
    Returns a list of node IDs from course to current node, matching the frontend tree structure.
    """
    path = []
    # Course (always start path with course_id)
    if 'course_id' in context:
        path.append(int(context['course_id']))
    # Subcourse (use hash if no DB id)
    if 'subcourse' in context:
        path.append(make_node_id(context['subcourse']))
    # Variant (training_type)
    if 'training_type' in context:
        path.append(make_node_id(context['training_type']))
    # Category
    if 'category_id' in context:
        path.append(int(context['category_id']))
    # Question
    if state == 'question_selected' and user_input:
        question_dict = context.get('question_dict')
        if question_dict and user_input in question_dict:
            path.append(int(question_dict[user_input]))
        else:
            path.append(make_node_id(user_input))
    # Result/testimonial
    if state in ('result_selected', 'testimonial_response') and user_input:
        path.append(make_node_id(user_input))
    return path
class RAGChatRequest(BaseModel):
    message: str
    user_id: int | None = None

@app.post("/register")
async def register(data: RegisterRequest):
    try:
        name = data.name.strip()
        mobile = data.mobile.strip()
        if not name or not mobile or not mobile.isdigit() or len(mobile) != 10:
            logger.error('Validation failed: name=%s, mobile=%s', name, mobile)
            raise HTTPException(status_code=400, detail="Valid name and 10-digit mobile are required")
        user_id, otp = await chatbot.register_user(name, mobile, 'Unknown')
        logger.info(f'Registration successful for user_id: {user_id}')
        return {"success": True, "message": "Registration successful", "otp": otp, "user_id": user_id}
    except Exception as e:
        logger.error(f'Error processing registration: {str(e)}')
        raise HTTPException(status_code=400, detail="Invalid request format")

@app.post("/verify-otp")
async def verify_otp(data: VerifyOTPRequest):
    try:
        if not data.user_id or not data.otp:
            logger.error(f'User ID or OTP missing: user_id={data.user_id}, otp={data.otp}')
            raise HTTPException(status_code=400, detail="User ID and OTP are required")
        if await chatbot.verify_otp(data.user_id, data.otp):
            logger.info(f'OTP verified for user_id: {data.user_id}')
            return {"success": True, "message": "OTP verified successfully", "user_id": data.user_id}
        logger.error(f'Invalid OTP for user_id: {data.user_id}')
        raise HTTPException(status_code=400, detail="Invalid OTP")
    except Exception as e:
        logger.error(f'Error verifying OTP: {e}')
        raise HTTPException(status_code=400, detail="Invalid request format")

@app.post("/chat")
async def chat(data: ChatRequest):
    try:
        state = data.state
        user_input = data.input.strip()
        user_id = data.user_id

        if state == "start":
            return {
                "response": "Please enter your city.",
                "options": [],
                "next_state": "city_selected",
                "path": []
            }

        elif state == "city_selected":
            selected_city = user_input.strip().encode('utf-8').decode('utf-8')
            nearest_center_response = await call_db_api("/api/find_nearest_center", params={"city": selected_city})
            nearest_center = nearest_center_response.get("nearest_center", selected_city) if nearest_center_response.get("success") else selected_city
            city_data = await call_db_api("/api/city_data", params={"city": nearest_center})
            if not city_data.get("data", {}).get("valid"):
                nearest_center = "Hyderabad"
                city_data = await call_db_api("/api/city_data", params={"city": nearest_center})
                if not city_data.get("data", {}).get("valid"):
                    logger.error(f"Hyderabad city data invalid: {city_data}")
                    return {
                        "response": "Sorry, something went wrong. Please try again later.",
                        "options": [],
                        "next_state": "start",
                        "path": []
                    }
                chatbot.set_context(user_id, {"city": nearest_center})
                if not city_data.get("data", {}).get("courses"):
                    return {
                        "response": f"No active courses available for {nearest_center}. Please try again later.",
                        "options": [],
                        "next_state": "start",
                        "path": []
                    }
                return {
                    "response": f"Sorry, we couldn't find your city. We've mapped you to our Hyderabad center. Which course are you looking for?",
                    "options": [course["name"] for course in city_data.get("data", {}).get("courses", [])],
                    "next_state": "course_selected",
                    "back_options": ["Back to cities"],
                    "path": get_path_for_state({}, state, user_input)
                }
            chatbot.set_context(user_id, {"city": nearest_center})
            if not city_data.get("data", {}).get("courses"):
                return {
                    "response": f"No active courses available for {nearest_center}. Please enter another city.",
                    "options": [],
                    "next_state": "city_selected",
                    "path": get_path_for_state({}, state, user_input)
                }
            return {
                "response": f"You selected: {nearest_center}. Which course are you looking for?",
                "options": [course["name"] for course in city_data.get("data", {}).get("courses", [])],
                "next_state": "course_selected",
                "back_options": ["Back to cities"],
                "path": get_path_for_state({}, state, user_input)
            }

        elif state == "course_selected":
            if user_input == "Back to cities":
                return {
                    "response": "Please enter your city.",
                    "options": [],
                    "next_state": "city_selected",
                    "path": []
                }
            selected_course = user_input
            context = chatbot.get_context(user_id)
            city_data = await call_db_api("/api/city_data", params={"city": context.get('city', '')})
            course_dict = {course["name"]: course["id"] for course in city_data.get("data", {}).get("courses", [])}
            course_id = course_dict.get(selected_course)
            if not course_id:
                return {
                    "response": "Invalid course. Please select a valid course.",
                    "options": [course["name"] for course in city_data.get("data", {}).get("courses", [])],
                    "next_state": "course_selected",
                    "back_options": ["Back to cities"],
                    "path": get_path_for_state(context, state, user_input)
                }
            chatbot.set_context(user_id, {"course": selected_course, "course_id": course_id})
            subcourse_options = await call_db_api("/api/subcourses", params={"course": selected_course})
            if not subcourse_options.get("data"):
                logger.error(f"No subcourses found for course: {selected_course}")
                return {
                    "response": f"No exam years available for {selected_course}. Please select another course.",
                    "options": [course["name"] for course in city_data.get("data", {}).get("courses", [])],
                    "next_state": "course_selected",
                    "back_options": ["Back to cities"],
                    "path": get_path_for_state(context, state, user_input)
                }
            return {
                "response": f"Which {selected_course} exam year are you looking for?",
                "options": subcourse_options.get("data", []),
                "next_state": "subcourse_selected",
                "back_options": ["Back to courses", "Main page"],
                "path": get_path_for_state(context, state, user_input)
            }

        elif state == "subcourse_selected":
            if user_input in ["Back to courses", "Main page"]:
                context = chatbot.get_context(user_id)
                city_data = await call_db_api("/api/city_data", params={"city": context.get('city', '')})
                return {
                    "response": f"Which course are you looking for in {context.get('city', '')}?",
                    "options": [course["name"] for course in city_data.get("data", {}).get("courses", [])],
                    "next_state": "course_selected",
                    "back_options": ["Back to cities"],
                    "path": get_path_for_state(context, state, user_input)
                }
            selected_subcourse = user_input
            context = chatbot.get_context(user_id)
            course_id = context.get("course_id")
            subcourse_options = await call_db_api("/api/subcourses", params={"course": context.get("course", "")})
            if selected_subcourse not in subcourse_options.get("data", []):
                return {
                    "response": f"Invalid exam year. Please select a valid {context.get('city', '')} exam year.",
                    "options": subcourse_options.get("data", []),
                    "next_state": "subcourse_selected",
                    "back_options": ["Back to courses", "Main page"],
                    "path": get_path_for_state(context, state, user_input)
                }
            chatbot.set_context(user_id, {"subcourse": selected_subcourse})
            variant_options = await call_db_api("/api/course_variants", params={"course_id": course_id, "subcourse": selected_subcourse})
            if not variant_options.get("data"):
                logger.error(f"No course variants found for subcourse: {selected_subcourse}, course_id: {course_id}")
                return {
                    "response": f"No variants available for {selected_subcourse}. Please select another exam year.",
                    "options": subcourse_options.get("data", []),
                    "next_state": "subcourse_selected",
                    "back_options": ["Back to courses", "Main page"],
                    "path": get_path_for_state(context, state, user_input)
                }
            return {
                "response": "What course variant would you like?",
                "options": variant_options.get("data", []),
                "next_state": "training_type_selected",
                "back_options": ["Back to exam years", "Main page"],
                "path": get_path_for_state(context, state, user_input)
            }

        elif state == "training_type_selected":
            if user_input == "Back to exam years":
                context = chatbot.get_context(user_id)
                subcourse_options = await call_db_api("/api/subcourses", params={"course": context.get("course", "")})
                return {
                    "response": f"Which {context.get('course', '')} exam year are you looking for?",
                    "options": subcourse_options.get("data", []),
                    "next_state": "subcourse_selected",
                    "back_options": ["Back to courses", "Main page"],
                    "path": get_path_for_state(context, state, user_input)
                }
            if user_input == "Main page":
                context = chatbot.get_context(user_id)
                city_data = await call_db_api("/api/city_data", params={"city": context.get('city', '')})
                return {
                    "response": f"Which course are you looking for in {context.get('city', '')}?",
                    "options": [course["name"] for course in city_data.get("data", {}).get("courses", [])],
                    "next_state": "course_selected",
                    "back_options": ["Back to cities"],
                    "path": get_path_for_state(context, state, user_input)
                }
            selected_variant = user_input
            context = chatbot.get_context(user_id)
            variant_options = await call_db_api("/api/course_variants", params={"course_id": context.get("course_id"), "subcourse": context.get("subcourse")})
            if selected_variant not in variant_options.get("data", []):
                return {
                    "response": f"Invalid variant. Please select a valid variant for {context.get('subcourse', '')}.",
                    "options": variant_options.get("data", []),
                    "next_state": "training_type_selected",
                    "back_options": ["Back to exam years", "Main page"],
                    "path": get_path_for_state(context, state, user_input)
                }
            chatbot.set_context(user_id, {"training_type": selected_variant})
            category_options = await call_db_api("/api/categories")
            if not category_options.get("data"):
                logger.error("No categories found")
                return {
                    "response": "No categories available. Let's start over.",
                    "options": [],
                    "next_state": "start",
                    "path": get_path_for_state({}, state, user_input)
                }
            return {
                "response": "How can I assist you further?",
                "options": category_options.get("data", []),
                "next_state": "category_selected",
                "back_options": ["Back to variants", "Main page"],
                "path": get_path_for_state(context, state, user_input)
            }

        elif state == "category_selected":
            if user_input == "Back to variants":
                context = chatbot.get_context(user_id)
                variant_options = await call_db_api("/api/course_variants", params={"course_id": context.get("course_id"), "subcourse": context.get("subcourse")})
                return {
                    "response": "What course variant would you like?",
                    "options": variant_options.get("data", []),
                    "next_state": "training_type_selected",
                    "back_options": ["Back to exam years", "Main page"],
                    "path": get_path_for_state(context, "category_selected", user_input)
                }
            if user_input == "Main page":
                context = chatbot.get_context(user_id)
                city_data = await call_db_api("/api/city_data", params={"city": context.get('city', '')})
                return {
                    "response": f"Which course are you looking for in {context.get('city', '')}?",
                    "options": [course["name"] for course in city_data.get("data", {}).get("courses", [])],
                    "next_state": "course_selected",
                    "back_options": ["Back to cities"],
                    "path": get_path_for_state(context, "category_selected", user_input)
                }
            if not user_input:
                category_options = await call_db_api("/api/categories")
                context = chatbot.get_context(user_id)
                return {
                    "response": "How can I assist you further?",
                    "options": category_options.get("data", []),
                    "next_state": "category_selected",
                    "back_options": ["Back to variants", "Main page"],
                    "path": get_path_for_state(context, "category_selected", user_input)
                }
            selected_category = user_input
            category_dict = await call_db_api("/api/categories_dict")
            if selected_category.upper() == "END_CHAT":
                return {
                    "response": "Goodbye! If you need help, feel free to reach out again.",
                    "options": [],
                    "next_state": "start",
                    "path": []
                }
            category_id = category_dict.get("data", {}).get(selected_category)
            if not category_id:
                logger.error(f"Invalid category selected: {selected_category}")
                category_options = await call_db_api("/api/categories")
                context = chatbot.get_context(user_id)
                return {
                    "response": "Invalid category. How can I assist you further?",
                    "options": category_options.get("data", []),
                    "next_state": "category_selected",
                    "back_options": ["Back to variants", "Main page"],
                    "path": get_path_for_state(context, "category_selected", user_input)
                }
            chatbot.set_context(user_id, {"category_id": category_id})
            context = chatbot.get_context(user_id)
            questions = await call_db_api("/api/questions", params={"category_id": category_id})
            return {
                "response": "Please select a question.",
                "options": questions.get("data", []),
                "next_state": "question_selected",
                "back_options": ["Back to categories", "Main page"],
                "path": get_path_for_state(context, "category_selected", user_input)
            }

        elif state == "question_selected":
            selected_question = user_input
            context = chatbot.get_context(user_id)
            if selected_question == "Back to categories":
                category_options = await call_db_api("/api/categories")
                context = chatbot.get_context(user_id)
                return {
                    "response": "How can I assist you further?",
                    "options": category_options.get("data", []),
                    "next_state": "category_selected",
                    "back_options": ["Back to variants", "Main page"],
                    "path": get_path_for_state(context, "question_selected", user_input)
                }
            elif selected_question.upper() == "BACK":
                category_options = await call_db_api("/api/categories")
                context = chatbot.get_context(user_id)
                return {
                    "response": "How can I assist you further?",
                    "options": category_options.get("data", []),
                    "next_state": "category_selected",
                    "back_options": ["Back to variants", "Main page"],
                    "path": get_path_for_state(context, "question_selected", user_input)
                }
            elif selected_question == "Main page":
                context = chatbot.get_context(user_id)
                city_data = await call_db_api("/api/city_data", params={"city": context.get('city', '')})
                return {
                    "response": f"Which course are you looking for in {context.get('city', '')}?",
                    "options": [course["name"] for course in city_data.get("data", {}).get("courses", [])],
                    "next_state": "course_selected",
                    "back_options": ["Back to cities"],
                    "path": get_path_for_state(context, "question_selected", user_input)
                }
            question_dict = await call_db_api("/api/questions_dict", params={"category_id": context.get("category_id")})
            chatbot.set_context(user_id, {"question_dict": question_dict.get("data", {})})
            context = chatbot.get_context(user_id)
            question_id = question_dict.get("data", {}).get(selected_question)
            if not question_id:
                questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                return {
                    "response": "Invalid question. Please select a valid question.",
                    "options": questions.get("data", []),
                    "next_state": "question_selected",
                    "back_options": ["Back to categories", "Main page"],
                    "path": get_path_for_state(context, "question_selected", user_input)
                }

            if question_id == 30:
                city = context.get("city", "").strip()
                html_response = f'<div class="prompt-item"><a href="https://www.time4education.com/local/locationcms/location_directors.php?city={city}" class="prompt-link" target="_blank"><i class="fas fa-link"></i>All Center details for {city}</a></div>'
                await db1.log_query(
                    user_id,
                    context.get("course"),
                    context.get("subcourse"),
                    context.get("training_type"),
                    context.get("category_id"),
                    question_id,
                    html_response
                )
                questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                return {
                    "response": html_response,
                    "options": questions.get("data", []),
                    "next_state": "question_selected",
                    "back_options": ["Back to categories", "Main page"]
                }

            if question_id == 35:
                course_id = context.get("course_id")
                course_name = context.get("course")
                query = """
                    SELECT applink, telegramlink, whatsapplink 
                    FROM courses 
                    WHERE id = %s AND course_status = 1
                """
                link_result = await db1.query(query, (course_id,))
                if link_result:
                    links = link_result[0]
                    applink = links['applink'] or '#'
                    telegramlink = links['telegramlink'] or '#'
                    whatsapplink = links['whatsapplink'] or '#'
                    html_response = (
                        f"<p>Yes, <a href='{applink}' target='_blank'>{course_name} APP</a> is our application.</p>"
                        f"<p>The link to the Telegram channel is: <a href='{telegramlink}' target='_blank'>TIME {course_name} Telegram Channel</a></p>"
                        f"<p>And our WhatsApp channel is: <a href='{whatsapplink}' target='_blank'>{course_name} WhatsApp Channel</a></p>"
                    )
                else:
                    html_response = "Sorry, no app or social media links are available for this course."
                await db1.log_query(
                    user_id,
                    context.get("course"),
                    context.get("subcourse"),
                    context.get("training_type"),
                    context.get("category_id"),
                    question_id,
                    html_response
                )
                questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                return {
                    "response": html_response,
                    "options": questions.get("data", []),
                    "next_state": "question_selected",
                    "back_options": ["Back to categories", "Main page"]
                }

            if context.get("category_id") == 8:
                question_columns = {
                    38: "eligibility_criteria",
                    39: "exam_dates",
                    40: "registration_process",
                    41: "score_validity",
                    42: "top_b_schools",
                    43: "mba_advantages",
                    44: "selection_process",
                    45: "attempts_allowed"
                }
                column = question_columns.get(question_id)
                if column:
                    query = f"""
                        SELECT `{column}`
                        FROM exam_info
                        WHERE course LIKE %s
                        LIMIT 1
                    """
                    course_param = f"%{context.get('course', '')}%"
                    try:
                        async with db1.get_cursor() as cursor:
                            await cursor.execute(query, (course_param,))
                            result = await cursor.fetchone()
                            if result and result.get(column):
                                answer = result.get(column)
                                await db1.log_query(
                                    user_id,
                                    context.get("course"),
                                    context.get("subcourse"),
                                    context.get("training_type"),
                                    context.get("category_id"),
                                    question_id,
                                    answer
                                )
                                questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                                return {
                                    "response": answer,
                                    "options": questions.get("data", []),
                                    "next_state": "question_selected",
                                    "back_options": ["Back to categories", "Main page"]
                                }
                            logger.error(f"No data found for course: {context.get('course', '')}")
                    except Exception as e:
                        logger.error(f"Error fetching exam_info: {e}")
                else:
                    logger.error(f"Invalid question_id: {question_id} for category_id 8")
                questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                return {
                    "response": "No information found for this question.",
                    "options": questions.get("data", []),
                    "next_state": "question_selected",
                    "back_options": ["Back to categories", "Main page"]
                }            
                        
            if question_id == 21:
                course_content = await db1.get_course_content(context.get("course_id"), context.get("course"))
                if not course_content:
                    questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                    return {
                        "response": "No results found for this course.",
                        "options": questions.get("data", []),
                        "next_state": "question_selected",
                        "back_options": ["Back to categories", "Main page"]
                    }
                seen_subtitles = set()
                unique_content = []
                for item in course_content:
                    subtitle = item['Subtitle'].strip()
                    if subtitle not in seen_subtitles:
                        seen_subtitles.add(subtitle)
                        unique_content.append(item)
                options = [item['Subtitle'] for item in unique_content]
                context["course_content"] = unique_content
                chatbot.set_context(user_id, context)
                return {
                    "response": "Please select a result to view:",
                    "options": options,
                    "next_state": "result_selected",
                    "back_options": ["Back to questions", "Main page"]
                }
   
            elif question_id == 1:
                try:
                    price_data = await call_db_api("/api/course_price", params={"variant": context.get("training_type", "")})
                    questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                    price = price_data.get("data", {}).get("Price")
                    offer_price = price_data.get("data", {}).get("OfferPrice")
                    if price is not None and price.strip():
                        html_response = f"<div class='scholarship-details'><p>Fees details for {context.get('training_type', '')}:</p>"
                        html_response += f"<p>Price: ₹{price}</p>"
                        if offer_price is not None and offer_price.strip():
                            html_response += f"<p>Offer Price: ₹{offer_price}</p>"
                        html_response += "</div>"
                        await db1.log_query(user_id, context.get("course"), context.get("subcourse"), context.get("training_type"), context.get("category_id", ""), question_id, html_response)
                        return {
                            "response": html_response,
                            "options": questions.get("data", []),
                            "next_state": "question_selected",
                            "back_options": ["Back to categories", "Main page"]
                        }
                    else:
                        html_response = "<div class='scholarship-details'><p>Price information is not available for this course.</p></div>"
                        questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                        return {
                            "response": html_response,
                            "options": questions.get("data", []),
                            "next_state": "question_selected",
                            "back_options": ["Back to categories", "Main page"]
                        }
                except Exception as e:
                    logger.error(f"Error fetching price for variant {context.get('training_type', '')}: {e}")
                    html_response = "<div class='scholarship-details'><p>Price information is not available for this course.</p></div>"
                    questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                    return {
                        "response": html_response,
                        "options": questions.get("data", []),
                        "next_state": "question_selected",
                        "back_options": ["Back to categories", "Main page"]
                    }

            elif question_id == 22:
                testimonials = await db1.get_testimonials(context.get("city"), context.get("course"))
                if not testimonials:
                    questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                    return {
                        "response": "No testimonials found for this course.",
                        "options": questions.get("data", []),
                        "next_state": "question_selected",
                        "back_options": ["Back to categories", "Main page"]
                    }
                cleaned_testimonials = []
                for t in testimonials:
                    cleaned_url = t['video_url'].strip()
                    cleaned_testimonials.append({'video_url': cleaned_url})
                random_testimonial = random.choice(cleaned_testimonials)
                video_url = random_testimonial['video_url']
                html_response = f"""
                <div class="prompt-item">
                    <iframe width="100%" height="180" src="https://{video_url}" title="Testimonial Video" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen=""></iframe>
                </div>
                <p>Would you like to watch another video?</p>
                """
                context["testimonials"] = cleaned_testimonials
                context["viewed_testimonials"] = [video_url]
                chatbot.set_context(user_id, context)
                return {
                    "response": html_response,
                    "options": ["Yes"],
                    "next_state": "testimonial_response",
                    "back_options": ["Back to questions", "Main page"]
                }

            elif question_id == 25:
                bschool_content = await db1.get_bschool_selection(context.get("course_id"))
                if not bschool_content:
                    questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                    return {
                        "response": "No B-School Selection data found for this course.",
                        "options": questions.get("data", []),
                        "next_state": "question_selected",
                        "back_options": ["Back to categories", "Main page"]
                    }
                options = [item['Subtitle'] for item in bschool_content]
                context["bschool_content"] = bschool_content
                chatbot.set_context(user_id, context)
                return {
                    "response": "Please select a B-School Selection option:",
                    "options": options,
                    "next_state": "result_selected",
                    "back_options": ["Back to questions", "Main page"]
                }

            answer = await call_db_api("/api/answer", params={
                "question_id": question_id,
                "course": context.get("course", ""),
                "subcourse": context.get("subcourse", ""),
                "training_type": context.get("training_type", ""),
                "city": context.get("city", "")
            })
            await db1.log_query(user_id, context.get("course"), context.get("subcourse"), context.get("training_type"), context.get("category_id"), question_id, answer.get("data", ""))
            questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
            return {
                "response": answer.get("data", ""),
                "options": questions.get("data", []),
                "next_state": "question_selected",
                "back_options": ["Back to categories", "Main page"]
            }

        elif state == "result_selected":
            if user_input == "Back to questions":
                context = chatbot.get_context(user_id)
                questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                return {
                    "response": "Please select a question.",
                    "options": questions.get("data", []),
                    "next_state": "question_selected",
                    "back_options": ["Back to categories", "Main page"]
                }
            if user_input == "Main page":
                context = chatbot.get_context(user_id)
                city_data = await call_db_api("/api/city_data", params={"city": context.get('city', '')})
                return {
                    "response": f"Which course are you looking for in {context.get('city', '')}?",
                    "options": [course["name"] for course in city_data.get("data", {}).get("courses", [])],
                    "next_state": "course_selected",
                    "back_options": ["Back to cities"]
                }
            context = chatbot.get_context(user_id)
            selected_subtitle = user_input.strip()
            course_content = context.get("course_content", [])
            bschool_content = context.get("bschool_content", [])
            content = course_content + bschool_content
            selected_item = next((item for item in content if item["Subtitle"].strip() == selected_subtitle), None)
            if selected_item:
                clean_subtitle = selected_item['Subtitle'].strip()
                html_response = f'<div class="prompt-item"><a href="https://www.time4education.com{selected_item["Link"]}" class="prompt-link" target="_blank"><i class="fas fa-link"></i> {clean_subtitle}</a></div>'
                logger.debug(f"Result selected response: {html_response}")
                questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                return {
                    "response": html_response,
                    "options": questions.get("data", []),
                    "next_state": "question_selected",
                    "back_options": ["Back to categories", "Main page"]
                }
            else:
                questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                return {
                    "response": "Invalid selection. Please choose a valid option.",
                    "options": questions.get("data", []),
                    "next_state": "question_selected",
                    "back_options": ["Back to categories", "Main page"]
                }

        elif state == "testimonial_response":
            if user_input == "Back to questions":
                context = chatbot.get_context(user_id)
                questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                return {
                    "response": "Please select a question.",
                    "options": questions.get("data", []),
                    "next_state": "question_selected",
                    "back_options": ["Back to categories", "Main page"]
                }
            if user_input == "Main page":
                context = chatbot.get_context(user_id)
                city_data = await call_db_api("/api/city_data", params={"city": context.get('city', '')})
                return {
                    "response": f"Which course are you looking for in {context.get('city', '')}?",
                    "options": [course["name"] for course in city_data.get("data", {}).get("courses", [])],
                    "next_state": "course_selected",
                    "back_options": ["Back to cities"]
                }
            context = chatbot.get_context(user_id)
            if user_input.lower() == "yes":
                testimonials = context.get("testimonials", [])
                viewed_testimonials = context.get("viewed_testimonials", [])
                unseen_testimonials = [t for t in testimonials if t['video_url'].strip() not in [v.strip() for v in viewed_testimonials]]
                if unseen_testimonials:
                    random_testimonial = random.choice(unseen_testimonials)
                    video_url = random_testimonial['video_url'].strip()
                    html_response = f"""
                    <div class="prompt-item">
                        <iframe width="100%" height="180" src="https://{video_url}" title="Testimonial Video" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen=""></iframe>
                    </div>
                    """
                    viewed_testimonials.append(video_url)
                    context["viewed_testimonials"] = viewed_testimonials
                    chatbot.set_context(user_id, context)
                    return {
                        "response": html_response + "<p>Would you like to watch another video?</p>",
                        "options": ["Yes"],
                        "next_state": "testimonial_response",
                        "back_options": ["Back to questions", "Main page"]
                    }
                else:
                    html_response = '<div class="prompt-item"><a href="https://www.time4education.com" class="prompt-link" target="_blank"><i class="fas fa-link"></i>Time4Education Website</a><p>You can watch other videos on our website</p></div>'.strip()
                    questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                    return {
                        "response": html_response,
                        "options": questions.get("data", []),
                        "next_state": "question_selected",
                        "back_options": ["Back to categories", "Main page"]
                    }
            questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
            return {
                "response": "Would you like to watch another video?",
                "options": ["Yes"],
                "next_state": "testimonial_response",
                "back_options": ["Back to questions", "Main page"]
            }

    except Exception as e:
        logger.error(f"Error in chat endpoint, state={state}, input={user_input}, user_id={user_id}: {str(e)}")
        try:
            category_options = await call_db_api("/api/categories")
            return {
                "response": "Sorry, something went wrong. Let's get back on track.",
                "options": category_options.get("data", []),
                "next_state": "category_selected",
                "back_options": ["Back to variants", "Main page"]
            }
        except Exception as fallback_e:
            logger.error(f"Fallback error fetching categories: {str(fallback_e)}")
            return {
                "response": "Sorry, something went wrong. Please try again later.",
                "options": [],
                "next_state": "start"
            }

@app.post("/rag-chat")
async def rag_chat(data: RAGChatRequest):
    """
    RAG-based chat endpoint that uses OpenAI to generate responses based on database context
    """
    try:
        user_input = data.message.strip()
        user_id = data.user_id

        # --- Normalize user input ---
        normalized_input = re.sub(r'[?.!]+$', '', user_input).strip().lower()

        logger.info(f"RAG chat request received: {user_input[:50]}... from user {user_id}")

        if not normalized_input:
            return {
                "response": "Please enter your question.",
                "type": "rag"
            }

        # Check if we're in demo mode
        if hasattr(app.state, 'demo_mode') and app.state.demo_mode:
            logger.info("Using demo RAG system")
            from demo_rag import DemoRAGSystem
            demo_rag = DemoRAGSystem()
            response = demo_rag.generate_demo_response(normalized_input)
            logger.info(f"Demo RAG response generated for user {user_id}: {response[:100]}...")
        else:
            logger.info("Using full RAG system with database")
            user_context = chatbot.get_context(user_id) if user_id else {}
            # --- Prompt engineering ---
            system_prompt = (
                "If the user asks about course fees, and you have the information, always provide it. "
                "Only ask for clarification if absolutely necessary. "
                "Be concise and helpful."
            )
            # --- Improved retrieval logic: pass normalized_input and system_prompt ---
            response = await rag_system.generate_rag_response(normalized_input, user_context, system_prompt=system_prompt)
            logger.info(f"RAG response generated for user {user_id}: {response[:100]}...")

        return {
            "response": response,
            "type": "rag"
        }

    except Exception as e:
        logger.error(f"Error in RAG chat endpoint: {str(e)}")
        return {
            "response": f"I apologize, but I'm having trouble processing your request right now. Error: {str(e)}",
            "type": "rag"
        }

# Helper function to call internal db_api routes
async def call_db_api(endpoint, params=None):
    try:
        if endpoint == "/api/city_data":
            return await get_city_data(params.get("city"))
        if endpoint == "/api/find_nearest_center":
            return await find_nearest_center(params.get("city"))
        if endpoint == "/api/course_variants":
            return await get_course_variants(params.get("course_id"), params.get("subcourse"))
        if endpoint == "/api/course_price":
            return await get_course_price(params.get("variant"))
        if endpoint == "/api/scholarship_exams":
            return await get_scholarship_exams(params.get("course"), params.get("city"))
        if endpoint == "/api/questions":
            return await get_questions(params.get("category_id"))
        if endpoint == "/api/questions_dict":
            return await get_questions_dict(params.get("category_id"))
        if endpoint == "/api/answer":
            return await get_answer(
                params.get("question_id"),
                params.get("course"),
                params.get("subcourse"),
                params.get("training_type"),
                params.get("city")
            )
        if endpoint == "/api/subcourses":
            return await get_subcourses(params.get("course"))

        endpoint_map = {
            "/api/cities": get_cities,
            "/api/categories": get_categories,
            "/api/categories_dict": get_categories_dict,
        }
        func = endpoint_map.get(endpoint)
        if func:
            return await func()

        raise HTTPException(status_code=404, detail="Endpoint not found")

    except HTTPException as e:
        logger.error(f"Internal API error at {endpoint}: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error at {endpoint}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.on_event("startup")
async def startup_event():
    try:
        await db1.init_pool()
        logger.info("Database connection established successfully")
        app.state.demo_mode = False
    except Exception as e:
        logger.warning(f"Database connection failed: {e}")
        logger.warning("Running in demo mode - database features will be limited")
        app.state.demo_mode = True

@app.on_event("shutdown")
async def shutdown_event():
    try:
        await db1.close()
    except:
        pass  # Ignore errors during shutdown

@app.get("/api/cities")
async def get_cities():
    try:
        result = await db1.query("SELECT city FROM locations")
        cities = [row['city'] for row in result]
        logger.debug(f"Fetched cities: {cities}")
        return {"success": True, "data": cities}
    except Exception as e:
        logger.error(f"Error fetching cities: {e}")
        return {"success": False, "error": "Failed to fetch cities"}

@app.get("/api/find_nearest_center")
async def find_nearest_center(city: str):
    try:
        query = "SELECT nearest_center FROM mdl_city_state_centerslist WHERE LOWER(city) = LOWER(%s)"
        result = await db1.query(query, (city,))
        if result:
            return {"success": True, "nearest_center": result[0]['nearest_center']}
        else:
            return {"success": False, "error": "City not found"}
    except Exception as e:
        logger.error(f"Error finding nearest center for city {city}: {e}")
        return {"success": False, "error": "Failed to find nearest center"}

@app.get("/api/courses/{city}")
async def get_courses(city: str):
    try:
        logger.debug(f"Fetching courses for city: {city}")
        result = await db1.query("SELECT school_courses, college_courses FROM locations WHERE city = %s", (city,))
        if not result:
            logger.info(f"No location found for city: {city}")
            return {"success": True, "data": []}
        school_courses = result[0]['school_courses'].split(',') if result[0]['school_courses'] else []
        college_courses = result[0]['college_courses'].split(',') if result[0]['college_courses'] else []
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
                course_id, title, coursename = row['id'], row['title'], row['coursename']
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
        cities = [row['city'] for row in cities_result]
        logger.debug(f"All cities: {cities}")
        valid = city in cities
        courses = []
        if valid:
            result = await db1.query("SELECT school_courses, college_courses FROM locations WHERE city = %s", (city,))
            logger.debug(f"Location query result for {city}: {result}")
            if result:
                school_courses = result[0]['school_courses'].split(',') if result[0]['school_courses'] else []
                college_courses = result[0]['college_courses'].split(',') if result[0]['college_courses'] else []
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
                            course_id, title, coursename = row['id'], row['title'], row['coursename']
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
        try:
            course, year = subcourse.split(' ', 1)
            year_pattern = f"%{year}%"
            general_pattern = f"%{course} Classroom course%"
        except ValueError:
            course = subcourse
            year_pattern = "%"
            general_pattern = f"%{course} Classroom course%"

        query = """
            SELECT Coursesubvariant FROM coursedetails 
            WHERE Courseid = %s AND Coursesubvariant LIKE %s
            UNION
            SELECT Coursesubvariant FROM coursedetails 
            WHERE Courseid = %s AND Coursesubvariant LIKE %s
        """
        result = await db1.query(query, (course_id, year_pattern, course_id, general_pattern))
        variants = [row['Coursesubvariant'] for row in result]
        logger.debug(f"Course variants: {variants}")
        return {"success": True, "data": variants}
    except Exception as e:
        logger.error(f"Error fetching course variants for course_id={course_id}, subcourse={subcourse}: {e}")
        return {"success": False, "error": f"Failed to fetch course variants: {str(e)}"}

@app.get("/api/course_price")
async def get_course_price(variant: str):
    try:
        logger.debug(f"Fetching price for variant: {variant}")
        query = "SELECT Price, OfferPrice FROM coursedetails WHERE Coursesubvariant LIKE %s"
        result = await db1.query(query, (f"%{variant}%",))
        logger.debug(f"Query result for variant {variant}: {result}")
        if result and len(result) > 0:
            return {"success": True, "data": {"Price": result[0]['Price'], "OfferPrice": result[0]['OfferPrice']}}
        logger.warning(f"No price found for variant: {variant}")
        return {"success": False, "error": "No price found for this variant"}
    except Exception as e:
        logger.error(f"Error fetching price for variant {variant}: {e}")
        return {"success": False, "error": f"Failed to fetch price: {str(e)}"}

@app.get("/api/scholarship_exams")
async def get_scholarship_exams(course: str, city: str):
    try:
        logger.debug(f"Fetching scholarship exams for course: {course}, city: {city}")
        result = await db1.get_scholarship_exams(course, city)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error fetching scholarship exams for course {course}, city {city}: {e}")
        return {"success": False, "error": f"Failed to fetch scholarship exams: {str(e)}"}

@app.get("/api/subcourses")
async def get_subcourses(course: str):
    try:
        logger.debug(f"Fetching subcourses for course: {course}")
        result = await db1.query_subcourses(course)
        subcourses = [row['subcourse'] for row in result]
        logger.debug(f"Subcourses: {subcourses}")
        return {"success": True, "data": subcourses}
    except Exception as e:
        logger.error(f"Error fetching subcourses for {course}: {e}")
        return {"success": False, "error": f"Failed to fetch subcourses: {str(e)}"}

@app.get("/api/categories")
async def get_categories():
    try:
        logger.debug("Fetching categories")
        result = await db1.get_categories()
        categories = [row['name'] for row in result]
        logger.debug(f"Categories: {categories}")
        return {"success": True, "data": categories}
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return {"success": False, "error": f"Failed to fetch categories: {str(e)}"}

@app.get("/api/categories_dict")
async def get_categories_dict():
    try:
        logger.debug("Fetching categories_dict")
        result = await db1.get_categories()
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
        result = await db1.get_questions(category_id)
        questions = [row['question_text'] for row in result]
        logger.debug(f"Questions: {questions}")
        return {"success": True, "data": questions}
    except Exception as e:
        logger.error(f"Error fetching questions for category {category_id}: {e}")
        return {"success": False, "error": f"Failed to fetch questions: {str(e)}"}

@app.get("/api/questions_dict")
async def get_questions_dict(category_id: int):
    try:
        logger.debug(f"Fetching questions_dict for category_id: {category_id}")
        result = await db1.get_questions(category_id)
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
        answer = await db1.get_answer(question_id, context)
        logger.debug(f"Answer: {answer}")
        return {"success": True, "data": answer}
    except Exception as e:
        logger.error(f"Error fetching answer for question {question_id}: {e}")
        return {"success": False, "error": f"Failed to fetch answer: {str(e)}"}

@app.get("/api/all_cities")
async def get_all_cities():
    try:
        query = "SELECT DISTINCT city FROM mdl_city_state_centerslist"
        result = await db1.query(query)
        cities = [row['city'] for row in result]
        # logger.debug(f"Fetched all cities: {cities}")
        return {"success": True, "data": cities}
    except Exception as e:
        logger.error(f"Error fetching all cities: {e}")
        return {"success": False, "error": "Failed to fetch cities"}

# Mount frontend folder to serve static files
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

#! TREEEEEEEEEEEEEEEEEEEEEEEEEEEEE
@app.get("/api/category_qa")
def get_category_qa_endpoint(category_name: str):
    """
    API endpoint to fetch all questions and their static answers for a given category.
    This is used by the conversation tree UI.
    """
    results = get_qa_for_category(category_name)
    if not results:
        # Even if no results, return an empty list, not an error
        return []
    return results