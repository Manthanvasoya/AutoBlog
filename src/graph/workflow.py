"""
LangGraph Workflow Definition — 11-node blog generation pipeline.
Orchestrates all agents with conditional routing, checkpointing, and HITL integration.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from src.core.state import BlogState
from src.core.constants import NodeNames
from src.core.config import get_app_settings, get_app_config
from src.database.sqlite_checkpoint import initialize_checkpoint_manager

# Import agent nodes
from src.agents.planner_agent import planner_agent_sync as planner_agent
from src.agents.research_agent import research_agent
from src.agents.outline_agent import outline_agent
from src.agents.writer_agent import writer_node, write_section_agent, merge_sections
from src.agents.visual_agent import visual_agent
from src.agents.seo_agent import seo_agent
from src.agents.critic_agent import critic_agent
from src.agents.publisher_agent import publisher_agent

# Import utility nodes
from src.nodes.assembler_node import assembler_node


def create_blog_workflow():
    """
    Create the 11-node LangGraph workflow.

    Graph topology:
    START
      ↓
    1. Planner (HITL 1)
      ↓
    2. Research (conditional)
      ↓
    3. Outline (HITL 2)
      ↓
    4. Writer (Send API fan-out)
      ↓
    5+6. Visual + SEO (parallel)
      ↓
    Merge
      ↓
    7. Assembler (pure Python)
      ↓
    8. Critic (HITL 3, with retry)
      ↓
    9. Publisher
      ↓
    END
    """

    workflow = StateGraph(BlogState)

    # ============ NODE 1: PLANNER ============
    workflow.add_node(NodeNames.PLANNER, planner_agent)

    # ============ NODE 2: RESEARCH (conditional) ============
    def research_node(state):
        """Conditional wrapper: only runs if needs_research=True"""
        if state["plan"].get("needs_research", False):
            return research_agent(state)
        return {}

    workflow.add_node(NodeNames.RESEARCH, research_node)

    # ============ NODE 3: OUTLINE ============
    workflow.add_node(NodeNames.OUTLINE, outline_agent)

    # ============ NODE 4: WRITER (parallel sections via Send API) ============
    workflow.add_node(NodeNames.WRITER, writer_node)
    workflow.add_node(NodeNames.WRITE_SECTION, write_section_agent)

    # Merge node to combine all section outputs
    def merge_node(state):
        """Merge all written sections into draft"""
        # Collect all sections that were written
        sections = state.get("sections", [])
        if not isinstance(sections, list) or not sections:
            sections = ["No content"]
        draft = "\n\n".join(sections)
        return {"draft": draft}

    workflow.add_node("merge_sections", merge_node)

    # ============ NODES 5+6: VISUAL + SEO (parallel) ============
    workflow.add_node(NodeNames.VISUAL, visual_agent)
    workflow.add_node(NodeNames.SEO, seo_agent)

    # Merge node for Visual + SEO results
    def merge_parallel(state):
        """Merge Visual and SEO outputs"""
        return state  # Both already write to state

    workflow.add_node(NodeNames.MERGE_PARALLEL, merge_parallel)

    # ============ NODE 7: ASSEMBLER (pure Python) ============
    workflow.add_node(NodeNames.ASSEMBLER, assembler_node)

    # ============ NODE 8: CRITIC (HITL 3, with retry) ============
    workflow.add_node(NodeNames.CRITIC, critic_agent)

    # ============ NODE 9: PUBLISHER ============
    workflow.add_node(NodeNames.PUBLISHER, publisher_agent)

    # ============ CONDITIONAL ROUTING ============

    def route_after_planner(state):
        """Route after Planner: check needs_research flag"""
        if state["plan"].get("needs_research", False):
            return NodeNames.RESEARCH
        else:
            return NodeNames.OUTLINE

    def route_after_critic(state):
        """Route after Critic: check if should retry or proceed"""
        if state.get("_should_retry", False):
            # Loop back to Writer for retry
            return NodeNames.WRITER
        else:
            # Proceed to Publisher
            return NodeNames.PUBLISHER

    # ============ GRAPH EDGES ============

    # Start to Planner
    workflow.add_edge(START, NodeNames.PLANNER)

    # Planner to Research or Outline (conditional)
    workflow.add_conditional_edges(NodeNames.PLANNER, route_after_planner)

    # Research to Outline
    workflow.add_edge(NodeNames.RESEARCH, NodeNames.OUTLINE)

    # Outline to Writer
    workflow.add_edge(NodeNames.OUTLINE, NodeNames.WRITER)

    # Writer fan-out (Send API creates parallel write_section nodes)
    # Collect results
    workflow.add_edge(NodeNames.WRITE_SECTION, "merge_sections")

    # Merge sections to Visual and SEO (parallel)
    workflow.add_edge("merge_sections", NodeNames.VISUAL)
    workflow.add_edge("merge_sections", NodeNames.SEO)

    # Visual and SEO to merge
    workflow.add_edge(NodeNames.VISUAL, NodeNames.MERGE_PARALLEL)
    workflow.add_edge(NodeNames.SEO, NodeNames.MERGE_PARALLEL)

    # Merge parallel to Assembler
    workflow.add_edge(NodeNames.MERGE_PARALLEL, NodeNames.ASSEMBLER)

    # Assembler to Critic
    workflow.add_edge(NodeNames.ASSEMBLER, NodeNames.CRITIC)

    # Critic to Publisher or Writer (conditional retry)
    workflow.add_conditional_edges(NodeNames.CRITIC, route_after_critic)

    # Publisher to End
    workflow.add_edge(NodeNames.PUBLISHER, END)

    # ============ CHECKPOINTING ============
    # SQLite checkpointing for HITL pause/resume
    settings = get_app_settings()
    checkpoint_manager = initialize_checkpoint_manager(settings.sqlite_db_path)
    saver = checkpoint_manager.get_saver()

    # Compile graph with checkpointer
    graph = workflow.compile(checkpointer=saver)

    return graph


def get_workflow():
    """Get or create the blog workflow"""
    return create_blog_workflow()


if __name__ == "__main__":
    # Test graph creation
    graph = get_workflow()
    print("Graph nodes:", graph.nodes)
    print("Graph edges:", graph.edges)
    print("✓ Workflow created successfully")
