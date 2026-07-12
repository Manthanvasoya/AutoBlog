from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime

class PlanDict(TypedDict, total=False):
    """Planner agent output"""
    target_audience: str
    tone: str
    needs_research: bool
    research_queries: List[str]
    outline_hints: List[str]
    visual_requirements: List[Dict[str, Any]]

class ResearchFactDict(TypedDict, total=False):
    """Individual research fact with source"""
    fact: str
    source: str
    relevance_score: float

class OutlineSection(TypedDict, total=False):
    """Individual section in the blog outline"""
    heading: str
    key_points: List[str]
    needs_visual: bool
    visual_type: str
    relevant_facts: List[ResearchFactDict]
    max_words: int

class OutlineDict(TypedDict, total=False):
    """Outline agent output"""
    title: str
    estimated_total_words: int
    sections: List[OutlineSection]

class ChartPath(TypedDict, total=False):
    """Chart metadata"""
    section_heading: str
    path: str

class SEODict(TypedDict, total=False):
    """SEO agent output"""
    tags: List[str]
    meta_description: str
    slug: str
    keywords: List[str]

class BlogState(TypedDict, total=False):
    """
    Shared LangGraph state for all agents and nodes.
    All blog generation data flows through this single TypedDict.
    """

    # ============ INPUT ============
    topic: str  # User-provided blog topic

    # ============ PLANNER AGENT OUTPUT ============
    plan: PlanDict  # Planning decision with needs_research flag

    # ============ RESEARCH AGENT OUTPUT ============
    summarized_facts: List[ResearchFactDict]  # Only extracted facts, never full articles

    # ============ OUTLINE AGENT OUTPUT ============
    outline: OutlineDict  # Blog structure with sections and pre-filtered facts

    # ============ WRITER AGENT OUTPUTS ============
    sections: List[str]  # Individual section content (list order = section order)
    draft: str  # Full blog in markdown (no images, no frontmatter yet)

    # ============ VISUAL AGENT OUTPUT ============
    chart_paths: List[ChartPath]  # Chart file paths with section headings
    cover_image_path: str  # Path to cover image

    # ============ SEO AGENT OUTPUT ============
    seo_tags: List[str]
    meta_description: str
    slug: str
    keywords: List[str]

    # ============ ASSEMBLER NODE OUTPUT ============
    assembled_blog: str  # Final markdown with SEO frontmatter + embedded charts

    # ============ CRITIC AGENT OUTPUTS ============
    critic_score: float  # Composite score (0.0 to 1.0)
    critic_feedback: str  # Detailed feedback for improvements
    iteration_count: int  # Number of retry iterations attempted

    # ============ PUBLISHER AGENT OUTPUT ============
    devto_url: str  # Live Dev.to article URL
    medium_url: str  # Live Medium article URL
    published: bool  # Whether successfully published

    # ============ INTERNAL TRACKING ============
    current_node: Optional[str]  # Which node is currently executing
    timestamp_created: Optional[datetime]  # When blog was created
    timestamp_published: Optional[datetime]  # When blog was published
    user_feedback: Optional[str]  # User feedback at checkpoint (HITL)
    error_message: Optional[str]  # Error if workflow failed

    # ============ OPTIONAL: RETRY/RESUME STATE ============
    last_checkpoint: Optional[str]  # Name of last HITL checkpoint
    thread_id: Optional[str]  # LangGraph thread ID for persistence
    execution_trace: List[Dict[str, Any]]  # Execution log of all nodes


# Type definitions for agent-specific state slices (for context pruning)

class PlannerInputState(TypedDict, total=False):
    """Minimal state passed to Planner agent"""
    topic: str

class PlannerOutputState(TypedDict, total=False):
    """Planner agent output"""
    plan: PlanDict

class ResearchInputState(TypedDict, total=False):
    """Minimal state passed to Research agent"""
    plan: PlanDict  # Only needs research_queries from plan

class ResearchOutputState(TypedDict, total=False):
    """Research agent output"""
    summarized_facts: List[ResearchFactDict]

class OutlineInputState(TypedDict, total=False):
    """Minimal state passed to Outline agent"""
    plan: PlanDict  # Only outline_hints + visual_requirements
    summarized_facts: List[ResearchFactDict]

class OutlineOutputState(TypedDict, total=False):
    """Outline agent output"""
    outline: OutlineDict

class WriterInputState(TypedDict, total=False):
    """Minimal state passed to Writer agent"""
    outline: OutlineDict
    plan: PlanDict  # Only tone + target_audience
    critic_feedback: Optional[str]  # If retry, include feedback

class WriterOutputState(TypedDict, total=False):
    """Writer agent output"""
    sections: List[str]
    draft: str

class VisualInputState(TypedDict, total=False):
    """Minimal state passed to Visual agent"""
    outline: OutlineDict  # Only sections with visual metadata
    topic: str
    plan: PlanDict  # Only tone

class VisualOutputState(TypedDict, total=False):
    """Visual agent output"""
    chart_paths: List[ChartPath]
    cover_image_path: str

class SEOInputState(TypedDict, total=False):
    """Minimal state passed to SEO agent"""
    topic: str
    outline: OutlineDict  # Only title and section headings

class SEOOutputState(TypedDict, total=False):
    """SEO agent output"""
    seo_tags: List[str]
    meta_description: str
    slug: str
    keywords: List[str]

class AssemblerInputState(TypedDict, total=False):
    """Minimal state passed to Assembler node"""
    draft: str
    chart_paths: List[ChartPath]
    cover_image_path: str
    seo_tags: List[str]
    meta_description: str
    slug: str
    outline: OutlineDict  # Only title

class AssemblerOutputState(TypedDict, total=False):
    """Assembler node output"""
    assembled_blog: str

class CriticInputState(TypedDict, total=False):
    """Minimal state passed to Critic agent"""
    assembled_blog: str
    summarized_facts: List[ResearchFactDict]
    iteration_count: int

class CriticOutputState(TypedDict, total=False):
    """Critic agent output"""
    critic_score: float
    critic_feedback: str
    iteration_count: int

class PublisherInputState(TypedDict, total=False):
    """Minimal state passed to Publisher agent"""
    assembled_blog: str
    cover_image_path: str
    seo_tags: List[str]
    meta_description: str
    slug: str

class PublisherOutputState(TypedDict, total=False):
    """Publisher agent output"""
    devto_url: str
    medium_url: str
    published: bool
