import pymongo
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mongo_connection():
    try:
        # Load environment variables
        load_dotenv()
        
        # Get MongoDB URL
        mongo_url = os.getenv('MONGODB_URL')
        db_name = os.getenv('MONGODB_DB_NAME')
        
        logger.info("Attempting to connect to MongoDB...")
        
        # Create a MongoDB client
        client = pymongo.MongoClient(mongo_url)
        
        # Force a connection attempt
        client.admin.command('ping')
        
        logger.info("Successfully connected to MongoDB!")
        
        # Get database
        db = client[db_name]
        
        # Test database operations
        test_collection = db.test_collection
        
        # Insert a test document
        result = test_collection.insert_one({"test": "Hello MongoDB Atlas!"})
        logger.info(f"Inserted test document with ID: {result.inserted_id}")
        
        # Find the document
        doc = test_collection.find_one({"test": "Hello MongoDB Atlas!"})
        logger.info(f"Found document: {doc}")
        
        # Clean up
        test_collection.delete_one({"_id": result.inserted_id})
        logger.info("Test document deleted")
        
        # Close connection
        client.close()
        logger.info("Connection closed")
        
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {str(e)}")
        raise

if __name__ == "__main__":
    test_mongo_connection()
