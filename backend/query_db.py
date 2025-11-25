#!/usr/bin/env python3
"""
Quick script to query the database interactively.

Usage:
    python query_db.py
"""

import sqlite3
import sys

DB_PATH = '../data/text_to_sql_poc.db'

def print_table(cursor, headers):
    """Print query results in a nice table format."""
    rows = cursor.fetchall()

    if not rows:
        print("No results found.")
        return

    # Calculate column widths
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))

    # Print header
    print("\n" + "-" * (sum(widths) + len(widths) * 3))
    print(" | ".join(str(h).ljust(w) for h, w in zip(headers, widths)))
    print("-" * (sum(widths) + len(widths) * 3))

    # Print rows
    for row in rows:
        print(" | ".join(str(val).ljust(w) for val, w in zip(row, widths)))

    print(f"\n{len(rows)} rows returned\n")


def main():
    """Main function to run interactive queries."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("="*70)
    print("TEXT-TO-SQL POC - DATABASE QUERY TOOL")
    print("="*70)
    print(f"Connected to: {DB_PATH}")
    print("\nAvailable tables: clients, products, sales, customer_segments")
    print("\nCommands:")
    print("  - Enter SQL query (e.g., SELECT * FROM clients)")
    print("  - Type 'tables' to show all tables")
    print("  - Type 'clients' to show all clients")
    print("  - Type 'products [client_id]' to show products for a client")
    print("  - Type 'sales [client_id]' to show sales for a client")
    print("  - Type 'quit' or 'exit' to quit")
    print("="*70 + "\n")

    while True:
        try:
            query = input("SQL> ").strip()

            if not query:
                continue

            if query.lower() in ['quit', 'exit']:
                print("Goodbye!")
                break

            # Shortcuts
            if query.lower() == 'tables':
                query = "SELECT name FROM sqlite_master WHERE type='table'"
            elif query.lower() == 'clients':
                query = "SELECT * FROM clients"
            elif query.lower().startswith('products'):
                parts = query.split()
                if len(parts) > 1:
                    client_id = parts[1]
                    query = f"SELECT * FROM products WHERE client_id = {client_id} LIMIT 20"
                else:
                    query = "SELECT * FROM products LIMIT 20"
            elif query.lower().startswith('sales'):
                parts = query.split()
                if len(parts) > 1:
                    client_id = parts[1]
                    query = f"""
                        SELECT s.sale_id, c.client_name, p.product_name, s.quantity, s.revenue, s.date
                        FROM sales s
                        JOIN clients c ON s.client_id = c.client_id
                        JOIN products p ON s.product_id = p.product_id
                        WHERE s.client_id = {client_id}
                        LIMIT 20
                    """
                else:
                    query = """
                        SELECT s.sale_id, c.client_name, p.product_name, s.quantity, s.revenue, s.date
                        FROM sales s
                        JOIN clients c ON s.client_id = c.client_id
                        JOIN products p ON s.product_id = p.product_id
                        LIMIT 20
                    """

            # Execute query
            cursor.execute(query)

            # Get column names
            if cursor.description:
                headers = [desc[0] for desc in cursor.description]
                print_table(cursor, headers)
            else:
                print("Query executed successfully (no results to display)")

        except sqlite3.Error as e:
            print(f"SQL Error: {e}\n")
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}\n")

    conn.close()


if __name__ == "__main__":
    main()
