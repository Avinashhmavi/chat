#!/usr/bin/env python3
"""
Test script for the RAG system with fee/price queries
"""
import asyncio
import os
from dotenv import load_dotenv
from config import MYSQL_CREDENTIALS
from db_connect import MySQLDB
from rag_system import RAGSystem

async def test_fee_rag_system():
    """Test the RAG system with fee-related queries"""
    
    # Load environment variables
    load_dotenv()
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key in the .env file")
        return
    
    try:
        # Initialize database connection
        print("🔌 Initializing database connection...")
        db = MySQLDB(MYSQL_CREDENTIALS)
        await db.init_pool()
        
        # Initialize RAG system
        print("🤖 Initializing RAG system...")
        rag = RAGSystem(db)
        
        # Test fee-related queries
        test_queries = [
            "What is the fees for CAT 2025 Online-Flexi (Recorded Videos) Course",
            "How much does the CAT classroom course cost?",
            "What is the price for GMAT online course?",
            "Tell me about CAT course fees",
            "What are the fees for MBA preparation courses?"
        ]
        
        print("\n🧪 Testing RAG system with fee-related queries...")
        print("=" * 70)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: {query}")
            print("-" * 50)
            
            try:
                # Test context retrieval
                context = await rag.search_relevant_context(query)
                print(f"📚 Found {len(context)} relevant context items")
                
                # Show what context was found
                for j, item in enumerate(context, 1):
                    print(f"  Context {j}:")
                    if item.get('course_variant'):
                        print(f"    Course Variant: {item['course_variant']}")
                    if item.get('Price'):
                        print(f"    Price: ₹{item['Price']}")
                    if item.get('OfferPrice'):
                        print(f"    Offer Price: ₹{item['OfferPrice']}")
                    if item.get('coursename'):
                        print(f"    Course Name: {item['coursename']}")
                    if item.get('question_text'):
                        print(f"    Question: {item['question_text']}")
                    if item.get('answer_text'):
                        print(f"    Answer: {item['answer_text'][:100]}...")
                
                # Test RAG response generation
                response = await rag.generate_rag_response(query)
                print(f"🤖 Response: {response[:300]}...")
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        print("\n✅ Fee RAG system test completed!")
        
        # Close database connection
        await db.close()
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_fee_rag_system()) 