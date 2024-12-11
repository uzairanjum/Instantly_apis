from pymongo import MongoClient
from src.settings import settings


class MongoDBClient:

    def __init__(self):
        self.client = MongoClient(settings.MONGODB_URI)
        self.collection = self.get_collection('recycled_leads')  # Set the collection here

    def get_collection(self, collection_name):
        return self.client['instantly'][collection_name]  # Specify the database name

    def insert_into_recycled_leads(self, document):
        """Insert a document into the recycled_leads collection."""
        return self.collection.insert_one(document)

    def get_from_recycled_leads_by_email(self, email):
        """Get documents from the recycled_leads collection based on a query."""
        return self.collection.find_one({'email': email})
    
    def get_all_from_recycled_leads(self, offset=0, limit=100):
        print(f"offset {offset}")
        print(f"limit {limit}")
        """Get all documents from the recycled_leads collection sorted by updated_at in ascending order.
        
        Args:
            offset (int): The number of documents to skip.
            limit (int): The maximum number of documents to return. If 0, returns all documents.
        """
        query = self.collection.find().sort('updated_at', 1).skip(offset).limit(limit)

        return query

    def update_by_email(self, email, update_fields):
        """Update a document in the recycled_leads collection based on email."""
        return self.collection.update_one({'email': email}, {'$set': update_fields})

    def delete_by_email(self, email):
        """Delete a document from the recycled_leads collection based on email."""
        return self.collection.delete_one({'email': email})


