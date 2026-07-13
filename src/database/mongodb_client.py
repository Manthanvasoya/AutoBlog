"""
MongoDB client for AutoBlog application data persistence.
Handles all application-level data: blogs, assets, SEO metadata, quality logs.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId


class MongoDBClient:
    """Client for MongoDB operations"""

    def __init__(self, uri: str, database: str, timeout_seconds: int = 30):
        """
        Initialize MongoDB client.

        Args:
            uri: MongoDB connection URI
            database: Database name
            timeout_seconds: Connection timeout
        """
        self.uri = uri
        self.database_name = database
        self.timeout_seconds = timeout_seconds
        self._client: Optional[MongoClient] = None
        self._db = None

    def connect(self) -> None:
        """Connect to MongoDB"""
        try:
            self._client = MongoClient(self.uri, serverSelectionTimeoutMS=self.timeout_seconds * 1000)
            # Test connection
            self._client.admin.command("ping")
            self._db = self._client[self.database_name]
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")

    def disconnect(self) -> None:
        """Disconnect from MongoDB"""
        if self._client:
            self._client.close()

    def get_collection(self, collection_name: str) -> Collection:
        """Get a collection from the database"""
        if self._db is None:
            raise RuntimeError("Not connected to MongoDB. Call connect() first.")
        return self._db[collection_name]

    # ============ BLOGS COLLECTION ============

    def save_blog(self, blog_data: Dict[str, Any]) -> str:
        """
        Save a blog record.

        Args:
            blog_data: Blog data dict

        Returns:
            MongoDB _id of saved document
        """
        collection = self.get_collection("blogs")
        blog_data["created_at"] = blog_data.get("created_at", datetime.utcnow())
        result = collection.insert_one(blog_data)
        return str(result.inserted_id)

    def get_blog(self, blog_id: str) -> Optional[Dict[str, Any]]:
        """Get a blog by ID"""
        collection = self.get_collection("blogs")
        return collection.find_one({"_id": ObjectId(blog_id)})

    def get_blogs_by_topic(self, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get blogs by topic"""
        collection = self.get_collection("blogs")
        return list(collection.find({"topic": topic}).limit(limit).sort("created_at", -1))

    def get_recent_blogs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent published blogs"""
        collection = self.get_collection("blogs")
        return list(collection.find().limit(limit).sort("publish_timestamp", -1))

    def update_blog(self, blog_id: str, updates: Dict[str, Any]) -> bool:
        """Update a blog record"""
        collection = self.get_collection("blogs")
        result = collection.update_one({"_id": ObjectId(blog_id)}, {"$set": updates})
        return result.modified_count > 0

    # ============ BLOG_ASSETS COLLECTION ============

    def save_blog_assets(self, blog_id: str, assets_data: Dict[str, Any]) -> str:
        """Save visual assets for a blog"""
        collection = self.get_collection("blog_assets")
        assets_data["blog_id"] = ObjectId(blog_id)
        assets_data["created_at"] = datetime.utcnow()
        result = collection.insert_one(assets_data)
        return str(result.inserted_id)

    def get_blog_assets(self, blog_id: str) -> Optional[Dict[str, Any]]:
        """Get assets for a blog"""
        collection = self.get_collection("blog_assets")
        return collection.find_one({"blog_id": ObjectId(blog_id)})

    # ============ BLOG_SEO COLLECTION ============

    def save_blog_seo(self, blog_id: str, seo_data: Dict[str, Any]) -> str:
        """Save SEO metadata for a blog"""
        collection = self.get_collection("blog_seo")
        seo_data["blog_id"] = ObjectId(blog_id)
        seo_data["created_at"] = datetime.utcnow()
        result = collection.insert_one(seo_data)
        return str(result.inserted_id)

    def get_blog_seo(self, blog_id: str) -> Optional[Dict[str, Any]]:
        """Get SEO metadata for a blog"""
        collection = self.get_collection("blog_seo")
        return collection.find_one({"blog_id": ObjectId(blog_id)})

    def get_blog_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get blog by SEO slug"""
        collection = self.get_collection("blog_seo")
        seo_data = collection.find_one({"slug": slug})
        if not seo_data:
            return None
        # Return the blog instead of SEO data
        return self.get_blog(str(seo_data["blog_id"]))

    # ============ BLOG_QUALITY_LOG COLLECTION ============

    def save_quality_log(self, blog_id: str, iteration: int, quality_data: Dict[str, Any]) -> str:
        """Save quality assessment log for an iteration"""
        collection = self.get_collection("blog_quality_log")
        quality_data["blog_id"] = ObjectId(blog_id)
        quality_data["iteration"] = iteration
        quality_data["timestamp"] = datetime.utcnow()
        result = collection.insert_one(quality_data)
        return str(result.inserted_id)

    def get_quality_logs(self, blog_id: str) -> List[Dict[str, Any]]:
        """Get all quality logs for a blog"""
        collection = self.get_collection("blog_quality_log")
        return list(collection.find({"blog_id": ObjectId(blog_id)}).sort("iteration", 1))

    # ============ RESEARCH_FACTS COLLECTION ============

    def save_research_facts(self, topic: str, research_data: Dict[str, Any]) -> str:
        """Save research facts for a topic"""
        collection = self.get_collection("research_facts")
        research_data["topic"] = topic
        research_data["created_at"] = datetime.utcnow()
        research_data["used_in_blogs"] = []
        result = collection.insert_one(research_data)
        return str(result.inserted_id)

    def get_research_facts(self, topic: str) -> Optional[Dict[str, Any]]:
        """Get cached research facts for a topic"""
        collection = self.get_collection("research_facts")
        return collection.find_one({"topic": topic})

    def update_research_fact_usage(self, research_id: str, blog_id: str) -> bool:
        """Record that a research fact was used in a blog"""
        collection = self.get_collection("research_facts")
        result = collection.update_one(
            {"_id": ObjectId(research_id)},
            {"$addToSet": {"used_in_blogs": ObjectId(blog_id)}},
        )
        return result.modified_count > 0

    # ============ EXECUTION_TRACE COLLECTION ============

    def save_execution_trace(self, blog_id: str, trace_data: Dict[str, Any]) -> str:
        """Save execution trace log for debugging"""
        collection = self.get_collection("execution_trace")
        trace_data["blog_id"] = ObjectId(blog_id)
        result = collection.insert_one(trace_data)
        return str(result.inserted_id)

    def get_execution_trace(self, blog_id: str) -> List[Dict[str, Any]]:
        """Get execution trace for a blog"""
        collection = self.get_collection("execution_trace")
        return list(collection.find({"blog_id": ObjectId(blog_id)}).sort("start_time", 1))

    # ============ UTILITY METHODS ============

    def search_blogs(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search blogs by topic or title"""
        collection = self.get_collection("blogs")
        return list(
            collection.find(
                {
                    "$or": [
                        {"topic": {"$regex": query, "$options": "i"}},
                        {"title": {"$regex": query, "$options": "i"}},
                    ]
                }
            )
            .limit(limit)
            .sort("created_at", -1)
        )

    def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        db = self._db
        return {
            "total_blogs": db["blogs"].count_documents({}),
            "published_blogs": db["blogs"].count_documents({"published": True}),
            "total_research_facts": db["research_facts"].count_documents({}),
            "quality_logs": db["blog_quality_log"].count_documents({}),
        }


def create_mongodb_client(uri: str, database: str, timeout_seconds: int = 30) -> MongoDBClient:
    """Create and connect MongoDB client"""
    client = MongoDBClient(uri, database, timeout_seconds)
    client.connect()
    return client
