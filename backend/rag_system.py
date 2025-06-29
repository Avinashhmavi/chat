import logging
from typing import List, Dict, Any
import openai
from config import OPENAI_API_KEY, OPENAI_MODEL
from db_connect import MySQLDB

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
        Search for relevant context from the database based on the user query using both full query and keyword-based search.
        """
        try:
            # 1. Try full query search
            categories_data = await self.db.search_categories_and_questions(query)
            exam_data = await self.db.search_exam_info(query)
            answers_data = await self.db.search_static_answers(query)
            context_data = []
            if categories_data:
                context_data.extend(categories_data)
            if exam_data:
                context_data.extend(exam_data)
            if answers_data:
                context_data.extend(answers_data)
            
            # 2. Check if query is about fees/prices and search for course prices
            fee_keywords = ['fee', 'fees', 'price', 'cost', 'offer', 'payment', 'amount', '₹', 'rs', 'rupees']
            query_lower = query.lower()
            price_data = []
            if any(keyword in query_lower for keyword in fee_keywords):
                price_data = await self.db.search_course_prices(query)
                if price_data:
                    context_data.extend(price_data)
            
            # 3. If not enough context, try keyword-based search
            if len(context_data) < 5:
                keywords = [word for word in query.split() if len(word) > 2]
                for kw in keywords:
                    cat_kw = await self.db.search_categories_and_questions(kw)
                    exam_kw = await self.db.search_exam_info(kw)
                    ans_kw = await self.db.search_static_answers(kw)
                    if cat_kw:
                        context_data.extend(cat_kw)
                    if exam_kw:
                        context_data.extend(exam_kw)
                    if ans_kw:
                        context_data.extend(ans_kw)
                    
                    # Also search for prices with keywords
                    if any(keyword in kw.lower() for keyword in fee_keywords):
                        price_kw = await self.db.search_course_prices(kw)
                        if price_kw:
                            context_data.extend(price_kw)
            
            # 4. Deduplicate context (optional, based on 'question_text' or 'answer_text')
            seen = set()
            unique_context = []
            for item in context_data:
                key = tuple(sorted(item.items()))
                if key not in seen:
                    unique_context.append(item)
                    seen.add(key)
            
            # 5. Separate price/fee info from other context
            price_items = [item for item in unique_context if item.get('Price') or item.get('OfferPrice') or item.get('course_variant')]
            other_items = [item for item in unique_context if not (item.get('Price') or item.get('OfferPrice') or item.get('course_variant'))]
            
            # 6. Return all price/fee info + up to 5 other context items
            final_context = price_items + other_items[:5]
            print(f"[RAG] Final context_data: {final_context}")
            return final_context
        except Exception as e:
            logger.error(f"Error searching context: {e}")
            return []
    
    async def generate_rag_response(self, query: str, user_context: Dict[str, Any] = None) -> str:
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
            
            # Create system prompt
            system_prompt = """You are TINA (TIME Instant Neural Assistant), a helpful assistant for T.I.M.E. (Triumphant Institute of Management Education). 
            You help students with information about courses, exams, admissions, and general queries.
            
            IMPORTANT: When the context contains "=== COURSE PRICE INFORMATION ===" section, you MUST use that exact price information to answer fee/price questions. 
            Do not give generic responses when specific price data is available.
            
            Use the provided context to answer questions accurately. If the context contains course fee/price information, 
            provide the exact amounts including both regular price and offer price if available. Format prices with the ₹ symbol.
            
            If the context doesn't contain enough information, politely ask the user to clarify or provide more specific information.
            
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
        
        # Always scan the full relevant_context for price/fee info
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
            else:
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