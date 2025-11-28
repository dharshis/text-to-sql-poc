#!/usr/bin/env python3
"""
Test script for metadata integration system.

Tests:
1. Metadata loader for em_market dataset
2. Business rules retrieval
3. Query patterns retrieval
4. Table metadata retrieval
5. Sample data fetching
6. Tool execution
"""

import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_metadata_loader():
    """Test basic metadata loading."""
    print("\n" + "=" * 70)
    print("TEST 1: Metadata Loader")
    print("=" * 70)
    
    from services.metadata_loader import load_dataset_metadata
    
    loader = load_dataset_metadata("em_market")
    stats = loader.get_statistics()
    
    print(f"\nDataset: {stats['dataset_id']}")
    print(f"Total Documents: {stats['total_documents']}")
    print(f"\nBy Type:")
    for doc_type, count in stats['by_type'].items():
        print(f"  • {doc_type}: {count}")
    print(f"\nUnique Files: {stats['unique_files']}")
    print(f"Metadata Directory: {stats['metadata_directory']}")
    
    # Show sample business rules
    rules = loader.get_documents_by_type("business_rule")
    if rules:
        print(f"\n📋 Sample Business Rules:")
        for rule in rules[:3]:
            title = rule.metadata.get('rule_title', 'Unknown')
            print(f"  • {title}")
    
    return loader


def test_business_rules_search(loader):
    """Test searching business rules."""
    print("\n" + "=" * 70)
    print("TEST 2: Business Rules Search")
    print("=" * 70)
    
    test_queries = [
        "market size by country",
        "year over year growth",
        "forecast CAGR"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        results = loader.search_content(query)
        
        # Filter for business rules only
        rule_results = [doc for doc in results if doc.metadata.get('type') == 'business_rule']
        
        print(f"   Found {len(rule_results)} relevant rules:")
        for doc in rule_results[:2]:
            title = doc.metadata.get('rule_title', doc.section)
            print(f"   • {title}")


def test_metadata_tools():
    """Test metadata tools integration."""
    print("\n" + "=" * 70)
    print("TEST 3: Metadata Tools")
    print("=" * 70)
    
    from services.agent_tools import create_metadata_tools_for_dataset
    
    dataset_id = "em_market"
    db_path = "../data/market_size.db"
    
    tools = create_metadata_tools_for_dataset(dataset_id, db_path)
    
    print(f"\n✅ Created {len(tools)} tools:")
    for tool_name, tool in tools.items():
        print(f"   • {tool_name}: {tool.description}")
    
    # Test search_metadata tool
    print("\n🔧 Testing search_metadata tool...")
    result = tools['search_metadata'].execute(
        query="latest year market size",
        top_k=3
    )
    
    if result['success']:
        print(f"   ✅ Success! Execution time: {result['elapsed']:.3f}s")
        print(f"   Found {len(result['result']['business_rules'])} business rules")
        print(f"   Found {len(result['result']['query_patterns'])} query patterns")
        
        # Show formatted context preview
        context = result['result']['formatted_context']
        print(f"\n   📝 Context preview (first 400 chars):")
        print("   " + context[:400].replace('\n', '\n   ') + "...")
    else:
        print(f"   ❌ Failed: {result['error']}")
    
    # Test get_table_schema tool
    print("\n🔧 Testing get_table_schema tool...")
    result = tools['get_table_schema'].execute(table_name="fact_market_size")
    
    if result['success']:
        print(f"   ✅ Success! Execution time: {result['elapsed']:.3f}s")
        print(f"   Found {len(result['result']['table_metadata'])} metadata documents")
    else:
        print(f"   ❌ Failed: {result['error']}")
    
    # Test get_sample_data tool
    print("\n🔧 Testing get_sample_data tool...")
    result = tools['get_sample_data'].execute(
        table_name="dim_geography",
        limit=3
    )
    
    if result['success']:
        print(f"   ✅ Success! Execution time: {result['elapsed']:.3f}s")
        samples = result['result']['samples']
        print(f"   Retrieved {len(samples)} sample rows")
        if samples:
            print(f"\n   Sample row 1:")
            for key, value in list(samples[0].items())[:5]:
                print(f"      {key}: {value}")
    else:
        print(f"   ❌ Failed: {result['error']}")


def test_query_patterns():
    """Test query pattern retrieval."""
    print("\n" + "=" * 70)
    print("TEST 4: Query Patterns")
    print("=" * 70)
    
    from services.metadata_loader import load_dataset_metadata
    
    loader = load_dataset_metadata("em_market")
    patterns = loader.get_documents_by_type("query_pattern")
    
    print(f"\n📊 Total Query Patterns: {len(patterns)}")
    
    if patterns:
        print(f"\n📝 Sample Patterns:")
        for pattern in patterns[:5]:
            title = pattern.metadata.get('pattern_title', 'Unknown')
            print(f"   • {title}")


def test_table_metadata():
    """Test table metadata retrieval."""
    print("\n" + "=" * 70)
    print("TEST 5: Table Metadata")
    print("=" * 70)
    
    from services.metadata_loader import load_dataset_metadata
    
    loader = load_dataset_metadata("em_market")
    table_docs = loader.get_documents_by_type("table_metadata")
    
    # Group by file
    by_file = {}
    for doc in table_docs:
        file_name = doc.file_name
        if file_name not in by_file:
            by_file[file_name] = []
        by_file[file_name].append(doc)
    
    print(f"\n📊 Tables with Metadata: {len(by_file)}")
    
    for file_name, docs in list(by_file.items())[:5]:
        print(f"\n   📄 {file_name}:")
        print(f"      Sections: {len(docs)}")
        section_names = [doc.metadata.get('section_title', doc.section) for doc in docs]
        print(f"      {', '.join(section_names[:3])}")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("🚀 METADATA SYSTEM TEST SUITE")
    print("=" * 70)
    
    try:
        # Test 1: Metadata Loader
        loader = test_metadata_loader()
        
        # Test 2: Business Rules Search
        test_business_rules_search(loader)
        
        # Test 3: Metadata Tools
        test_metadata_tools()
        
        # Test 4: Query Patterns
        test_query_patterns()
        
        # Test 5: Table Metadata
        test_table_metadata()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print("\nNext Steps:")
        print("1. Integrate metadata tools into agentic_text2sql_service.py")
        print("2. Add metadata context to SQL generation prompts")
        print("3. Test with real queries through the API")
        print("4. Monitor improvement in query accuracy")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()

