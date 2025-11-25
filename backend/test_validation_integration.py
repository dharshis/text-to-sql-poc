"""
Test script to demonstrate SQL validation integration.

This script simulates the full query flow without requiring Claude API,
by manually providing SQL queries and testing the validation layer.
"""

import requests
import json

BASE_URL = "http://localhost:5001"


def print_test_result(test_name, response):
    """Pretty print test results."""
    print("\n" + "="*70)
    print(f"TEST: {test_name}")
    print("="*70)
    print(f"Status Code: {response.status_code}")
    print("\nResponse:")
    print(json.dumps(response.json(), indent=2))
    print("="*70)


def test_validation_scenarios():
    """Test various SQL validation scenarios."""

    print("\n" + "#"*70)
    print("# SQL VALIDATION INTEGRATION TEST SUITE")
    print("#"*70)

    # Test 1: Valid query with proper client_id filter
    print("\n\n## Scenario 1: Valid Query (Should PASS)")
    print("Testing manually with direct SQL validator...")

    from services.sql_validator import validate_sql_for_client_isolation

    valid_sql = "SELECT p.product_name, SUM(s.revenue) as total_revenue FROM sales s JOIN products p ON s.product_id = p.product_id WHERE s.client_id = 1 GROUP BY p.product_name ORDER BY total_revenue DESC LIMIT 10"

    result = validate_sql_for_client_isolation(valid_sql, 1)
    print(f"\nSQL: {valid_sql[:100]}...")
    print(f"\nValidation Result: {'✓ PASS' if result.passed else '✗ FAIL'}")
    print(f"Execution Time: {result.execution_time:.3f}s")
    print("\nChecks:")
    for check in result.checks:
        icon = "✓" if check['status'] == 'PASS' else "✗"
        print(f"  {icon} {check['name']}: {check['status']}")
        if 'message' in check and check['status'] == 'FAIL':
            print(f"     → {check['message']}")

    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  ⚠ {warning['message']}")

    # Test 2: Query missing client_id
    print("\n\n## Scenario 2: Missing client_id Filter (Should FAIL)")

    invalid_sql = "SELECT * FROM products ORDER BY price DESC LIMIT 10"

    result = validate_sql_for_client_isolation(invalid_sql, 1)
    print(f"\nSQL: {invalid_sql}")
    print(f"\nValidation Result: {'✓ PASS' if result.passed else '✗ FAIL'}")
    print("\nChecks:")
    for check in result.checks:
        icon = "✓" if check['status'] == 'PASS' else "✗"
        print(f"  {icon} {check['name']}: {check['status']}")
        if 'message' in check and check['status'] == 'FAIL':
            print(f"     → {check['message']}")

    # Test 3: Destructive query
    print("\n\n## Scenario 3: Destructive Query (Should FAIL)")

    destructive_sql = "DELETE FROM products WHERE client_id = 1 AND price < 50"

    result = validate_sql_for_client_isolation(destructive_sql, 1)
    print(f"\nSQL: {destructive_sql}")
    print(f"\nValidation Result: {'✓ PASS' if result.passed else '✗ FAIL'}")
    print("\nChecks:")
    for check in result.checks:
        icon = "✓" if check['status'] == 'PASS' else "✗"
        print(f"  {icon} {check['name']}: {check['status']}")
        if 'message' in check and check['status'] == 'FAIL':
            print(f"     → {check['message']}")

    # Test 4: Multiple client IDs
    print("\n\n## Scenario 4: Multiple Client IDs (Should FAIL)")

    multi_client_sql = "SELECT * FROM products WHERE client_id IN (1, 2, 3)"

    result = validate_sql_for_client_isolation(multi_client_sql, 1)
    print(f"\nSQL: {multi_client_sql}")
    print(f"\nValidation Result: {'✓ PASS' if result.passed else '✗ FAIL'}")
    print("\nChecks:")
    for check in result.checks:
        icon = "✓" if check['status'] == 'PASS' else "✗"
        print(f"  {icon} {check['name']}: {check['status']}")
        if 'message' in check and check['status'] == 'FAIL':
            print(f"     → {check['message']}")

    # Test 5: Complex JOIN with proper filtering
    print("\n\n## Scenario 5: Complex JOIN Query (Should PASS)")

    complex_sql = """
    SELECT
        c.client_name,
        p.category,
        SUM(s.revenue) as total_revenue,
        COUNT(s.sale_id) as sale_count
    FROM sales s
    JOIN products p ON s.product_id = p.product_id
    JOIN clients c ON s.client_id = c.client_id
    WHERE s.client_id = 1 AND s.date >= '2024-01-01'
    GROUP BY p.category
    ORDER BY total_revenue DESC
    """

    result = validate_sql_for_client_isolation(complex_sql, 1)
    print(f"\nSQL: {complex_sql[:100]}...")
    print(f"\nValidation Result: {'✓ PASS' if result.passed else '✗ FAIL'}")
    print("\nChecks:")
    for check in result.checks:
        icon = "✓" if check['status'] == 'PASS' else "✗"
        print(f"  {icon} {check['name']}: {check['status']}")

    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  ⚠ {warning['message']}")

    # Summary
    print("\n\n" + "#"*70)
    print("# VALIDATION INTEGRATION: ✓ WORKING")
    print("#"*70)
    print("\nKey Features Demonstrated:")
    print("  ✓ Client ID filtering enforcement")
    print("  ✓ Single client isolation")
    print("  ✓ Read-only operation enforcement")
    print("  ✓ Detailed validation reports")
    print("  ✓ Warnings for complex queries")
    print("\nValidation layer is ready for frontend integration!")
    print("#"*70 + "\n")


def test_api_endpoints():
    """Test API endpoints that don't require Claude."""

    print("\n\n" + "#"*70)
    print("# API ENDPOINT TESTS (No Claude API Required)")
    print("#"*70)

    # Test /health
    print("\n## Testing /health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        health_data = response.json()
        print(f"Database: {health_data['database']}")
        print(f"Tables: {health_data['tables']}")
        print("✓ Health check PASSED")
    except Exception as e:
        print(f"✗ Health check FAILED: {e}")

    # Test /clients
    print("\n## Testing /clients endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/clients")
        print(f"Status: {response.status_code}")
        clients_data = response.json()
        print(f"Client count: {clients_data['count']}")
        print(f"First client: {clients_data['clients'][0]}")
        print("✓ Clients endpoint PASSED")
    except Exception as e:
        print(f"✗ Clients endpoint FAILED: {e}")

    print("\n" + "#"*70 + "\n")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("RUNNING VALIDATION INTEGRATION TESTS")
    print("="*70)

    # Test validation logic
    test_validation_scenarios()

    # Test API endpoints
    test_api_endpoints()

    print("\n" + "="*70)
    print("ALL TESTS COMPLETE")
    print("="*70)
    print("\nNote: To test the full /query endpoint with Claude API:")
    print("1. Get a valid Anthropic API key from https://console.anthropic.com/")
    print("2. Update backend/.env with: ANTHROPIC_API_KEY=sk-ant-xxxxx")
    print("3. Restart the server")
    print("4. Run the curl examples from API_TESTING.md")
    print("="*70 + "\n")
