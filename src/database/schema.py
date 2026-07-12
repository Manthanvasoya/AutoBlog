"""
MongoDB schema definitions for AutoBlog application.
Note: MongoDB is schema-free, but we define expected structures here.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

# ============ BLOGS COLLECTION ============
# Stores final published blog records
BLOGS_SCHEMA = {
    "_id": "ObjectId",  # MongoDB auto-generated
    "topic": "str",  # Original user topic
    "title": "str",  # Final blog title
    "devto_url": "str",  # Published Dev.to article URL
    "medium_url": "str",  # Published Medium article URL
    "critic_score": "float",  # Final quality score (0.0-1.0)
    "word_count": "int",  # Total word count
    "section_count": "int",  # Number of sections
    "publish_timestamp": "datetime",  # When published
    "created_at": "datetime",  # When blog request created
}

# ============ BLOG_ASSETS COLLECTION ============
# Stores visual assets (charts, cover images) for each blog
BLOG_ASSETS_SCHEMA = {
    "_id": "ObjectId",
    "blog_id": "ObjectId",  # Reference to blogs collection
    "chart_paths": [
        {
            "section_heading": "str",  # Section title
            "path": "str",  # File path to saved chart
            "format": "str",  # png, jpg, etc.
        }
    ],
    "cover_image_path": "str",  # Path to cover image file
    "created_at": "datetime",
}

# ============ BLOG_SEO COLLECTION ============
# Stores SEO metadata for each blog
BLOG_SEO_SCHEMA = {
    "_id": "ObjectId",
    "blog_id": "ObjectId",  # Reference to blogs collection
    "seo_tags": ["str"],  # Platform tags (Dev.to, Medium)
    "meta_description": "str",  # Google search snippet
    "slug": "str",  # URL-friendly slug
    "keywords": ["str"],  # Primary keywords for ranking
    "created_at": "datetime",
}

# ============ BLOG_QUALITY_LOG COLLECTION ============
# Stores critic feedback and scores for every iteration
BLOG_QUALITY_LOG_SCHEMA = {
    "_id": "ObjectId",
    "blog_id": "ObjectId",  # Reference to blogs collection
    "iteration": "int",  # Which iteration (1, 2, 3...)
    "critic_score": "float",  # Depth/clarity/grounding score
    "depth_score": "float",  # Content coverage (0.0-1.0)
    "clarity_score": "float",  # Writing quality (0.0-1.0)
    "grounding_score": "float",  # Fact grounding (0.0-1.0)
    "critic_feedback": "str",  # Detailed feedback
    "passed": "bool",  # Whether this iteration passed
    "timestamp": "datetime",
}

# ============ RESEARCH_FACTS COLLECTION ============
# Stores extracted facts by topic for potential reuse
RESEARCH_FACTS_SCHEMA = {
    "_id": "ObjectId",
    "topic": "str",  # Blog topic
    "summarized_facts": [
        {
            "fact": "str",  # Single extracted fact
            "source": "str",  # Source URL
            "relevance_score": "float",  # Relevance (0.0-1.0)
        }
    ],
    "research_queries": ["str"],  # Queries used to find facts
    "created_at": "datetime",
    "used_in_blogs": ["ObjectId"],  # Blogs that used this research
}

# ============ EXECUTION_TRACE COLLECTION ============
# Stores execution logs for debugging and monitoring
EXECUTION_TRACE_SCHEMA = {
    "_id": "ObjectId",
    "blog_id": "ObjectId",  # Reference to blogs collection
    "node_name": "str",  # Which node executed
    "status": "str",  # success, failed, skipped
    "start_time": "datetime",
    "end_time": "datetime",
    "duration_seconds": "float",
    "error_message": "str",  # If failed
    "tokens_used": "int",  # LLM tokens (estimated)
}


def get_collection_names() -> List[str]:
    """Get list of all collection names"""
    return [
        "blogs",
        "blog_assets",
        "blog_seo",
        "blog_quality_log",
        "research_facts",
        "execution_trace",
    ]


def get_indexes() -> Dict[str, List[tuple]]:
    """
    MongoDB indexes for efficient queries.
    Returns dict of collection_name -> list of (field, direction) tuples
    """
    return {
        "blogs": [
            ("topic", 1),
            ("publish_timestamp", -1),
            ("created_at", -1),
        ],
        "blog_assets": [
            ("blog_id", 1),
        ],
        "blog_seo": [
            ("blog_id", 1),
            ("slug", 1),
        ],
        "blog_quality_log": [
            ("blog_id", 1),
            ("iteration", 1),
        ],
        "research_facts": [
            ("topic", 1),
            ("created_at", -1),
        ],
        "execution_trace": [
            ("blog_id", 1),
            ("node_name", 1),
        ],
    }
