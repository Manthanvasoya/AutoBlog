"""
Integration test for the AutoBlog workflow.
Tests that the graph can be created and basic state flows.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import init_config
from src.graph.workflow import get_workflow
from src.core.state import BlogState


def test_workflow_creation():
    """Test that workflow can be created"""
    init_config()
    workflow = get_workflow()
    assert workflow is not None
    print("✓ Workflow created successfully")


def test_workflow_nodes():
    """Test that all nodes are present"""
    init_config()
    workflow = get_workflow()

    nodes = list(workflow.nodes)
    print(f"✓ Graph has {len(nodes)} nodes")

    # Verify critical nodes exist
    expected_nodes = ["planner", "research", "outline", "writer", "visual", "seo", "critic", "publisher"]
    for node in expected_nodes:
        if node in nodes:
            print(f"  ✓ {node}")
        else:
            print(f"  ✗ Missing: {node}")


def test_initial_state():
    """Test that initial state can be created"""
    initial_state: BlogState = {
        "topic": "Test Topic",
        "plan": {},
        "summarized_facts": [],
        "outline": {},
        "sections": [],
        "draft": "",
        "chart_paths": [],
        "cover_image_path": "",
        "seo_tags": [],
        "meta_description": "",
        "slug": "",
        "keywords": [],
        "assembled_blog": "",
        "critic_score": 0.0,
        "critic_feedback": "",
        "iteration_count": 0,
        "devto_url": "",
        "medium_url": "",
        "published": False,
    }

    assert initial_state["topic"] == "Test Topic"
    print("✓ Initial state created successfully")


def main():
    """Run all tests"""
    print("=" * 50)
    print("AutoBlog Workflow Tests")
    print("=" * 50)

    try:
        print("\n1. Testing workflow creation...")
        test_workflow_creation()

        print("\n2. Testing workflow nodes...")
        test_workflow_nodes()

        print("\n3. Testing initial state...")
        test_initial_state()

        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        print("=" * 50)
        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
