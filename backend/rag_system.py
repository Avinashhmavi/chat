import logging
from typing import List, Dict, Any
import openai
from config import OPENAI_API_KEY, OPENAI_MODEL
from db_connect import MySQLDB

logger = logging.getLogger(__name__)

class RAGSystem:
    def __init__(self, db: MySQLDB):
        self.db = db
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
    async def search_relevant_context(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for relevant context from the database based on the user query
        """
        try:
            # Search in categories and questions
            categories_data = await self.db.search_categories_and_questions(query)
            
            # Search in exam_info
            exam_data = await self.db.search_exam_info(query)
            
            # Search in static_answers
            answers_data = await self.db.search_static_answers(query)
            
            # Combine all relevant data
            context_data = []
            
            if categories_data:
                context_data.extend(categories_data)
            
            if exam_data:
                context_data.extend(exam_data)
                
            if answers_data:
                context_data.extend(answers_data)
            
            return context_data[:5]  # Limit to top 5 most relevant results
            
        except Exception as e:
            logger.error(f"Error searching context: {e}")
            return []
    
    async def generate_rag_response(self, query: str, user_context: Dict[str, Any] = None) -> str:
        """
        Generate a response using RAG (Retrieval-Augmented Generation)
        """
        try:
            # Search for relevant context
            relevant_context = await self.search_relevant_context(query)
            
            if not relevant_context:
                return "I don't have specific information about that. Could you please rephrase your question or ask about our courses, exam information, or general queries?"
            
            # Build context string
            context_string = self._build_context_string(relevant_context, user_context)
            
            # Create system prompt
            system_prompt = """You are TINA (TIME Instant Neural Assistant), a helpful assistant for T.I.M.E. (Triumphant Institute of Management Education). 
            You help students with information about courses, exams, admissions, and general queries.
            
            Use the provided context to answer questions accurately. If the context doesn't contain enough information, 
            politely ask the user to clarify or provide more specific information.
            
            Always be helpful, professional, and encouraging. If you don't know something, say so rather than making up information."""
            
            # Create user message
            user_message = f"Context: {context_string}\n\nUser Question: {query}\n\nPlease provide a helpful response based on the context provided."
            
            # Generate response using OpenAI
            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again later or contact our support team."
    
    def _build_context_string(self, relevant_context: List[Dict[str, Any]], user_context: Dict[str, Any] = None) -> str:
        """
        Build a context string from relevant data and user context
        """
        context_parts = []
        
        # Add user context if available
        if user_context:
            if user_context.get('city'):
                context_parts.append(f"User's city: {user_context['city']}")
            if user_context.get('course'):
                context_parts.append(f"User's selected course: {user_context['course']}")
            if user_context.get('subcourse'):
                context_parts.append(f"User's selected exam year: {user_context['subcourse']}")
        
        # Add relevant context data
        for item in relevant_context:
            if item.get('category_name'):
                context_parts.append(f"Category: {item['category_name']}")
            if item.get('question_text'):
                context_parts.append(f"Question: {item['question_text']}")
            if item.get('answer_text'):
                context_parts.append(f"Answer: {item['answer_text']}")
            if item.get('course'):
                context_parts.append(f"Course: {item['course']}")
            if item.get('eligibility_criteria'):
                context_parts.append(f"Eligibility: {item['eligibility_criteria']}")
            if item.get('exam_dates'):
                context_parts.append(f"Exam Dates: {item['exam_dates']}")
            if item.get('registration_process'):
                context_parts.append(f"Registration: {item['registration_process']}")
        
        return "\n".join(context_parts) 