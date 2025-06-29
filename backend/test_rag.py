#!/usr/bin/env python3
"""
Test script for the RAG system
"""
import asyncio
import os
from dotenv import load_dotenv
from config import MYSQL_CREDENTIALS
from db_connect import MySQLDB
from rag_system import RAGSystem

async def test_rag_system():
    """Test the RAG system with sample queries"""
    
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
        
        # Test queries
        test_queries = [
            "What are the eligibility criteria for CAT?",
            "Tell me about MBA advantages",
            "What are the exam dates for GMAT?",
            "How much does the classroom course cost?",
            "What is the registration process for CAT?"
        ]
        
        print("\n🧪 Testing RAG system with sample queries...")
        print("=" * 60)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: {query}")
            print("-" * 40)
            
            try:
                # Test context retrieval
                context = await rag.search_relevant_context(query)
                print(f"📚 Found {len(context)} relevant context items")
                
                # Test RAG response generation
                response = await rag.generate_rag_response(query)
                print(f"🤖 Response: {response[:200]}...")
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        print("\n✅ RAG system test completed!")
        
        # Close database connection
        await db.close()
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_rag_system()) 