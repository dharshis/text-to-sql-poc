"""
Test service integration for Story 5.
Verifies dataset_id flows correctly through all services.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.agentic_text2sql_service import AgenticText2SQLService
from services.claude_service import ClaudeService


def test_agentic_service_accepts_dataset_id():
    """Test AgenticText2SQLService accepts dataset_id parameter"""
    service = AgenticText2SQLService(dataset_id='em_market')
    assert service.dataset_id == 'em_market', "AgenticText2SQLService should store dataset_id"
    assert service.claude_service.dataset_id == 'em_market', "ClaudeService should receive dataset_id"
    print("✓ AgenticText2SQLService passes dataset_id to ClaudeService")


def test_service_without_dataset_id():
    """Test services work without dataset_id (backward compatibility)"""
    service = AgenticText2SQLService()
    assert service.dataset_id is None, "dataset_id should default to None"
    assert service.claude_service.dataset_id is None, "ClaudeService dataset_id should be None"
    print("✓ Services work without dataset_id (fallback behavior)")


def test_claude_service_dataset_id():
    """Test ClaudeService stores dataset_id"""
    claude = ClaudeService(dataset_id='em_market')
    assert claude.dataset_id == 'em_market', "ClaudeService should store dataset_id"
    print("✓ ClaudeService stores dataset_id")


def test_claude_service_loads_metadata():
    """Test ClaudeService loads dataset-specific instructions"""
    claude = ClaudeService(dataset_id='em_market')
    # Should have loaded instructions from metadata
    assert claude.dataset_specific_instructions != "", "Should have loaded metadata instructions"
    assert len(claude.dataset_specific_instructions) > 100, "Instructions should have content"
    print(f"✓ ClaudeService loaded {len(claude.dataset_specific_instructions)} chars of metadata")


def test_dataset_id_in_multiple_services():
    """Test dataset_id consistency across multiple service instances"""
    agentic = AgenticText2SQLService(dataset_id='em_market')
    claude = ClaudeService(dataset_id='em_market')

    assert agentic.dataset_id == claude.dataset_id, "Both services should have same dataset_id"
    assert agentic.claude_service.dataset_id == claude.dataset_id, "Nested service should match"
    print("✓ Dataset ID consistent across multiple service instances")


if __name__ == '__main__':
    print("="*70)
    print("Story 5: Service Integration Test Suite")
    print("="*70)
    print()

    try:
        test_agentic_service_accepts_dataset_id()
        test_service_without_dataset_id()
        test_claude_service_dataset_id()
        test_claude_service_loads_metadata()
        test_dataset_id_in_multiple_services()

        print()
        print("="*70)
        print("✅ All 5 tests passed!")
        print("="*70)

    except AssertionError as e:
        print()
        print("="*70)
        print(f"❌ Test failed: {e}")
        print("="*70)
        sys.exit(1)
    except Exception as e:
        print()
        print("="*70)
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print("="*70)
        sys.exit(1)
