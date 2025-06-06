from flask import Flask, request, jsonify
from flask_cors import CORS
from config import MYSQL_CREDENTIALS, MSSQL_CREDENTIALS, DB3_CREDENTIALS
from db_connect import MySQLDB, MSSQLDB, DB3
from chatbot_engine import ChatbotEngine
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure CORS
CORS(app, resources={r"/*": {"origins": "http://localhost:8000", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]}})

# Initialize database connections
db1 = MySQLDB(MYSQL_CREDENTIALS)
db2 = MSSQLDB(MSSQL_CREDENTIALS)
db3 = DB3(DB3_CREDENTIALS)

# Initialize chatbot engine
chatbot = ChatbotEngine(db1, db2, db3)

@app.route('/register', methods=['POST'])
def register():
    try:
        if not request.is_json:
            logger.error('Request is not JSON')
            return jsonify({'success': False, 'message': 'Request must be JSON'}), 400
        
        data = request.get_json(force=True)
        logger.debug('Received data: %s', data)

        name = data.get('name', '').strip()
        mobile = data.get('mobile', '').strip()
        logger.debug('Parsed name: %s', name)
        logger.debug('Parsed mobile: %s', mobile)

        if not name or not mobile or not mobile.isdigit() or len(mobile) != 10:
            logger.error('Validation failed: name=%s, mobile=%s', name, mobile)
            return jsonify({'success': False, 'message': 'Valid name and 10-digit mobile are required'}), 400

        user_id, otp = chatbot.register_user(name, mobile, 'Unknown')
        logger.info('Registration successful for user_id: %s', user_id)
        return jsonify({'success': True, 'message': 'Registration successful. OTP sent', 'otp': otp, 'user_id': user_id})
    
    except Exception as e:
        logger.error('Error processing request: %s', str(e))
        return jsonify({'success': False, 'message': 'Invalid request format'}), 400

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json(force=True)
        logger.debug('Received OTP verification data: %s', data)
        user_id = data.get('user_id')
        otp = data.get('otp')
        if not user_id or not otp:
            logger.error('User ID or OTP missing: user_id=%s, otp=%s', user_id, otp)
            return jsonify({'success': False, 'message': 'User ID and OTP are required'}), 400
        if chatbot.verify_otp(user_id, otp):
            logger.info('OTP verified for user_id: %s', user_id)
            return jsonify({'success': True, 'message': 'OTP verified successfully', 'user_id': user_id})
        logger.warning('Invalid OTP for user_id: %s', user_id)
        return jsonify({'success': False, 'message': 'Invalid OTP'})
    except Exception as e:
        logger.error('Error verifying OTP: %s', str(e))
        return jsonify({'success': False, 'message': 'Invalid request format'}), 400

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(force=True)
        logger.debug('Received chat data: %s', data)
        state = data.get('state', 'start')
        user_input = data.get('input', '')
        user_id = data.get('user_id')

        if state == 'start':
            return jsonify({
                'response': f"Hi, <user>! I'm TIME Instant Neural Assistant (TINA) here to assist you today.\n\nWhat city are you from?",
                'options': ['Hyderabad', 'Mumbai', 'Delhi', 'Bangalore', 'Chennai'],
                'next_state': 'city_selected'
            })

        elif state == 'city_selected':
            selected_city = user_input
            valid_cities = ['Hyderabad', 'Mumbai', 'Delhi', 'Bangalore', 'Chennai']
            if selected_city not in valid_cities:
                return jsonify({
                    'response': 'Invalid city. Please select a valid city.',
                    'options': valid_cities,
                    'next_state': 'city_selected'
                })
            chatbot.set_context(user_id, {'city': selected_city})
            courses = ['CAT', 'GMAT', 'Bank Exams', 'SSC CGLE', 'GRE', 'MAT', 'ICET', 'MHCET', 'CMAT', 'IPMAT', 'CLAT', 'CUET', 'OTHERS']
            return jsonify({
                'response': f'You selected {selected_city}. Which Course are you looking for?',
                'options': courses,
                'next_state': 'course_selected'
            })

        elif state == 'course_selected':
            selected_course = user_input
            chatbot.set_context(user_id, {'course': selected_course})
            subcourses = db3.query_subcourses(selected_course)
            subcourse_options = [subcourse[0] for subcourse in subcourses]
            return jsonify({
                'response': f'Which {selected_course} Exam year are you looking for?',
                'options': subcourse_options,
                'next_state': 'subcourse_selected'
            })

        elif state == 'subcourse_selected':
            selected_subcourse = user_input
            chatbot.set_context(user_id, {'subcourse': selected_subcourse})
            coursetypes = db3.query_coursetypes(selected_subcourse)
            coursetype_options = [coursetype[0] for coursetype in coursetypes]
            return jsonify({
                'response': 'What type of training would you like?',
                'options': coursetype_options,
                'next_state': 'training_type_selected'
            })

        elif state == 'training_type_selected':
            selected_training_type = user_input
            chatbot.set_context(user_id, {'training_type': selected_training_type})
            categories = db3.get_categories()
            category_options = [category[1] for category in categories]
            return jsonify({
                'response': 'How can I assist you further?',
                'options': category_options,
                'next_state': 'category_selected'
            })

        elif state == 'category_selected':
            if not user_input:
                categories = db3.get_categories()
                category_options = [category[1] for category in categories]
                return jsonify({
                    'response': 'How can I assist you further?',
                    'options': category_options,
                    'next_state': 'category_selected'
                })

            selected_category = user_input
            categories = db3.get_categories()
            category_dict = {category[1]: category[0] for category in categories}
            if selected_category == 'End Chat':
                return jsonify({
                    'response': 'Goodbye! If you need help, feel free to reach out again.',
                    'options': [],
                    'next_state': 'start'
                })
            category_id = category_dict.get(selected_category)
            if not category_id:
                category_options = [category[1] for category in categories]
                return jsonify({
                    'response': 'Invalid category. How can I assist you further?',
                    'options': category_options,
                    'next_state': 'category_selected'
                })
            questions = db3.get_questions(category_id)
            question_options = [question[1] for question in questions]
            chatbot.set_context(user_id, {'category_id': category_id})
            return jsonify({
                'response': 'Please select a question:',
                'options': question_options,
                'next_state': 'question_selected'
            })

        elif state == 'question_selected':
            selected_question = user_input
            questions = db3.get_questions(chatbot.get_context(user_id)['category_id'])
            question_dict = {question[1]: question[0] for question in questions}
            if selected_question == 'Back':
                categories = db3.get_categories()
                category_options = [category[1] for category in categories]
                return jsonify({
                    'response': 'How can I assist you further?',
                    'options': category_options,
                    'next_state': 'category_selected'
                })
            question_id = question_dict.get(selected_question)
            context = chatbot.get_context(user_id)
            answer = db3.get_answer(question_id, context, db1, db2)
            db3.log_query(user_id, context['course'], context['subcourse'], context['training_type'], context['category_id'], question_id, answer)
            
            questions = db3.get_questions(context['category_id'])
            question_options = [question[1] for question in questions]
            
            return jsonify({
                'response': answer,
                'options': question_options,
                'next_state': 'question_selected'
            })

        return jsonify({
            'response': 'Something went wrong. Let’s start over.',
            'options': ['Restart'],
            'next_state': 'start'
        })

    except Exception as e:
        logger.error('Error processing chat request: %s', str(e))
        categories = db3.get_categories()
        category_options = [category[1] for category in categories]
        return jsonify({
            'response': 'Sorry, something went wrong. Let’s get back on track. How can I assist you further?',
            'options': category_options,
            'next_state': 'category_selected'
        }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)