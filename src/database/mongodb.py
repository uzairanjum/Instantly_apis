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
    
    def get_all_from_recycled_leads(self):
        """Get all documents from the recycled_leads collection sorted by updated_At in ascending order."""
        return self.collection.find().sort('updated_at', 1)  

    def update_by_email(self, email, update_fields):
        """Update a document in the recycled_leads collection based on email."""
        return self.collection.update_one({'email': email}, {'$set': update_fields})

    def delete_by_email(self, email):
        """Delete a document from the recycled_leads collection based on email."""
        return self.collection.delete_one({'email': email})


