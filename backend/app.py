from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import MYSQL_CREDENTIALS, MSSQL_CREDENTIALS, DB3_CREDENTIALS
from db_connect import MySQLDB, MSSQLDB, DB3
from chatbot_engine import ChatbotEngine
import httpx
import logging
import asyncio
import random

app = FastAPI()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

db1 = MySQLDB(MYSQL_CREDENTIALS)
db2 = MSSQLDB(MSSQL_CREDENTIALS)
db3 = DB3(DB3_CREDENTIALS)

chatbot = ChatbotEngine(db1, db2, db3)

DB_API_URL = "http://localhost:8001"

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

async def call_db_api(endpoint, params=None, retries=3, backoff=1):
    url = f"{DB_API_URL}{endpoint}"
    async with httpx.AsyncClient(timeout=5) as client:
        for attempt in range(retries):
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                if not data.get("success"):
                    logger.error(f"API error at {url}: {data.get('error')}")
                    raise HTTPException(status_code=500, detail=data.get("error"))
                return data["data"]
            except httpx.RequestError as e:
                logger.error(f"API call failed at {url}: {e}")
                if attempt == retries - 1:
                    raise HTTPException(status_code=503, detail="Database API unavailable")
                await asyncio.sleep(backoff * (2 ** attempt))

@app.on_event("startup")
async def startup_event():
    await db1.init_pool()
    await db3.init_pool()

@app.on_event("shutdown")
async def shutdown_event():
    await db1.close()
    await db3.close()
    db2.close()

@app.post("/register")
async def register(data: RegisterRequest):
    try:
        name = data.name.strip()
        mobile = data.mobile.strip()
        logger.debug('Parsed name: %s, mobile: %s', name, mobile)
        if not name or not mobile or not mobile.isdigit() or len(mobile) != 10:
            logger.error('Validation failed: name=%s, mobile=%s', name, mobile)
            raise HTTPException(status_code=400, detail="Valid name and 10-digit mobile are required")
        user_id, otp = await chatbot.register_user(name, mobile, 'Unknown')
        logger.info(f'Registration successful for user_id: {user_id}')
        return {"success": True, "message": "Registration successful", "otp": otp, "user_id": user_id}
    except Exception as e:
        logger.error(f'Error processing request: {str(e)}')
        raise HTTPException(status_code=400, detail="Invalid request format")

@app.post("/verify-otp")
async def verify_otp(data: VerifyOTPRequest):
    try:
        logger.debug(f'Received OTP verification data: {data.dict()}')
        if not data.user_id or not data.otp:
            logger.error(f'User ID or OTP missing: user_id={data.user_id}, otp={data.otp}')
            raise HTTPException(status_code=400, detail="User ID and OTP are required")
        if await chatbot.verify_otp(data.user_id, data.otp):
            logger.info(f'OTP verified for user_id: {data.user_id}')
            return {"success": True, "message": "OTP verified successfully", "user_id": data.user_id}
        logger.warning(f'Invalid OTP for user_id: {data.user_id}')
        raise HTTPException(status_code=400, detail="Invalid OTP")
    except Exception as e:
        logger.error(f'Error verifying OTP: {e}')
        raise HTTPException(status_code=400, detail="Invalid request format")

@app.post("/chat")
async def chat(data: ChatRequest):
    try:
        logger.debug(f"Received data: {data.dict()}")
        state = data.state
        user_input = data.input.strip()
        user_id = data.user_id

        if state == "start":
            city_options = await call_db_api("/api/cities")
            logger.debug(f"Fetched cities: {city_options}")
            if not city_options:
                logger.error("No cities found")
                return {"response": "No cities available. Please contact support.", "options": [], "next_state": "start"}
            return {
                "response": "Please select a city.",
                "options": city_options,
                "next_state": "city_selected"
            }

        elif state == "city_selected":
            selected_city = user_input
            city_data = await call_db_api(f"/api/city_data/{selected_city}")
            if not city_data["valid"]:
                cities = city_data.get("cities", [])
                return {
                    "response": "Invalid city. Please select a valid city.",
                    "options": cities,
                    "next_state": "city_selected"
                }
            chatbot.set_context(user_id, {"city": selected_city})
            if not city_data["courses"]:
                cities = city_data.get("cities", [])
                return {
                    "response": f"No active courses available for {selected_city}. Please select another city.",
                    "options": cities,
                    "next_state": "city_selected"
                }
            return {
                "response": f"You selected: {selected_city}. Which course are you looking for?",
                "options": [course["name"] for course in city_data["courses"]],
                "next_state": "course_selected"
            }

        elif state == "course_selected":
            selected_course = user_input
            context = chatbot.get_context(user_id)
            city_data = await call_db_api(f"/api/city_data/{context.get('city', '')}")
            course_dict = {course["name"]: course["id"] for course in city_data.get("courses", [])}
            course_id = course_dict.get(selected_course)
            if not course_id:
                return {
                    "response": "Invalid course. Please select a valid course.",
                    "options": [course["name"] for course in city_data.get("courses", [])],
                    "next_state": "course_selected"
                }
            chatbot.set_context(user_id, {"course": selected_course, "course_id": course_id})
            subcourse_options = await call_db_api("/api/subcourses", params={"course": selected_course})
            if not subcourse_options:
                logger.warning(f"No subcourses found for course: {selected_course}")
                return {
                    "response": f"No exam years available for {selected_course}. Please select another course.",
                    "options": [course["name"] for course in city_data.get("courses", [])],
                    "next_state": "course_selected"
                }
            return {
                "response": f"Which {selected_course} exam year are you looking for?",
                "options": subcourse_options,
                "next_state": "subcourse_selected"
            }

        elif state == "subcourse_selected":
            selected_subcourse = user_input
            context = chatbot.get_context(user_id)
            course_id = context.get("course_id")
            subcourse_options = await call_db_api("/api/subcourses", params={"course": context.get("course", "")})
            if selected_subcourse not in subcourse_options:
                return {
                    "response": f"Invalid exam year. Please select a valid {context.get('course', '')} exam year.",
                    "options": subcourse_options,
                    "next_state": "subcourse_selected"
                }
            chatbot.set_context(user_id, {"subcourse": selected_subcourse})
            variant_options = await call_db_api("/api/course_variants", params={"course_id": course_id, "subcourse": selected_subcourse})
            if not variant_options:
                logger.warning(f"No course variants found for subcourse: {selected_subcourse}, course_id: {course_id}")
                return {
                    "response": f"No variants available for {selected_subcourse}. Please select another exam year.",
                    "options": subcourse_options,
                    "next_state": "subcourse_selected"
                }
            return {
                "response": "What course variant would you like?",
                "options": variant_options,
                "next_state": "training_type_selected"
            }

        elif state == "training_type_selected":
            selected_variant = user_input
            context = chatbot.get_context(user_id)
            variant_options = await call_db_api("/api/course_variants", params={"course_id": context.get("course_id"), "subcourse": context.get("subcourse")})
            if selected_variant not in variant_options:
                return {
                    "response": f"Invalid variant. Please select a valid variant for {context.get('subcourse', '')}.",
                    "options": variant_options,
                    "next_state": "training_type_selected"
                }
            logger.debug(f"Processing training_type_selected with input: {selected_variant}")
            chatbot.set_context(user_id, {"training_type": selected_variant})
            category_options = await call_db_api("/api/categories")
            if not category_options:
                logger.warning("No categories found")
                return {
                    "response": "No categories available. Let’s start over.",
                    "options": [],
                    "next_state": "start"
                }
            return {
                "response": "How can I assist you further?",
                "options": category_options,
                "next_state": "category_selected"
            }

        elif state == "category_selected":
            if not user_input:
                category_options = await call_db_api("/api/categories")
                return {
                    "response": "How can I assist you further?",
                    "options": category_options,
                    "next_state": "category_selected"
                }
            selected_category = user_input
            category_dict = await call_db_api("/api/categories_dict")
            if selected_category.upper() == "END_CHAT":
                return {
                    "response": "Goodbye! If you need help, feel free to reach out again.",
                    "options": [],
                    "next_state": "start"
                }
            category_id = category_dict.get(selected_category)
            if not category_id:
                logger.error(f"Invalid category selected: {selected_category}")
                category_options = await call_db_api("/api/categories")
                return {
                    "response": "Invalid category. How can I assist you further?",
                    "options": category_options,
                    "next_state": "category_selected"
                }
            questions = await call_db_api("/api/questions", params={"category_id": category_id})
            chatbot.set_context(user_id, {"category_id": category_id})
            return {
                "response": "Please select a question.",
                "options": questions,
                "next_state": "question_selected"
            }

        elif state == "question_selected":
            selected_question = user_input
            context = chatbot.get_context(user_id)
            question_dict = await call_db_api("/api/questions_dict", params={"category_id": context.get("category_id")})
            if selected_question.upper() == "BACK":
                category_options = await call_db_api("/api/categories")
                return {
                    "response": "How can I assist you further?",
                    "options": category_options,
                    "next_state": "category_selected"
                }
            question_id = question_dict.get(selected_question)
            if not question_id:
                questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                return {
                    "response": "Invalid question. Please select a valid question.",
                    "options": questions,
                    "next_state": "question_selected"
                }

            if context.get("category_id") == 8:
                    question_columns = {
                        39: "eligibility_criteria",
                        40: "exam_dates",
                        41: "registration_process",
                        42: "score_validity",
                        43: "top_b_schools",
                        44: "mba_advantages",
                        45: "selection_process",
                        46: "attempts_allowed"
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
                        logger.debug(f"Executing query: {query} with parameter: {course_param}")
                        try:
                            async with db3.get_cursor() as cursor:
                                logger.debug("Before executing query")
                                await cursor.execute(query, (course_param,))
                                logger.debug("After executing query")
                                result = await cursor.fetchone()
                                logger.debug(f"Query result: {result}")
                                if result:
                                    answer = result.get(column)
                                    logger.debug(f"Answer extracted: {answer}")
                                    if answer:
                                        await db3.log_query(
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
                                            "options": questions,  # Move options here
                                            "next_state": "question_selected"
                                        }
                                    else:
                                        logger.warning(f"No data found for column {column} in result")
                                else:
                                    logger.warning(f"No data found for course: {context.get('course', '')}")
                        except Exception as e:
                            logger.error(f"Error fetching exam_info: {e}")
                    else:
                        logger.error(f"Invalid question_id: {question_id} for category_id 8")
                    questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                    return {
                        "response": "No information found for this question.",
                        "options": questions,  # Move options here
                        "next_state": "question_selected"
                    }            
                    
            if question_id == 22:
                course_content = await db1.get_course_content(context.get("course_id"), context.get("course"))
                if not course_content:
                    questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                    return {
                        "response": "No results found for this course.",
                        "options": questions,
                        "next_state": "question_selected"
                    }
                options = [item['Subtitle'] for item in course_content]
                context["course_content"] = course_content
                chatbot.set_context(user_id, context)
                return {
                    "response": "Please select a result to view:",
                    "options": options,
                    "next_state": "result_selected"
                }

            elif question_id == 23:
                testimonials = await db1.get_testimonials(context.get("city"), context.get("course"))
                if not testimonials:
                    questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                    return {
                        "response": "No testimonials found for this course.",
                        "options": questions,
                        "next_state": "question_selected"
                    }
                random_testimonial = random.choice(testimonials)
                video_url = random_testimonial['video_url']
                html_response = f"""
                <div class="prompt-item">
                    <iframe width="100%" height="180" src="https://{video_url}" title="Testimonial Video" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen=""></iframe>
                    <p class="prompt-text">Watch our introduction video</p>
                </div>
                """
                context["testimonials"] = testimonials
                context["viewed_testimonials"] = [video_url]
                chatbot.set_context(user_id, context)
                return {
                    "response": html_response,
                    "options": ["Yes", "No"],
                    "next_state": "testimonial_response"
                }

            elif question_id == 26:
                bschool_content = await db1.get_bschool_selection(context.get("course_id"))
                if not bschool_content:
                    questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                    return {
                        "response": "No B-School Selection data found for this course.",
                        "options": questions,
                        "next_state": "question_selected"
                    }
                options = [item['Subtitle'] for item in bschool_content]
                context["bschool_content"] = bschool_content
                chatbot.set_context(user_id, context)
                return {
                    "response": "Please select a B-School Selection option:",
                    "options": options,
                    "next_state": "result_selected"
                }

            answer = await call_db_api("/api/answer", params={
                "question_id": question_id,
                "course": context.get("course", ""),
                "subcourse": context.get("subcourse", ""),
                "training_type": context.get("training_type", ""),
                "city": context.get("city", "")
            })
            await db3.log_query(user_id, context.get("course"), context.get("subcourse"), context.get("training_type"), context.get("category_id"), question_id, answer)
            questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
            return {
                "response": answer,
                "options": [],
                "next_state": "question_selected",
                "follow_up": {
                    "response": "How can I assist you further?",
                    "options": questions,
                    "next_state": "question_selected"
                }
            }

        elif state == "result_selected":
            context = chatbot.get_context(user_id)
            selected_subtitle = user_input
            course_content = context.get("course_content", [])
            bschool_content = context.get("bschool_content", [])
            content = course_content + bschool_content
            selected_item = next((item for item in content if item["Subtitle"] == selected_subtitle), None)
            if selected_item:
                html_response = f"""
                <div class="prompt-item">
                    <a href="https://www.time4education.com{selected_item['Link']}" class="prompt-link" target="_blank">
                        <i class="fas fa-link"></i> {selected_item['Subtitle']}
                    </a>
                </div>
                """
                questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                return {
                    "response": html_response,
                    "options": [],
                    "next_state": "question_selected",
                    "follow_up": {
                        "response": "How can I assist you further?",
                        "options": questions,
                        "next_state": "question_selected"
                    }
                }
            else:
                questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                return {
                    "response": "Invalid selection. Please choose a valid option.",
                    "options": questions,
                    "next_state": "question_selected"
                }

        elif state == "testimonial_response":
            context = chatbot.get_context(user_id)
            if user_input.lower() == "yes":
                testimonials = context.get("testimonials", [])
                viewed_testimonials = context.get("viewed_testimonials", [])
                unseen_testimonials = [t for t in testimonials if t['video_url'] not in viewed_testimonials]
                if unseen_testimonials:
                    random_testimonial = random.choice(unseen_testimonials)
                    video_url = random_testimonial['video_url']
                    html_response = f"""
                    <div class="prompt-item">
                        <iframe width="100%" height="180" src="https://{video_url}" title="Testimonial Video" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen=""></iframe>
                        <p class="prompt-text">Watch our introduction video</p>
                    </div>
                    """
                    viewed_testimonials.append(video_url)
                    context["viewed_testimonials"] = viewed_testimonials
                    chatbot.set_context(user_id, context)
                    return {
                        "response": html_response,
                        "options": ["Yes", "No"],
                        "next_state": "testimonial_response"
                    }
                else:
                    questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
                    return {
                        "response": "No more testimonial videos available.",
                        "options": [],
                        "next_state": "question_selected",
                        "follow_up": {
                            "response": "How can I assist you further?",
                            "options": questions,
                            "next_state": "question_selected"
                        }
                    }
            questions = await call_db_api("/api/questions", params={"category_id": context.get("category_id")})
            return {
                "response": "",
                "options": [],
                "next_state": "question_selected",
                "follow_up": {
                    "response": "How can I assist you further?",
                    "options": questions,
                    "next_state": "question_selected"
                }
            }

        return {
            "response": "Something went wrong. Let’s start over.",
            "options": ["Restart"],
            "next_state": "start"
        }

    except Exception as e:
        logger.error(f"Error in chat endpoint, state={state}, input={user_input}, user_id={user_id}: {str(e)}")
        try:
            category_options = await call_db_api("/api/categories")
            return {
                "response": "Sorry, something went wrong. Let’s get back on track.",
                "options": [],
                "next_state": "category_selected",
                "follow_up": {
                    "response": "How can I assist you further?",
                    "options": category_options,
                    "next_state": "category_selected"
                }
            }
        except Exception as fallback_e:
            logger.error(f"Fallback error fetching categories: {str(fallback_e)}")
            return {
                "response": "Sorry, something went wrong. Please try again later.",
                "options": [],
                "next_state": "start"
            }