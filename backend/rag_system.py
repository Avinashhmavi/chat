import logging
from typing import List, Dict, Any
import openai
from config import OPENAI_API_KEY, OPENAI_MODEL
from db_connect import MySQLDB
import re

logger = logging.getLogger(__name__)

class RAGSystem:
    def __init__(self, db: MySQLDB):
        self.db = db
        if OPENAI_API_KEY:
            self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        else:
            logger.warning("OpenAI API key not found. RAG system will not work.")
            self.openai_client = None
        
    async def search_relevant_context(self, query: str) -> List[Dict[str, Any]]:
        """
        Broadened: Search all relevant tables for every user query, using fuzzy/semantic matching and keyword splitting.
        Aggregate all results for AI context.
        """
        try:
            # Normalize and split query into keywords
            norm_query = re.sub(r'[?.!]+$', '', query).strip().lower()
            keywords = [kw for kw in norm_query.split() if len(kw) > 2]
            context_data = []
            # 1. Search all tables with full query
            categories_data = await self.db.search_categories_and_questions(norm_query)
            exam_data = await self.db.search_exam_info(norm_query)
            answers_data = await self.db.search_static_answers(norm_query)
            price_data = await self.db.search_course_prices(norm_query)
            context_data.extend(categories_data or [])
            context_data.extend(exam_data or [])
            context_data.extend(answers_data or [])
            context_data.extend(price_data or [])
            # 2. Search all tables with each keyword
            for kw in keywords:
                cat_kw = await self.db.search_categories_and_questions(kw)
                exam_kw = await self.db.search_exam_info(kw)
                ans_kw = await self.db.search_static_answers(kw)
                price_kw = await self.db.search_course_prices(kw)
                context_data.extend(cat_kw or [])
                context_data.extend(exam_kw or [])
                context_data.extend(ans_kw or [])
                context_data.extend(price_kw or [])
            # 3. Deduplicate context (by sorted items)
            seen = set()
            unique_context = []
            for item in context_data:
                key = tuple(sorted(item.items()))
                if key not in seen:
                    unique_context.append(item)
                    seen.add(key)
            # 4. Separate price/fee info from other context
            price_items = [item for item in unique_context if item.get('Price') or item.get('OfferPrice') or item.get('course_variant')]
            other_items = [item for item in unique_context if not (item.get('Price') or item.get('OfferPrice') or item.get('course_variant'))]
            # 5. Return all price/fee info + up to 10 other context items
            final_context = price_items + other_items[:10]
            print(f"[RAG DEBUG] Final context_data for query '{query}': {final_context}")
            return final_context
        except Exception as e:
            logger.error(f"Error searching context: {e}")
            return []
    
    async def generate_rag_response(self, query: str, user_context: Dict[str, Any] = None, system_prompt: str = None) -> str:
        """
        Generate a response using RAG (Retrieval-Augmented Generation)
        """
        try:
            if not self.openai_client:
                return "OpenAI API key is not configured. Please set the OPENAI_API_KEY environment variable to use AI chat features."
            
            # Search for relevant context
            relevant_context = await self.search_relevant_context(query)
            
            if not relevant_context:
                return "I don't have specific information about that. Could you please rephrase your question or ask about our courses, exam information, or general queries?"
            
            # Build context string
            context_string = self._build_context_string(relevant_context, user_context)
            logger.info(f"[RAG DEBUG] Context string for query '{query}':\n{context_string}")
            
            # Use provided system_prompt if available, else default
            if system_prompt is None:
                system_prompt = (
                    "You are TINA (TIME Instant Neural Assistant), a helpful assistant for T.I.M.E. (Triumphant Institute of Management Education). "
                    "You help students with information about courses, exams, admissions, and general queries.\n\n"
                    "IMPORTANT: When the context contains \"=== COURSE PRICE INFORMATION ===\" section, you MUST use that exact price information to answer fee/price questions. "
                    "If the context contains a test name, date, registration, or other details, you MUST include them in your answer verbatim. "
                    "Do not give generic responses if details are available.\n\n"
                    "Use the provided context to answer questions accurately. If the context contains course fee/price information, "
                    "provide the exact amounts including both regular price and offer price if available. Format prices with the ₹ symbol.\n\n"
                    "If the context doesn't contain enough information, politely ask the user to clarify or provide more specific information.\n\n"
                    "Always be helpful, professional, and encouraging. If you don't know something, say so rather than making up information."
                )
            
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
        
        # Always scan the full relevant_context for price/fee info and test/exam details
        price_info_found = []
        other_context = []
        
        for item in relevant_context:
            # Check if this item contains price information
            if item.get('Price') or item.get('OfferPrice') or item.get('course_variant'):
                price_info = []
                if item.get('course_variant'):
                    price_info.append(f"Course Variant: {item['course_variant']}")
                if item.get('Price'):
                    price_info.append(f"Regular Price: ₹{item['Price']}")
                if item.get('OfferPrice'):
                    price_info.append(f"Offer Price: ₹{item['OfferPrice']}")
                if item.get('coursename'):
                    price_info.append(f"Course Name: {item['coursename']}")
                if item.get('title'):
                    price_info.append(f"Course Title: {item['title']}")
                if price_info:
                    price_info_found.append(" | ".join(price_info))
            # Add test/exam details if present
            if item.get('test_name') or item.get('test_type') or item.get('registration_closed') or item.get('exam_date'):
                test_info = []
                if item.get('test_name'):
                    test_info.append(f"Test Name: {item['test_name']}")
                if item.get('test_type'):
                    test_info.append(f"Test Type: {item['test_type']}")
                if item.get('registration_closed'):
                    test_info.append(f"Registration Closed: {item['registration_closed']}")
                if item.get('exam_date'):
                    test_info.append(f"Exam Date: {item['exam_date']}")
                if test_info:
                    other_context.append(" | ".join(test_info))
            # Other context information
            if item.get('category_name'):
                other_context.append(f"Category: {item['category_name']}")
            if item.get('question_text'):
                other_context.append(f"Question: {item['question_text']}")
            if item.get('answer_text'):
                other_context.append(f"Answer: {item['answer_text']}")
            if item.get('course'):
                other_context.append(f"Course: {item['course']}")
            if item.get('eligibility_criteria'):
                other_context.append(f"Eligibility: {item['eligibility_criteria']}")
            if item.get('exam_dates'):
                other_context.append(f"Exam Dates: {item['exam_dates']}")
            if item.get('registration_process'):
                other_context.append(f"Registration: {item['registration_process']}")
        
        # Add price information first, then other context
        if price_info_found:
            context_parts.append("=== COURSE PRICE INFORMATION ===")
            context_parts.extend(price_info_found)
            context_parts.append("=== END PRICE INFORMATION ===")
            context_parts.append("")
        
        if other_context:
            context_parts.append("=== OTHER RELEVANT INFORMATION ===")
            context_parts.extend(other_context[:10])  # Limit other context to avoid token limits
            context_parts.append("=== END OTHER INFORMATION ===")
        
        return "\n".join(context_parts) 