"""
Claude API service for SQL query generation.

This service integrates with Anthropic's Claude API to convert natural language
queries into SQL queries for the retail market research database.
"""

import logging
from anthropic import Anthropic, APIError, APITimeoutError
from config import Config

logger = logging.getLogger(__name__)

# Import metadata loader for dataset-specific instructions
try:
    from services.metadata_loader import MetadataLoader
except ImportError:
    logger.warning("MetadataLoader not available, dataset-specific instructions will be disabled")
    MetadataLoader = None


# Base LLM instructions that apply to ALL datasets (generic SQL rules)
BASE_LLM_INSTRUCTIONS = """You are an expert SQL query generator for SQLite databases.

## SQL Generation Rules

1. Use ONLY the tables and columns defined in the provided schema
2. Generate valid SQLite syntax
3. Return ONLY the SQL query - no explanations, no markdown, no code blocks
4. Use appropriate JOINs when querying multiple tables
5. For aggregations, use GROUP BY and appropriate aggregate functions
6. Limit results to 100 rows unless explicitly requested otherwise
7. Use proper date formats (YYYY-MM-DD) for date comparisons
8. Always apply the client/corporation filter as instructed

## General Best Practices

- Use table aliases for clarity (e.g., `FROM sales s JOIN products p`)
- For "last N years" queries, use fact table's MAX(year), NOT current date
  Example: `year >= (SELECT MAX(year) - N FROM fact_table WHERE is_forecast = 0)`
- Use proper aggregate functions: SUM(), COUNT(), AVG(), MIN(), MAX()
- Always order results meaningfully (typically by the metric DESC or by date)

{DYNAMIC_SCHEMA_PLACEHOLDER}

{DATASET_SPECIFIC_INSTRUCTIONS}

{FILTER_INSTRUCTION}
"""


class ClaudeService:
    """Service for interacting with Claude API to generate SQL queries."""

    def __init__(self, api_key=None, dataset_id=None):
        """
        Initialize Claude service with hybrid instruction loading.

        Args:
            api_key (str, optional): Anthropic API key. Uses Config.ANTHROPIC_API_KEY if None.
            dataset_id (str, optional): Dataset ID for loading metadata
        """
        self.api_key = api_key or Config.ANTHROPIC_API_KEY

        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY in .env file.")

        self.client = Anthropic(api_key=self.api_key)
        self.model = Config.CLAUDE_MODEL
        self.max_tokens = Config.CLAUDE_MAX_TOKENS
        self.timeout = Config.CLAUDE_TIMEOUT

        # Load dataset-specific instructions from metadata
        self.dataset_id = dataset_id
        self.dataset_specific_instructions = self._load_dataset_instructions(dataset_id)

        logger.info(f"Claude service initialized with model: {self.model}, dataset: {dataset_id}")

    def _load_dataset_instructions(self, dataset_id):
        """Load dataset-specific instructions from metadata (hybrid approach)."""
        if not dataset_id:
            logger.warning("No dataset_id provided, no dataset-specific instructions loaded")
            return ""

        if not MetadataLoader:
            logger.warning("MetadataLoader not available, using generic instructions only")
            return ""

        try:
            metadata_loader = MetadataLoader(dataset_id=dataset_id)
            # Load all metadata first
            metadata_loader.load_all()
            # Load llm_instructions (file name without extension)
            docs = metadata_loader.get_documents_by_file('llm_instructions')
            if docs:
                # Combine all sections
                instructions = "\n\n".join([doc.content for doc in docs])
                logger.info(f"Loaded dataset-specific instructions from llm_instructions.md ({len(instructions)} chars)")
                return instructions
            else:
                logger.warning(f"No llm_instructions.md found for dataset {dataset_id}, using generic instructions only")
                return ""
        except Exception as e:
            logger.error(f"Error loading dataset instructions for {dataset_id}: {e}")
            return ""

    def _get_filter_instruction(self, client_id, dataset_id=None):
        """
        Get dataset-specific filtering instruction for SQL generation (config-driven).

        Args:
            client_id (int): Client/Corporation ID
            dataset_id (str, optional): Dataset identifier

        Returns:
            str: Filtering instruction for the LLM
        """
        if not dataset_id:
            return f'ALWAYS include "WHERE client_id = {client_id}" in your queries'

        try:
            dataset_config = Config.get_dataset(dataset_id)

            if 'client_isolation' in dataset_config:
                client_iso = dataset_config['client_isolation']
                method = client_iso.get('method', 'row-level')
                filter_field = client_iso.get('filter_field', 'client_id')

                if method == 'brand-hierarchy':
                    filter_table = client_iso.get('filter_table', 'Dim_Brand')
                    return (f'MANDATORY: Filter by {filter_field} = {client_id} '
                           f'through {filter_table} join. Refer to dataset-specific examples for hierarchy details.')
                elif method == 'row-level':
                    return f'ALWAYS include "WHERE {filter_field} = {client_id}" in your queries'

            # Default fallback
            return f'ALWAYS include "WHERE client_id = {client_id}" in your queries'

        except Exception as e:
            logger.warning(f"Error loading dataset config for {dataset_id}: {e}")
            return f'ALWAYS include "WHERE client_id = {client_id}" in your queries'

    def generate_sql(self, natural_language_query, client_id, client_name=None, custom_schema=None, dataset_id=None):
        """
        Generate SQL query from natural language using Claude API.

        Args:
            natural_language_query (str): User's natural language query
            client_id (int): Client ID for data isolation
            client_name (str, optional): Client name for additional context
            custom_schema (str, optional): Custom database schema (overrides default)
            dataset_id (str, optional): Dataset identifier for dataset-specific instructions

        Returns:
            str: Generated SQL query

        Raises:
            APITimeoutError: If Claude API times out
            APIError: If Claude API returns an error
            ValueError: If generated SQL is invalid
        """
        logger.info(f"Generating SQL for client_id={client_id}, dataset={dataset_id}, query='{natural_language_query[:100]}'")

        # Build user prompt with client context
        user_prompt = f"""Client Context: client_id = {client_id}"""
        if client_name:
            user_prompt += f', client_name = "{client_name}"'

        user_prompt += f"""

Natural Language Query: {natural_language_query}

Generate the SQL query:"""

        # Build hybrid system prompt
        system_prompt = BASE_LLM_INSTRUCTIONS

        # Add database schema
        if custom_schema:
            system_prompt = system_prompt.replace(
                "{DYNAMIC_SCHEMA_PLACEHOLDER}",
                f"\n## Database Schema\n\n{custom_schema}\n"
            )
        else:
            system_prompt = system_prompt.replace("{DYNAMIC_SCHEMA_PLACEHOLDER}", "")

        # Add dataset-specific instructions (examples, patterns)
        if self.dataset_specific_instructions:
            system_prompt = system_prompt.replace(
                "{DATASET_SPECIFIC_INSTRUCTIONS}",
                f"\n## Dataset-Specific Patterns\n\n{self.dataset_specific_instructions}\n"
            )
        else:
            system_prompt = system_prompt.replace("{DATASET_SPECIFIC_INSTRUCTIONS}", "")

        # Add runtime filter instruction
        filter_instruction = self._get_filter_instruction(client_id, dataset_id or self.dataset_id)
        system_prompt = system_prompt.replace(
            "{FILTER_INSTRUCTION}",
            f"\n## Client Filtering Requirement\n\n{filter_instruction}\n"
        )

        # Replace client_id placeholders in examples
        system_prompt = system_prompt.replace("{client_id}", str(client_id))

        try:
            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Extract SQL from response
            sql_query = message.content[0].text.strip()

            # Clean up any markdown code blocks if present
            if sql_query.startswith('```'):
                # Remove markdown code blocks
                lines = sql_query.split('\n')
                sql_query = '\n'.join(line for line in lines if not line.startswith('```'))
                sql_query = sql_query.strip()

            logger.info(f"Generated SQL: {sql_query[:200]}...")
            return sql_query

        except APITimeoutError as e:
            logger.error(f"Claude API timeout: {e}")
            raise ValueError("SQL generation timed out. Please try again.") from e

        except APIError as e:
            logger.error(f"Claude API error: {e}")
            raise ValueError(f"Failed to generate SQL: {str(e)}") from e

        except Exception as e:
            logger.error(f"Unexpected error generating SQL: {e}")
            raise ValueError(f"Unexpected error: {str(e)}") from e

    def get_schema_info(self):
        """
        Get database schema information.

        Returns:
            str: Base LLM instructions (schema should be provided dynamically)
        """
        return "Schema should be fetched dynamically from database. Use custom_schema parameter in generate_sql()."
