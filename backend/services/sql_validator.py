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
    Validate SQL query for client data isolation (method-driven validation).

    This performs basic string-based validation for POC demonstration.
    In production, use a proper SQL parser (sqlparse, pglast, etc.).

    Args:
        sql_query (str): SQL query to validate
        expected_client_id (int): Expected client ID that should be filtered
        dataset_config (dict, optional): Dataset configuration with client_isolation info

    Returns:
        ValidationResult: Validation results with checks and warnings

    Validation Checks:
        1. Client ID Filter - Ensures proper filter based on isolation method
        2. Single Client - Ensures no other client/corporation IDs are referenced
        3. Read-Only - Ensures no destructive SQL operations (DROP, DELETE, UPDATE, etc.)

    Method-Driven Features:
        - Validates based on config's isolation method ("row-level" or "brand-hierarchy")
        - Uses config's filter_field (client_id, corp_id, etc.)
        - Adapts validation patterns to dataset requirements
        - Provides method-specific error messages
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
    # Check 1: Client/Corporation ID Filter (MANDATORY - Method-Driven)
    # ==========================================
    # ALL datasets MUST filter by client/corporation ID
    # Validation method is determined by config, not hardcoded table names

    # Determine isolation method from config
    filter_field = "client_id"  # Default
    filter_method = "row-level"  # Default

    if dataset_config and 'client_isolation' in dataset_config:
        client_iso = dataset_config['client_isolation']
        filter_method = client_iso.get('method', 'row-level')
        filter_field = client_iso.get('filter_field', 'client_id')
    
    # Look for the appropriate filter pattern based on method
    if filter_method == "brand-hierarchy":
        # Brand-hierarchy method: check for filter_field anywhere in query
        # More flexible validation - allows complex join patterns
        filter_patterns = [
            rf'\bWHERE\s+.*?\b{filter_field}\s*=\s*{expected_client_id}\b',
            rf'\bAND\s+.*?\b{filter_field}\s*=\s*{expected_client_id}\b',
            rf'\b{filter_field}\s*=\s*{expected_client_id}\b',  # Anywhere in query
        ]

        filter_found = False
        for pattern in filter_patterns:
            if re.search(pattern, sql_normalized, re.IGNORECASE):
                filter_found = True
                break

        if not filter_found:
            passed = False
            checks.append({
                "name": "Client ID Filter",
                "status": "FAIL",
                "message": f"Missing {filter_field} = {expected_client_id} filter (method: {filter_method})"
            })
            logger.warning(f"Validation FAILED: Missing {filter_field} filter for client {expected_client_id}")
        else:
            checks.append({
                "name": "Client ID Filter",
                "status": "PASS",
                "message": f"Found {filter_field} = {expected_client_id} filter"
            })
            logger.debug(f"{filter_field} filter check: PASS")
    
    else:
        # Default: row-level filtering (generic filter_field)
        # Pattern to find WHERE clause with filter_field filter
        # Matches: WHERE filter_field = X OR WHERE t.filter_field = X OR WHERE ... AND filter_field = X
        filter_patterns = [
            rf'\bWHERE\s+.*?\b{filter_field}\s*=\s*{expected_client_id}\b',
            rf'\bAND\s+.*?\b{filter_field}\s*=\s*{expected_client_id}\b',
            rf'\b{filter_field}\s*=\s*{expected_client_id}\b.*?\bWHERE\b',  # In subqueries
        ]

        filter_found = False
        for pattern in filter_patterns:
            if re.search(pattern, sql_normalized, re.IGNORECASE):
                filter_found = True
                break

        if not filter_found:
            passed = False
            checks.append({
                "name": "Client ID Filter",
                "status": "FAIL",
                "message": f"Missing WHERE {filter_field} = {expected_client_id} filter"
            })
            logger.warning(f"Validation FAILED: Missing {filter_field} filter for client {expected_client_id}")
        else:
            checks.append({
                "name": "Client ID Filter",
                "status": "PASS",
                "message": f"Query correctly filters by {filter_field} = {expected_client_id}"
            })
            logger.debug(f"{filter_field} filter check: PASS")

    # ==========================================
    # Check 2: Single Client
    # ==========================================
    # Ensure no references to other client/corporation IDs
    # This prevents queries like: WHERE filter_field IN (1,2,3) or filter_field = 5 OR filter_field = 6

    # Find all filter_field = N patterns
    all_filter_matches = re.findall(rf'\b{filter_field}\s*=\s*(\d+)', sql_normalized, re.IGNORECASE)
    all_filter_ids = [int(match) for match in all_filter_matches]

    # Check for IN clauses: filter_field IN (1,2,3)
    in_clause_matches = re.findall(rf'\b{filter_field}\s+IN\s*\([^)]+\)', sql_normalized, re.IGNORECASE)
    if in_clause_matches:
        passed = False
        checks.append({
            "name": "Single Client",
            "status": "FAIL",
            "message": f"Query uses IN clause with multiple {filter_field}s - data isolation violated"
        })
        logger.warning(f"Validation FAILED: IN clause detected with multiple {filter_field}s")
    elif len(set(all_filter_ids)) > 1:
        # Multiple different filter IDs found
        passed = False
        checks.append({
            "name": "Single Client",
            "status": "FAIL",
            "message": f"Query references multiple {filter_field}s: {set(all_filter_ids)}"
        })
        logger.warning(f"Validation FAILED: Multiple {filter_field}s found: {set(all_filter_ids)}")
    elif all_filter_ids and all_filter_ids[0] != expected_client_id:
        # Found a filter_field but it doesn't match expected
        passed = False
        checks.append({
            "name": "Single Client",
            "status": "FAIL",
            "message": f"Query filters by {filter_field} = {all_filter_ids[0]} but expected {expected_client_id}"
        })
        logger.warning(f"Validation FAILED: Wrong {filter_field} {all_filter_ids[0]} vs expected {expected_client_id}")
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
            "message": f"Multiple WHERE clauses detected ({where_count}) - verify JOIN logic includes {filter_field} filtering"
        })
        logger.info(f"Warning: Multiple WHERE clauses ({where_count})")

    # Warning 2: Subqueries detected
    if "SELECT" in sql_upper and sql_upper.count("SELECT") > 1:
        warnings.append({
            "type": "SUBQUERY",
            "message": f"Subquery detected - ensure all subqueries filter by {filter_field}"
        })
        logger.info(f"Warning: Subquery detected")

    # Warning 3: UNION detected (could bypass filters)
    if "UNION" in sql_upper:
        warnings.append({
            "type": "UNION",
            "message": f"UNION detected - verify both queries filter by {filter_field}"
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
