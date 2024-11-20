import asyncio
import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from backend.database.db_config import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)

async def test_connection():
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        
        # Test connection
        await db_manager.connect()
        logging.info("Successfully connected to MongoDB Atlas!")
        
        # Test basic operations
        collection = db_manager.db.test_collection
        
        # Insert a test document
        result = await collection.insert_one({"test": "Hello MongoDB Atlas!"})
        logging.info(f"Inserted test document with ID: {result.inserted_id}")
        
        # Retrieve the document
        doc = await collection.find_one({"test": "Hello MongoDB Atlas!"})
        logging.info(f"Retrieved test document: {doc}")
        
        # Clean up - delete test document
        await collection.delete_one({"_id": result.inserted_id})
        logging.info("Test document deleted")
        
        # Close connection
        await db_manager.close()
        logging.info("Connection closed successfully")
        
    except Exception as e:
        logging.error(f"Error testing MongoDB connection: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_connection())
