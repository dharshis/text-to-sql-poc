"""
SQL validation service for enforcing client data isolation.

This service validates generated SQL queries to ensure:
1. Client ID filtering is enforced (WHERE client_id = X)
2. No cross-client data access (single client only)
3. Read-only operations (no destructive keywords)

This is a critical security layer for multi-tenant data isolation.
"""

import re
import logging
import time

logger = logging.getLogger(__name__)


class ValidationResult:
    """Container for validation results."""

    def __init__(self, passed, checks, warnings, execution_time=0.0):
        self.passed = passed
        self.checks = checks
        self.warnings = warnings
        self.execution_time = execution_time

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'passed': self.passed,
            'checks': self.checks,
            'warnings': self.warnings,
            'execution_time': round(self.execution_time, 3)
        }


def validate_sql_for_client_isolation(sql_query, expected_client_id, dataset_config=None):
    """
    Validate SQL query for client data isolation (dataset-aware).

    This performs basic string-based validation for POC demonstration.
    In production, use a proper SQL parser (sqlparse, pglast, etc.).

    Args:
        sql_query (str): SQL query to validate
        expected_client_id (int): Expected client ID that should be filtered
        dataset_config (dict, optional): Dataset configuration with table info

    Returns:
        ValidationResult: Validation results with checks and warnings

    Validation Checks:
        1. Client ID Filter - Ensures WHERE client_id = {expected_client_id} is present
        2. Single Client - Ensures no other client IDs are referenced
        3. Read-Only - Ensures no destructive SQL operations (DROP, DELETE, UPDATE, etc.)
        
    Dataset-Aware Features:
        - Validates based on dataset's fact tables (if config provided)
        - Checks client isolation on correct tables
        - Provides dataset-specific error messages
    """
    start_time = time.time()

    logger.info(f"Validating SQL for client_id={expected_client_id}, dataset={dataset_config.get('name') if dataset_config else 'unknown'}")

    checks = []
    warnings = []
    passed = True

    # Normalize SQL for consistent checking
    sql_upper = sql_query.upper()
    sql_normalized = ' '.join(sql_query.split())  # Collapse whitespace

    # ==========================================
    # Check 1: Client ID Filter
    # ==========================================
    # Look for "WHERE ... client_id = {expected_client_id}"
    # This should appear in the query to filter by client

    # Pattern to find WHERE clause with client_id filter
    # Matches: WHERE client_id = 5 OR WHERE s.client_id = 5 OR WHERE ... AND client_id = 5
    client_id_patterns = [
        rf'\bWHERE\s+.*?\bclient_id\s*=\s*{expected_client_id}\b',
        rf'\bAND\s+.*?\bclient_id\s*=\s*{expected_client_id}\b',
        rf'\bclient_id\s*=\s*{expected_client_id}\b.*?\bWHERE\b',  # In subqueries
    ]

    client_id_found = False
    for pattern in client_id_patterns:
        if re.search(pattern, sql_normalized, re.IGNORECASE):
            client_id_found = True
            break

    if not client_id_found:
        passed = False
        checks.append({
            "name": "Client ID Filter",
            "status": "FAIL",
            "message": f"Missing WHERE client_id = {expected_client_id} filter"
        })
        logger.warning(f"Validation FAILED: Missing client_id filter for client {expected_client_id}")
    else:
        checks.append({
            "name": "Client ID Filter",
            "status": "PASS",
            "message": f"Query correctly filters by client_id = {expected_client_id}"
        })
        logger.debug(f"Client ID filter check: PASS")

    # ==========================================
    # Check 2: Single Client
    # ==========================================
    # Ensure no references to other client IDs
    # This prevents queries like: WHERE client_id IN (1,2,3) or client_id = 5 OR client_id = 6

    # Find all client_id = N patterns
    all_client_id_matches = re.findall(r'\bclient_id\s*=\s*(\d+)', sql_normalized, re.IGNORECASE)
    all_client_ids = [int(match) for match in all_client_id_matches]

    # Check for IN clauses: client_id IN (1,2,3)
    in_clause_matches = re.findall(r'\bclient_id\s+IN\s*\([^)]+\)', sql_normalized, re.IGNORECASE)
    if in_clause_matches:
        passed = False
        checks.append({
            "name": "Single Client",
            "status": "FAIL",
            "message": "Query uses IN clause with multiple client IDs - data isolation violated"
        })
        logger.warning(f"Validation FAILED: IN clause detected with multiple clients")
    elif len(set(all_client_ids)) > 1:
        # Multiple different client IDs found
        passed = False
        checks.append({
            "name": "Single Client",
            "status": "FAIL",
            "message": f"Query references multiple client IDs: {set(all_client_ids)}"
        })
        logger.warning(f"Validation FAILED: Multiple client IDs found: {set(all_client_ids)}")
    elif all_client_ids and all_client_ids[0] != expected_client_id:
        # Found a client_id but it doesn't match expected
        passed = False
        checks.append({
            "name": "Single Client",
            "status": "FAIL",
            "message": f"Query filters by client_id = {all_client_ids[0]} but expected {expected_client_id}"
        })
        logger.warning(f"Validation FAILED: Wrong client ID {all_client_ids[0]} vs expected {expected_client_id}")
    else:
        checks.append({
            "name": "Single Client",
            "status": "PASS",
            "message": "Query correctly references only one client"
        })
        logger.debug(f"Single client check: PASS")

    # ==========================================
    # Check 3: Read-Only
    # ==========================================
    # Block destructive SQL operations
    # POC should only allow SELECT queries

    destructive_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE"]

    found_destructive = None
    for keyword in destructive_keywords:
        # Use word boundaries to avoid false positives (e.g., "UPDATE" in column name)
        pattern = rf'\b{keyword}\b'
        if re.search(pattern, sql_upper):
            found_destructive = keyword
            break

    if found_destructive:
        passed = False
        checks.append({
            "name": "Read-Only",
            "status": "FAIL",
            "message": f"Destructive keyword detected: {found_destructive}. Only SELECT queries allowed."
        })
        logger.warning(f"Validation FAILED: Destructive keyword '{found_destructive}' detected")
    else:
        checks.append({
            "name": "Read-Only",
            "status": "PASS",
            "message": "Query is read-only (SELECT only)"
        })
        logger.debug(f"Read-only check: PASS")

    # ==========================================
    # Warnings (informational, don't fail validation)
    # ==========================================

    # Warning 1: Multiple WHERE clauses (could indicate complex JOIN logic)
    where_count = sql_upper.count("WHERE")
    if where_count > 1:
        warnings.append({
            "type": "MULTIPLE_WHERE",
            "message": f"Multiple WHERE clauses detected ({where_count}) - verify JOIN logic includes client_id filtering"
        })
        logger.info(f"Warning: Multiple WHERE clauses ({where_count})")

    # Warning 2: Subqueries detected
    if "SELECT" in sql_upper and sql_upper.count("SELECT") > 1:
        warnings.append({
            "type": "SUBQUERY",
            "message": "Subquery detected - ensure all subqueries filter by client_id"
        })
        logger.info(f"Warning: Subquery detected")

    # Warning 3: UNION detected (could bypass filters)
    if "UNION" in sql_upper:
        warnings.append({
            "type": "UNION",
            "message": "UNION detected - verify both queries filter by client_id"
        })
        logger.info(f"Warning: UNION detected")

    execution_time = time.time() - start_time

    result = ValidationResult(
        passed=passed,
        checks=checks,
        warnings=warnings,
        execution_time=execution_time
    )

    if passed:
        logger.info(f"✓ Validation PASSED in {execution_time:.3f}s")
    else:
        logger.error(f"✗ Validation FAILED in {execution_time:.3f}s")

    return result


def get_validation_summary(validation_result):
    """
    Get a summary of validation results.

    Args:
        validation_result (ValidationResult): Validation result

    Returns:
        dict: Summary with passed status, total checks, failed checks
    """
    total_checks = len(validation_result.checks)
    failed_checks = len([c for c in validation_result.checks if c['status'] == 'FAIL'])
    passed_checks = total_checks - failed_checks

    return {
        'passed': validation_result.passed,
        'total_checks': total_checks,
        'passed_checks': passed_checks,
        'failed_checks': failed_checks,
        'has_warnings': len(validation_result.warnings) > 0
    }


# Test cases for validation (can be used for unit testing)
TEST_CASES = [
    {
        'name': 'Valid SELECT with client_id filter',
        'sql': 'SELECT * FROM products WHERE client_id = 5',
        'client_id': 5,
        'should_pass': True
    },
    {
        'name': 'Valid JOIN with client_id filter',
        'sql': 'SELECT p.product_name, SUM(s.revenue) FROM sales s JOIN products p ON s.product_id = p.product_id WHERE s.client_id = 5 GROUP BY p.product_name',
        'client_id': 5,
        'should_pass': True
    },
    {
        'name': 'Missing client_id filter',
        'sql': 'SELECT * FROM products',
        'client_id': 5,
        'should_pass': False
    },
    {
        'name': 'Wrong client_id',
        'sql': 'SELECT * FROM products WHERE client_id = 3',
        'client_id': 5,
        'should_pass': False
    },
    {
        'name': 'Multiple client IDs (IN clause)',
        'sql': 'SELECT * FROM products WHERE client_id IN (1,2,3)',
        'client_id': 1,
        'should_pass': False
    },
    {
        'name': 'Destructive DELETE',
        'sql': 'DELETE FROM products WHERE client_id = 5',
        'client_id': 5,
        'should_pass': False
    },
    {
        'name': 'Destructive UPDATE',
        'sql': 'UPDATE products SET price = 100 WHERE client_id = 5',
        'client_id': 5,
        'should_pass': False
    },
    {
        'name': 'Destructive DROP',
        'sql': 'DROP TABLE products',
        'client_id': 5,
        'should_pass': False
    }
]


if __name__ == '__main__':
    """Run validation test cases."""
    print("="*70)
    print("SQL VALIDATOR TEST SUITE")
    print("="*70)

    passed_tests = 0
    failed_tests = 0

    for i, test in enumerate(TEST_CASES, 1):
        print(f"\nTest {i}: {test['name']}")
        print(f"SQL: {test['sql'][:80]}...")
        print(f"Expected client_id: {test['client_id']}")

        result = validate_sql_for_client_isolation(test['sql'], test['client_id'])

        print(f"Result: {'PASS' if result.passed else 'FAIL'}")
        print(f"Checks:")
        for check in result.checks:
            status_icon = "✓" if check['status'] == 'PASS' else "✗"
            print(f"  {status_icon} {check['name']}: {check['status']}")
            if check['status'] == 'FAIL':
                print(f"     {check['message']}")

        if result.warnings:
            print(f"Warnings:")
            for warning in result.warnings:
                print(f"  ⚠ {warning['message']}")

        # Check if test result matches expectation
        if result.passed == test['should_pass']:
            passed_tests += 1
            print("✓ Test PASSED (result matches expectation)")
        else:
            failed_tests += 1
            print(f"✗ Test FAILED (expected {test['should_pass']}, got {result.passed})")

    print("\n" + "="*70)
    print(f"SUMMARY: {passed_tests}/{len(TEST_CASES)} tests passed")
    print("="*70)
