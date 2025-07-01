#!/usr/bin/env python3
"""
Demo script for testing RAG functionality without database
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY not found in environment variables")
    print("Please set your OpenAI API key in the .env file")
    print("You can get one from: https://platform.openai.com/api-keys")
    print("For demo purposes, the script will show sample responses without OpenAI.")
    print("")

import openai
from config import OPENAI_API_KEY, OPENAI_MODEL

class DemoRAGSystem:
    def __init__(self):
        if OPENAI_API_KEY:
            self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        else:
            self.openai_client = None
        
    def generate_demo_response(self, query: str) -> str:
        """
        Generate a demo response using OpenAI without database context
        """
        try:
            if not self.openai_client:
                # Return sample responses when OpenAI is not available
                sample_responses = {
                    "What are the eligibility criteria for CAT?": "The Common Admission Test (CAT) typically requires a Bachelor's degree with at least 50% marks (45% for SC/ST/PwD). Final year students can also apply. The exam is conducted by IIMs for MBA admissions.",
                    "Tell me about MBA advantages": "An MBA offers several advantages: career advancement, higher salary potential, leadership skill development, networking opportunities, specialization options, and entrepreneurial skills. It opens doors to management roles and global opportunities.",
                    "What are the exam dates for GMAT?": "GMAT is a computer-adaptive test available year-round at various test centers. You can choose your preferred date and time based on availability. Registration is recommended well in advance.",
                    "How should I prepare for MBA entrance exams?": "Prepare by understanding the exam format, creating a study plan, using quality study materials, practicing mock tests, focusing on weak areas, staying updated with current affairs, and maintaining a healthy lifestyle.",
                    "What are the benefits of doing an MBA?": "MBA benefits include career advancement, higher earning potential, skill development, networking opportunities, global exposure, and preparation for leadership roles in business."
                }
                
                # Find the best matching question
                for sample_q, sample_a in sample_responses.items():
                    if any(word in query.lower() for word in sample_q.lower().split()):
                        return sample_a
                
                return "I can help you with questions about MBA entrance exams, CAT, GMAT, MBA advantages, and exam preparation. Please ask a specific question about these topics."
            
            # Create system prompt for T.I.M.E. chatbot
            system_prompt = """You are TINA (TIME Instant Neural Assistant), a helpful assistant for T.I.M.E. (Triumphant Institute of Management Education). 
            You help students with information about courses, exams, admissions, and general queries.
            
            Since this is a demo mode without database access, provide general helpful information about:
            - Common MBA entrance exams (CAT, GMAT, XAT, etc.)
            - General MBA advantages and career prospects
            - Typical exam preparation advice
            - General information about business schools
            
            Always be helpful, professional, and encouraging. If you don't know something specific, say so rather than making up information."""
            
            # Generate response using OpenAI
            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"I apologize, but I'm having trouble processing your request right now. Error: {str(e)}"

async def demo_rag_system():
    """Demo the RAG system with sample queries"""
    
    print("🤖 TINA Chatbot RAG Demo")
    print("=" * 40)
    print("This demo shows the AI-powered chat functionality.")
    print("Note: Running without database, so responses are general.")
    print("")
    
    # Initialize demo RAG system
    rag = DemoRAGSystem()
    
    # Demo queries
    demo_queries = [
        "What are the eligibility criteria for CAT?",
        "Tell me about MBA advantages",
        "What are the exam dates for GMAT?",
        "How should I prepare for MBA entrance exams?",
        "What are the benefits of doing an MBA?"
    ]
    
    print("🧪 Testing AI responses with sample queries...")
    print("=" * 60)
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n📝 Demo {i}: {query}")
        print("-" * 40)
        
        try:
            response = rag.generate_demo_response(query)
            print(f"🤖 Response: {response}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 Demo completed!")
    print("")
    print("To test with full database integration:")
    print("1. Set up MySQL database with the schema from sql_scripts_db3/")
    print("2. Configure database credentials in backend/.env")
    print("3. Run: cd backend && python test_rag.py")
    print("4. Run: ./start.sh (to start the full chatbot)")

if __name__ == "__main__":
    asyncio.run(demo_rag_system()) 