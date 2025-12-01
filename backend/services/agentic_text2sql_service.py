"""
Agentic Text2SQL Service with LangGraph orchestration.

This service implements a multi-agent workflow for intelligent SQL generation
with clarification, reflection, retry, and natural language explanations.

Architecture Reference: docs/architecture-agentic-text2sql.md
- Section 4.1: AgentState Structure
- Section 4.2: State Machine Graph
- Section 3.1: Component Architecture
"""

from typing import TypedDict, Annotated, List, Dict, Optional
from langgraph.graph import StateGraph, END
import operator
import logging
import json
from datetime import datetime
from services.claude_service import ClaudeService
from services.agent_tools import Tool
from database.db_manager import get_engine

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """
    State for the agentic workflow.
    Architecture Reference: Section 4.1 (AgentState Structure)
    
    This TypedDict carries all context through the workflow. Fields with
    Annotated[List, operator.add] accumulate across nodes.
    """
    # Core query info
    user_query: str
    session_id: str
    resolved_query: str
    client_id: int  # For security validation
    client_name: Optional[str]
    dataset_id: str  # Dataset identifier (sales, market_size, etc.)
    
    # Conversation context
    chat_history: Annotated[List[Dict], operator.add]
    
    # Iteration tracking
    iteration: int
    max_iterations: int
    
    # Retrieved context
    schema: Optional[str]
    sample_data: Dict[str, str]
    metadata_context: Annotated[List[Dict], operator.add]
    
    # Generated artifacts
    sql_query: Optional[str]
    execution_result: Optional[Dict]
    validation_result: Optional[Dict]
    security_validation: Optional[Dict]  # Security checks (client isolation, read-only)
    explanation: Optional[str]
    
    # Reflection and clarification
    reflection_result: Optional[Dict]
    clarification_needed: bool
    clarification_questions: Annotated[List[str], operator.add]
    skip_clarification_check: bool  # Skip detection if query already clarified

    # Session memory (Story 7.1)
    is_followup: bool
    resolution_info: Optional[Dict]
    
    # Tool tracking
    tool_calls: Annotated[List[Dict], operator.add]
    
    # Flow control
    next_action: str
    is_complete: bool
    error: Optional[str]


class AgenticText2SQLService:
    """
    Agentic Text2SQL with LangGraph orchestration.
    Architecture Reference: Section 3.1 (Component Architecture)
    
    This service orchestrates multiple agent nodes (planning, SQL generation,
    reflection, clarification) through a LangGraph state machine.
    """
    
    def __init__(self, dataset_id=None):
        """Initialize service with dataset awareness and session storage.

        Args:
            dataset_id (str, optional): Dataset identifier for metadata loading and validation
        """
        self.dataset_id = dataset_id
        self.claude_service = ClaudeService(dataset_id=dataset_id)
        self.db_engine = get_engine()
        self.tools = self._initialize_tools()
        self.workflow = self._build_workflow()

        # Session storage (Architecture Section 7.1 - in-memory for POC)
        self.chat_sessions = {}

        # Load domain vocabulary from schema for keyword-based detection
        self.domain_vocab = self._load_domain_vocabulary(dataset_id)

        logger.info(f"AgenticText2SQLService initialized for dataset: {dataset_id or 'default'}")
    
    def _get_chat_history(self, session_id: str) -> List[Dict]:
        """
        Retrieve conversation history for session.
        Architecture Reference: Section 7.1
        """
        history = self.chat_sessions.get(session_id, [])
        logger.info(f"Retrieved {len(history)} previous queries for session {session_id}")
        return history
    
    def _add_to_history(self, session_id: str, entry: Dict):
        """
        Add entry to conversation history.
        Architecture Reference: Section 7.1
        Retention: Last 10 queries per session
        """
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = []
            logger.info(f"Created new session: {session_id}")
        
        self.chat_sessions[session_id].append(entry)
        
        # Keep only last 10 exchanges (Architecture Section 7.1)
        if len(self.chat_sessions[session_id]) > 10:
            removed = len(self.chat_sessions[session_id]) - 10
            self.chat_sessions[session_id] = self.chat_sessions[session_id][-10:]
            logger.info(f"Session {session_id}: trimmed {removed} old entries, keeping 10 most recent")
        
        logger.info(f"Session {session_id}: added entry, total={len(self.chat_sessions[session_id])}")

    def _format_conversation_context(self, session_id: str, max_entries: int = 5) -> str:
        """
        Format recent conversation history for Claude context.
        Story: STORY-001 - Conversation Context for Follow-Up Queries
        AC1: Context Formatting

        Args:
            session_id: Session identifier
            max_entries: Maximum number of queries to include (default: 5)

        Returns:
            Formatted markdown string with conversation context, or empty string if no history
        """
        history = self._get_chat_history(session_id)

        # No history - return empty string (AC1, edge case handling)
        if not history:
            logger.debug(f"No conversation history for session {session_id}")
            return ""

        # Get last N entries
        recent_history = history[-max_entries:]

        # Filter out failed/incomplete entries (no SQL generated)
        valid_entries = [
            entry for entry in recent_history
            if entry.get('sql_query') and entry.get('sql_query').strip()
        ]

        if not valid_entries:
            logger.debug(f"No valid entries with SQL in session {session_id}")
            return ""

        # Build simple conversation context - no filter extraction needed
        # LLM can infer context from seeing previous queries and SQL
        context = "\n## Previous Queries in This Conversation:\n\n"

        for i, entry in enumerate(valid_entries, 1):
            user_query = entry.get('user_query', 'Unknown query')
            sql_query = entry.get('sql_query', '')

            # Show SQL (truncated for tokens)
            sql_truncated = sql_query[:300] + "..." if len(sql_query) > 300 else sql_query

            context += f"**Query {i}:** {user_query}\n"
            context += f"```sql\n{sql_truncated}\n```\n\n"

        context += "**Context Instruction:** Maintain the scope and filters from the most recent query above "
        context += "unless the user explicitly changes the context (e.g., 'show me Europe instead', 'start fresh').\n"

        logger.info(f"Formatted conversation context for session {session_id}: {len(valid_entries)} queries, {len(context)} chars")
        return context

    def _load_domain_vocabulary(self, dataset_id: str) -> Dict[str, List[str]]:
        """
        Load or extract domain vocabulary for dataset.

        Args:
            dataset_id: Dataset identifier

        Returns:
            Dictionary with vocabulary (entities, metrics, dimensions)
        """
        if not dataset_id:
            logger.warning("No dataset_id provided, using minimal fallback vocabulary")
            return {
                "entities": ["data", "records", "metric", "metrics"],
                "metrics": ["value", "count", "total", "amount"],
                "dimensions": ["category", "type", "group"]
            }

        try:
            from services.domain_vocabulary import get_vocabulary
            from config import Config

            dataset_config = Config.get_dataset(dataset_id)
            db_path = dataset_config['db_path']

            vocabulary = get_vocabulary(dataset_id, db_path)
            logger.info(f"Loaded domain vocabulary for {dataset_id}: "
                       f"{len(vocabulary['entities'])} entities, "
                       f"{len(vocabulary['metrics'])} metrics, "
                       f"{len(vocabulary['dimensions'])} dimensions")

            return vocabulary

        except Exception as e:
            logger.error(f"Failed to load domain vocabulary: {e}", exc_info=True)
            # Return minimal fallback
            return {
                "entities": ["data", "records", "metric", "metrics"],
                "metrics": ["value", "count", "total", "amount"],
                "dimensions": ["category", "type", "group"]
            }

    def _detect_followup(self, user_query: str, chat_history: List[Dict]) -> tuple:
        """
        Detect if query is a follow-up using keyword and context analysis.
        Story 7.1 - AC1: Follow-up Detection Method
        
        Args:
            user_query: The current user query
            chat_history: List of previous queries in session
            
        Returns:
            (is_followup, confidence) - bool and float 0-1
        """
        query_lower = user_query.lower().strip()
        
        # No history = not a follow-up
        if not chat_history:
            logger.info(f"No history for follow-up detection: '{user_query}'")
            return False, 1.0
        
        # Keyword patterns (Story 7.1 spec)
        followup_keywords = [
            "what about", "show me", "same but", "also show",
            "compare", "versus", "vs", "by", "for", "in", "only",
            "just", "filter", "more", "less", "that", "it",
            "them", "this", "these", "previous", "last", "next",
            "and", "also", "too", "again"
        ]
        
        # Check for keywords
        has_keywords = any(kw in query_lower for kw in followup_keywords)
        
        # Check for very short queries (likely follow-ups)
        word_count = len(user_query.split())
        is_short = word_count <= 4
        
        # Check for complete queries (has main entity/action)
        # These indicate a standalone query rather than a follow-up
        # Use domain vocabulary extracted from schema
        entity_keywords = self.domain_vocab.get("entities", [])
        
        # Action keywords that indicate complete queries
        complete_action_keywords = [
            "list all", "show all", "get all", "display all",
            "show me all", "give me all", "find all"
        ]
        
        # Dimension modifiers that indicate follow-ups (overrides entity check)
        # Build from domain vocabulary dimensions
        dimension_keywords = self.domain_vocab.get("dimensions", [])
        dimension_modifiers = [f"by {dim}" for dim in dimension_keywords] + [f"for {dim}" for dim in dimension_keywords]
        
        has_entity = any(word in query_lower for word in entity_keywords)
        has_complete_action = any(action in query_lower for action in complete_action_keywords)
        has_dimension_modifier = any(mod in query_lower for mod in dimension_modifiers)
        
        # Scoring logic (Story 7.1 spec + refinements)
        confidence = 0.5
        is_followup = False
        
        # Dimension modifiers are strong indicators of follow-ups
        if has_dimension_modifier:
            is_followup = True
            confidence = 0.85
            reason = "dimension modifier (follow-up)"
        # Complete action phrases indicate standalone queries
        elif has_complete_action:
            is_followup = False
            confidence = 0.9
            reason = "complete action phrase (standalone query)"
        elif has_keywords and is_short and not has_entity:
            is_followup = True
            confidence = 0.9
            reason = "has keywords + short + no entity"
        elif has_keywords and is_short and has_entity:
            # Has entity but still short - likely standalone
            is_followup = False
            confidence = 0.7
            reason = "has keywords + short + entity (standalone)"
        elif has_keywords and not has_entity:
            is_followup = True
            confidence = 0.7
            reason = "has keywords + no entity"
        elif is_short and not has_entity:
            is_followup = True
            confidence = 0.6
            reason = "short + no entity"
        else:
            is_followup = False
            confidence = 0.8
            reason = "appears to be new query"
        
        logger.info(f"Follow-up detection: query='{user_query}' -> is_followup={is_followup}, confidence={confidence:.2f} ({reason})")
        
        return is_followup, confidence
    
    def _resolve_query_with_history(self, user_query: str, chat_history: List[Dict]) -> Dict:
        """
        Resolve follow-up query into standalone query using Claude.
        Story 7.1 - AC2: Query Resolution with Claude
        
        Args:
            user_query: The current user query (potentially a follow-up)
            chat_history: List of previous queries in session
            
        Returns:
            Dict with resolved_query, confidence, is_followup, interpretation, entities_inherited
        """
        logger.info(f"Resolving query with history: '{user_query}'")
        start_time = datetime.now()
        
        # Use last 2-3 queries for context (Story 7.1 spec)
        recent_history = chat_history[-3:] if len(chat_history) > 3 else chat_history
        
        if not recent_history:
            logger.info("No history available, returning original query")
            return {
                "resolved_query": user_query,
                "confidence": 1.0,
                "is_followup": False,
                "interpretation": "First query in session",
                "entities_inherited": {}
            }
        
        # Build context string with entity metadata (Story 7.2 - AC5)
        context_lines = []
        for i, entry in enumerate(recent_history, 1):
            context_lines.append(f"{i}. Query: \"{entry.get('user_query', 'N/A')}\"")
            context_lines.append(f"   Resolved to: \"{entry.get('resolved_query', entry.get('user_query', 'N/A'))}\"")
            
            # Include structured entity context (Story 7.2 enhancement)
            if entry.get('key_entities'):
                entities = entry['key_entities']
                context_lines.append(f"   Dimensions: {entities.get('dimensions', [])}")
                context_lines.append(f"   Metrics: {entities.get('metrics', [])}")
                context_lines.append(f"   Time period: {entities.get('time_period', 'all time')}")
                if entities.get('filters'):
                    context_lines.append(f"   Filters: {entities.get('filters', [])}")
                if entities.get('limit'):
                    context_lines.append(f"   Limit: {entities.get('limit')}")
        
        context = "\n".join(context_lines)
        
        # Claude resolution prompt (Story 7.1 spec)
        resolution_prompt = f"""You are a query resolution assistant for a text-to-SQL analytics system.

Previous conversation context:
{context}

New user query: "{user_query}"

Your task: Resolve this query into a complete, standalone natural language query that can be converted to SQL.

If it's a follow-up:
- Inherit relevant context from previous queries
- Resolve pronouns (it, that, them) to specific entities
- Expand implicit references (Q4 → "in Q4 2024", by region → "grouped by region")
- Keep the user's intent but make it standalone

If it's NOT a follow-up:
- Return the query unchanged

Respond in JSON format:
{{
    "resolved_query": "complete standalone query",
    "confidence": 0.95,
    "is_followup": true,
    "interpretation": "User wants to see same data but for Q4",
    "entities_inherited": {{"time_period": "Q4", "metrics": ["revenue"], "dimensions": ["product"]}}
}}
"""
        
        try:
            # Call Claude (Story 7.1 spec: temp=0.3, max_tokens=500)
            response = self.claude_service.client.messages.create(
                model=self.claude_service.model,
                max_tokens=500,
                temperature=0.3,  # Lower temp for consistency
                system="You are a precise query resolution assistant. Always respond in valid JSON.",
                messages=[{"role": "user", "content": resolution_prompt}]
            )
            
            result_text = response.content[0].text.strip()
            
            # Clean up markdown code blocks if present
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:].strip()
            
            result = json.loads(result_text)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Query resolved in {elapsed:.2f}s: '{user_query}' → '{result['resolved_query']}' (confidence: {result.get('confidence', 0.0):.2f})")
            
            # Performance warning (Story 7.1 spec: target ≤2s)
            if elapsed > 2.0:
                logger.warning(f"Resolution exceeded 2s target: {elapsed:.2f}s")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude JSON response: {e}", exc_info=True)
            elapsed = (datetime.now() - start_time).total_seconds()
            # Fallback: return original query (Story 7.1 spec)
            return {
                "resolved_query": user_query,
                "confidence": 0.5,
                "is_followup": False,
                "interpretation": "Resolution failed (JSON parse error), using original query",
                "entities_inherited": {}
            }
        except Exception as e:
            logger.error(f"Query resolution failed: {e}", exc_info=True)
            elapsed = (datetime.now() - start_time).total_seconds()
            # Fallback: return original query (Story 7.1 spec)
            return {
                "resolved_query": user_query,
                "confidence": 0.5,
                "is_followup": False,
                "interpretation": f"Resolution failed ({str(e)}), using original query",
                "entities_inherited": {}
            }
    
    def _expand_query_with_context(self, user_query: str, chat_history: List[Dict], is_clarified: bool = False) -> str:
        """
        Expand fragment/follow-up queries into complete queries using conversation context.
        Works at natural language level - no SQL parsing needed.
        
        Story: Query Expansion Architecture - Story 1
        
        Args:
            user_query: Current user input (may be fragment like "by region" or complete query)
            chat_history: Previous queries in conversation (for context)
            is_clarified: If True, this is a clarified query with additional context
            
        Returns:
            Expanded, standalone natural language query
            
        Examples:
            Previous: "Show sales in 2023"
            Input: "by region"
            Output: "Show sales in 2023 by region"
            
            Previous: "Show sales in 2023", "by region"
            Input: "for Africa"  
            Output: "Show sales in 2023 by region for Africa"
            
            Clarified: "Show sales. Additional information: for Q4 2023"
            Output: "Show sales for Q4 2023" (incorporates clarification naturally)
        """
        logger.info(f"Expanding query: '{user_query}' (clarified: {is_clarified})")
        start_time = datetime.now()
        
        # For clarified queries, try to incorporate the clarification naturally
        combined_query = None
        if is_clarified:
            # Extract original query and clarification
            if "Additional information:" in user_query:
                parts = user_query.split("Additional information:", 1)
                original = parts[0].strip().rstrip('.')
                clarification = parts[1].strip()
                
                # Check if clarification is a complete query (has action verb)
                clarification_lower = clarification.lower()
                has_action_in_clarification = any(word in clarification_lower for word in [
                    "show", "list", "display", "get", "find", "compare", "analyze", "need", "want", "see"
                ])
                
                # If clarification is a complete query, use it as the main query
                if has_action_in_clarification:
                    logger.info(f"Clarification is a complete query - using it directly: '{clarification}'")
                    combined_query = clarification
                else:
                    # Clarification is additional context - combine with original
                    combined_query = f"{original} {clarification}".strip()
                    logger.info(f"Clarified query combined: '{combined_query}'")
                
                # Still run through expansion to incorporate history if needed
                if chat_history:
                    # Use the combined query for expansion
                    user_query = combined_query
                else:
                    return combined_query
            elif "Additional context:" in user_query:
                # Handle old format for backward compatibility
                parts = user_query.split("Additional context:", 1)
                original = parts[0].strip().rstrip('.')
                clarification = parts[1].strip()
                
                # Same logic: check if clarification is complete
                clarification_lower = clarification.lower()
                has_action_in_clarification = any(word in clarification_lower for word in [
                    "show", "list", "display", "get", "find", "compare", "analyze", "need", "want", "see"
                ])
                
                if has_action_in_clarification:
                    logger.info(f"Clarification is a complete query (old format) - using it directly: '{clarification}'")
                    combined_query = clarification
                else:
                    combined_query = f"{original} {clarification}".strip()
                    logger.info(f"Clarified query combined (old format): '{combined_query}'")
                
                if chat_history:
                    user_query = combined_query
                else:
                    return combined_query
        
        # No history = use query as-is
        if not chat_history:
            logger.info("No history for expansion, using query as-is")
            return combined_query if (is_clarified and combined_query) else user_query
        
        # Get last 3-5 user queries (just NL, not SQL) for context
        recent_history = chat_history[-5:] if len(chat_history) > 5 else chat_history
        previous_queries = [entry.get('user_query', '') for entry in recent_history]
        
        # Build expansion prompt
        if is_clarified:
            # Special handling for clarified queries - incorporate clarification naturally
            expansion_prompt = f"""You are helping incorporate clarification into a data analysis query.

Previous user queries in this conversation:
{chr(10).join(f"{i+1}. {q}" for i, q in enumerate(previous_queries))}

Current user input: "{user_query}"

This query includes additional clarification information. Your task:
- If the clarification is a COMPLETE query (has action verb like "show", "need", "want"), use it as the main query
- If the clarification is just additional context, incorporate it naturally into the original query
- Make sure the final query is COMPLETE and STANDALONE
- The clarification should be seamlessly integrated, not just appended

Examples:
Input: "show me by region. Additional information: I need revenue by region"
Output: "Show revenue by region"

Input: "Show sales. Additional information: for Q4 2023"
Output: "Show sales for Q4 2023"

CRITICAL: Return a natural, complete query that incorporates the clarification. No "Additional information:" markers in output.
Return ONLY the complete expanded query text, nothing else. No explanations.
"""
        else:
            expansion_prompt = f"""You are helping expand fragment queries in a data analysis conversation.

Previous user queries in this conversation:
{chr(10).join(f"{i+1}. {q}" for i, q in enumerate(previous_queries))}

Current user input: "{user_query}"

Your task:
- If this is a FRAGMENT or FOLLOW-UP (like "by region", "for 2024", "what about Q2"), expand it into a COMPLETE, STANDALONE query using context
- If this is already a COMPLETE query, return it unchanged
- When expanding, intelligently decide: Is user adding to context or replacing context?
  - "by region" = additive (keep previous scope, add dimension)
  - "what about 2024?" = replacement (replace time period, keep structure)
  - "show me brands instead" = new topic (ignore previous context)

CRITICAL: The expanded query must be COMPLETE and include the full query intent, NOT just the new filter.
WRONG: "WHERE corp_id = 105"
RIGHT: "Show sales by region for corporation 105"

Return ONLY the complete expanded query text, nothing else. No explanations.
"""
        
        try:
            # Call Claude with low temperature for consistent expansion
            response = self.claude_service.client.messages.create(
                model=self.claude_service.model,
                max_tokens=200,  # Short response expected
                temperature=0.2,  # Low temp for consistency
                system="You are a query expansion assistant. You MUST output a complete, standalone natural language query. NEVER output SQL fragments or WHERE clauses. Output only the full expanded query as natural language, nothing else.",
                messages=[{"role": "user", "content": expansion_prompt}]
            )
            
            expanded_query = response.content[0].text.strip()

            # Remove quotes if Claude added them
            if expanded_query.startswith('"') and expanded_query.endswith('"'):
                expanded_query = expanded_query[1:-1]

            # SAFETY CHECK: Validate that expanded query is not a SQL fragment
            sql_fragment_indicators = [
                "WHERE ", "SELECT ", "FROM ", "JOIN ", "GROUP BY",
                "ORDER BY", "LIMIT ", "corp_id =", "client_id ="
            ]
            is_sql_fragment = any(indicator.lower() in expanded_query.lower() for indicator in sql_fragment_indicators)

            if is_sql_fragment:
                logger.error(f"⚠️ Query expansion returned SQL fragment instead of natural language: '{expanded_query}'")
                logger.error(f"Falling back to previous query context for safety")
                # Fallback: Use the most recent complete query with the user's input appended
                if previous_queries:
                    last_query = previous_queries[-1]
                    expanded_query = f"{last_query} {user_query}"
                    logger.warning(f"Fallback expansion: '{expanded_query}'")
                else:
                    # No history, use original query
                    expanded_query = user_query
                    logger.warning(f"No history available, using original query: '{user_query}'")

            elapsed = (datetime.now() - start_time).total_seconds()

            if expanded_query != user_query:
                logger.info(f"Query expanded in {elapsed:.2f}s: '{user_query}' → '{expanded_query}'")
            else:
                logger.info(f"Query unchanged (complete query): '{user_query}'")

            # Performance target: < 1 second
            if elapsed > 1.0:
                logger.warning(f"Query expansion exceeded 1s target: {elapsed:.2f}s")

            return expanded_query
            
        except Exception as e:
            logger.error(f"Query expansion failed: {e}", exc_info=True)
            # Fallback: use original query
            logger.info("Falling back to original query")
            return user_query
    
    def _extract_entities(self, state: AgentState) -> Dict:
        """
        Extract semantic entities from generated SQL query.
        Story 7.2 - AC2: Entity Extraction from Query State
        
        POC-level implementation using regex patterns (not full SQL parser).
        
        Args:
            state: Current agent state with SQL query
            
        Returns:
            Dict with dimensions, metrics, filters, time_period, grouping, limit
        """
        sql = state.get("sql_query", "")
        if not sql:
            logger.info("No SQL query to extract entities from")
            return {}
        
        logger.info("Extracting entities from SQL query")
        sql_lower = sql.lower()
        
        entities = {
            "dimensions": [],
            "metrics": [],
            "filters": [],
            "time_period": "all time",
            "grouping": [],
            "limit": None
        }
        
        try:
            # Extract dimensions from SELECT and GROUP BY (Story 7.2 spec)
            dimension_keywords = ['product', 'region', 'category', 'client', 'customer', 'segment']
            for keyword in dimension_keywords:
                if keyword in sql_lower:
                    if keyword not in entities["dimensions"]:
                        entities["dimensions"].append(keyword)
            
            # Extract metrics from SELECT aggregations (Story 7.2 spec)
            import re
            metrics_pattern = r'(SUM|COUNT|AVG|MAX|MIN)\s*\(\s*\w*\.?(\w+)\s*\)'
            metrics_matches = re.findall(metrics_pattern, sql, re.IGNORECASE)
            for agg, field in metrics_matches:
                if field.lower() not in ['*', 'id'] and field.lower() not in entities["metrics"]:
                    entities["metrics"].append(field.lower())
            
            # Extract filters from WHERE clause (Story 7.2 spec)
            where_pattern = r'WHERE\s+(.+?)(?:GROUP BY|ORDER BY|LIMIT|$)'
            where_match = re.search(where_pattern, sql, re.IGNORECASE | re.DOTALL)
            if where_match:
                where_clause = where_match.group(1)
                
                # Extract client_id filter
                client_pattern = r'client_id\s*=\s*(\d+)'
                client_match = re.search(client_pattern, where_clause, re.IGNORECASE)
                if client_match:
                    entities["filters"].append({"client_id": int(client_match.group(1))})
                
                # Extract category filter
                category_pattern = r'category\s*=\s*[\'"]([^\'"]+)[\'"]'
                category_match = re.search(category_pattern, where_clause, re.IGNORECASE)
                if category_match:
                    entities["filters"].append({"category": category_match.group(1)})
                
                # Extract time period (Story 7.2 spec)
                # Check for specific date ranges
                if 'date >=' in where_clause.lower():
                    date_pattern = r'date\s*>=\s*[\'"]([\d-]+)[\'"].*?date\s*<=\s*[\'"]([\d-]+)[\'"]'
                    date_match = re.search(date_pattern, where_clause, re.IGNORECASE)
                    if date_match:
                        start_date = date_match.group(1)
                        end_date = date_match.group(2)
                        
                        # Try to infer quarter
                        if '10-01' in start_date and '12-31' in end_date:
                            year = start_date[:4]
                            entities["time_period"] = f"Q4 {year}"
                        elif '07-01' in start_date and '09-30' in end_date:
                            year = start_date[:4]
                            entities["time_period"] = f"Q3 {year}"
                        elif '04-01' in start_date and '06-30' in end_date:
                            year = start_date[:4]
                            entities["time_period"] = f"Q2 {year}"
                        elif '01-01' in start_date and '03-31' in end_date:
                            year = start_date[:4]
                            entities["time_period"] = f"Q1 {year}"
                        else:
                            entities["time_period"] = f"{start_date} to {end_date}"
                
                # Check for relative dates (last 6 months, etc.)
                if "'-6 months'" in where_clause or "'-6 month'" in where_clause:
                    entities["time_period"] = "last 6 months"
                elif "'-1 year'" in where_clause or "'-12 month'" in where_clause:
                    entities["time_period"] = "last year"
                elif "'-1 month'" in where_clause:
                    entities["time_period"] = "last month"
            
            # Extract grouping from GROUP BY (Story 7.2 spec)
            group_pattern = r'GROUP BY\s+([\w., ]+)'
            group_match = re.search(group_pattern, sql, re.IGNORECASE)
            if group_match:
                group_clause = group_match.group(1)
                # Extract column names (handle aliases like p.product_name)
                group_cols = re.findall(r'(?:\w+\.)?(\w+)', group_clause)
                entities["grouping"] = [col for col in group_cols if col.lower() not in ['as']]
            
            # Extract limit (Story 7.2 spec)
            limit_pattern = r'LIMIT\s+(\d+)'
            limit_match = re.search(limit_pattern, sql, re.IGNORECASE)
            if limit_match:
                entities["limit"] = int(limit_match.group(1))
            
            logger.info(f"Extracted entities: {entities}")
            
        except Exception as e:
            logger.error(f"Entity extraction error: {e}", exc_info=True)
            # Return partial entities on error
        
        return entities
    
    def _summarize_results(self, execution_result: Dict) -> str:
        """
        Summarize query results into human-readable string.
        Story 7.2 - AC3: Results Summarization

        Args:
            execution_result: Dict with results, columns, row_count

        Returns:
            Summary string like "5 rows: Le Creuset ($12K) (top)"
        """
        if not execution_result:
            return "0 rows"

        # STORY-001: Defensive check - if execution_result is already a string (shouldn't happen)
        if isinstance(execution_result, str):
            logger.warning(f"execution_result is a string, not dict: {execution_result[:100]}")
            return execution_result

        # Note: QueryExecutor returns 'results' key (Story 7.1 fix)
        results = execution_result.get("results", [])
        row_count = execution_result.get("row_count", 0)
        
        if not results or row_count == 0:
            return "0 rows"
        
        try:
            # Get first row for "top" value
            first_row = results[0]
            
            if row_count <= 5:
                # Show first few values (Story 7.2 spec)
                values = []
                for i, row in enumerate(results[:3]):
                    # Get first non-id value from row
                    row_values = [v for k, v in row.items() if k.lower() not in ['id', 'client_id']]
                    if row_values:
                        first_val = row_values[0]
                        # Format numbers with K/M suffix
                        if isinstance(first_val, (int, float)) and first_val > 1000:
                            if first_val > 1000000:
                                first_val = f"${first_val/1000000:.1f}M"
                            else:
                                first_val = f"${first_val/1000:.1f}K"
                        values.append(str(first_val))
                
                summary = f"{row_count} rows: {', '.join(values)}"
                if len(summary) > 100:
                    summary = summary[:97] + "..."
                return summary
            else:
                # Large result set (Story 7.2 spec)
                first_value = None
                for k, v in first_row.items():
                    if k.lower() not in ['id', 'client_id']:
                        first_value = v
                        break
                
                if first_value:
                    if isinstance(first_value, (int, float)) and first_value > 1000:
                        if first_value > 1000000:
                            first_value = f"${first_value/1000000:.1f}M"
                        else:
                            first_value = f"${first_value/1000:.1f}K"
                    return f"{row_count} rows: {first_value} (top)"
                else:
                    return f"{row_count} rows"
        
        except Exception as e:
            logger.error(f"Results summarization error: {e}", exc_info=True)
            return f"{row_count} rows"
    
    def _build_workflow(self) -> StateGraph:
        """
        Build LangGraph workflow with clarification, planning, tools, SQL generation, and reflection.
        Architecture Reference: Section 4.2 (State Machine Graph), Section 10.2 (Clarification Flow)
        
        Workflow: detect_clarification → [plan → tools/SQL/reflect] OR [complete with questions]
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("detect_clarification", self._detect_clarification_node)
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("execute_tools", self._execute_tools_node)
        workflow.add_node("generate_sql", self._generate_sql_node)
        workflow.add_node("reflect", self._reflect_node)
        workflow.add_node("generate_explanation", self._generate_explanation_node)
        workflow.add_node("complete", self._complete_node)
        
        # Set entry point (Architecture Section 10.2)
        workflow.set_entry_point("detect_clarification")
        
        # Clarification routing: proceed or return questions
        workflow.add_conditional_edges(
            "detect_clarification",
            self._should_clarify,
            {
                "plan": "plan",  # No clarification needed
                "complete": "complete"  # Return questions to user
            }
        )
        
        # Add conditional edges from plan
        workflow.add_conditional_edges(
            "plan",
            self._should_execute_or_generate,
            {
                "execute_tools": "execute_tools",
                "generate_sql": "generate_sql",
                "reflect": "reflect",
                "generate_explanation": "generate_explanation",
                "complete": "complete"
            }
        )
        
        # Loop edges: back to plan
        workflow.add_edge("execute_tools", "plan")
        workflow.add_edge("generate_sql", "plan")
        workflow.add_edge("generate_explanation", "plan")
        
        # Reflection conditional routing (Architecture Section 10.3)
        workflow.add_conditional_edges(
            "reflect",
            self._should_refine,
            {
                "refine": "plan",  # Retry: back to plan with reset state
                "continue": "plan"  # Accept: back to plan for explanation generation
            }
        )
        
        # Terminal edge
        workflow.add_edge("complete", END)
        
        logger.info("Workflow built: detect_clarification → [plan ⇄ tools/SQL/reflect] OR [complete]")
        return workflow.compile()
    
    def _detect_clarification_node(self, state: AgentState) -> Dict:
        """
        Detect if query needs clarification (simplified POC version).
        Architecture Reference: Section 5.3.1
        Performance Target: ≤3s

        POC: Simple keyword-based detection for speed.
        Enhanced: Catches fragment queries that need context or clarification.
        """
        # Skip clarification check if this is an enhanced/clarified query
        if state.get("skip_clarification_check", False):
            logger.info("Skipping clarification check (query already clarified)")
            return {
                "clarification_needed": False,
                "clarification_questions": []
            }

        query = state["resolved_query"]
        chat_history = self._get_chat_history(state["session_id"])
        logger.info(f"Checking for ambiguity: '{query}' (history: {len(chat_history)} queries)")

        # POC: Check for ambiguous patterns without sufficient context
        query_lower = query.lower()
        questions = []
        
        # Count words (helps identify fragments)
        word_count = len(query.split())
        
        # Check if query has complete information
        # Use domain vocabulary extracted from schema
        has_entity = any(word in query_lower for word in self.domain_vocab.get("entities", []))
        has_metric = any(word in query_lower for word in self.domain_vocab.get("metrics", []) +
                        ["how much", "how many", "all", "list"])
        has_action = any(word in query_lower for word in [
            "show", "list", "display", "get", "find", "compare", "analyze"
        ])
        
        # CRITICAL: Catch vague fragment queries (no history context)
        # Examples: "how about south", "what about q4", "only electronics"
        if len(chat_history) == 0:
            vague_patterns = [
                "how about", "what about", "how are", "what are",
                "only ", "just ", "for ", "in "
            ]
            is_vague_fragment = any(pattern in query_lower for pattern in vague_patterns)
            
            # Short queries (≤4 words) that are vague
            if is_vague_fragment and word_count <= 4:
                # Check if it has enough context
                if not (has_entity and has_metric and has_action):
                    questions.append("What would you like to know? Please provide more details.")
                    questions.append("Examples: 'Top products by revenue in South', 'Sales in Q4', etc.")
            
            # Dimension/location only (no entity or metric)
            # Examples: "south", "q4", "electronics", "by region"
            # Use dimension keywords from vocabulary + time keywords
            time_keywords = ["q1", "q2", "q3", "q4", "january", "february", "march", "april", "may", "june",
                           "july", "august", "september", "october", "november", "december"]
            dimension_words = self.domain_vocab.get("dimensions", []) + time_keywords
            has_only_location = any(word in query_lower for word in dimension_words)
            
            if has_only_location and not (has_entity and has_metric):
                questions.append("What data would you like to see?")
                questions.append("What metric are you interested in? (revenue, quantity, count?)")
        
        # Check for grouping-only queries without entity/metric (e.g., "show me by region")
        grouping_only_patterns = [
            "show me by", "show by", "list by", "display by", 
            "compare by", "group by", "break down by", "split by"
        ]
        has_grouping_only = any(pattern in query_lower for pattern in grouping_only_patterns)
        
        if has_grouping_only and len(chat_history) == 0:
            if not has_entity or not has_metric:
                if "What data would you like to see?" not in questions:
                    questions.append("What data would you like to see? (products, sales, customers?)")
                if "What metric are you interested in?" not in questions:
                    questions.append("What metric are you interested in? (revenue, quantity, count?)")
        
        # Check for trends without time period
        if "trend" in query_lower:
            import re
            # Check for any 4-digit year (2020-2030) or time keywords
            has_year = bool(re.search(r'\b(20[0-9]{2}|202[0-9])\b', query_lower))
            has_time_keyword = any(word in query_lower for word in [
                "q1", "q2", "q3", "q4", "january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december",
                "week", "month", "quarter", "year", "last", "this", "recent", "latest"
            ])
            
            # Only ask for time period if query is incomplete (missing action, metric, or entity)
            # If query is complete, time period is optional (defaults to all time)
            query_is_complete = has_action and (has_metric or has_entity)
            
            if not (has_year or has_time_keyword) and not query_is_complete:
                questions.append("Which time period?")
        
        # Check for performance without metric
        if "performance" in query_lower:
            has_metric = any(word in query_lower for word in ["revenue", "sales", "quantity", "profit", "growth", "margin"])
            if not has_metric:
                questions.append("Which metric (revenue, quantity, growth)?")
        
        # Check for top/best without sufficient criteria
        if ("top" in query_lower or "best" in query_lower):
            # Use domain vocabulary extracted from schema
            has_entity_specific = any(word in query_lower for word in self.domain_vocab.get("entities", []))
            has_metric_specific = any(word in query_lower for word in self.domain_vocab.get("metrics", []))
            if not (has_entity_specific and has_metric_specific):
                questions.append("By what measure? (e.g., revenue, units sold, market size, growth rate)")
        
        clarification_needed = len(questions) > 0
        
        if clarification_needed:
            logger.info(f"Ambiguity detected: {len(questions)} question(s)")
        else:
            logger.info("Query appears clear, proceeding")
        
        return {
            "clarification_needed": clarification_needed,
            "clarification_questions": questions if questions else []
        }
    
    def _should_clarify(self, state: AgentState) -> str:
        """
        Conditional routing: return questions or proceed to planning.
        Architecture Reference: Section 10.2 (Clarification Flow)
        """
        if state.get("clarification_needed", False):
            logger.info("Clarification needed, returning to user")
            return "complete"  # Return immediately with questions
        else:
            logger.info("No clarification needed, proceeding to plan")
            return "plan"
    
    def _plan_node(self, state: AgentState) -> Dict:
        """
        Intelligent workflow routing based on state.
        Architecture Reference: Section 5.3.2 (Planning Node Design)
        
        Decision Tree:
        1. No schema → get_schema
        2. Has schema, no SQL → generate_sql
        3. Has SQL, not executed → execute_sql
        4. Has results, not validated → validate_results
        5. Max iterations OR all complete → complete
        """
        iteration = state["iteration"] + 1
        logger.info(f"Planning iteration {iteration}/{state['max_iterations']}")
        
        updates = {"iteration": iteration}
        
        # Max iteration guard (Architecture Section 13.1)
        if iteration > state["max_iterations"]:
            logger.warning(f"Max iterations reached: {iteration}")
            updates["next_action"] = "complete"
            updates["is_complete"] = True
            return updates
        
        # Decision tree (Architecture Section 5.3.2)
        if state["schema"] is None:
            next_action = "get_schema"
        elif state["sql_query"] is None:
            next_action = "generate_sql"
        elif state["execution_result"] is None:
            next_action = "execute_sql"
        elif state["validation_result"] is None:
            next_action = "validate_results"
        elif state["reflection_result"] is None:
            next_action = "reflect"
        elif state["explanation"] is None and state.get("execution_result") is not None:
            # Generate explanation if we have execution results (even if empty)
            next_action = "generate_explanation"
        else:
            next_action = "complete"
            updates["is_complete"] = True
        
        logger.info(f"Planning decision: {next_action} (iteration {iteration})")
        updates["next_action"] = next_action
        
        return updates
    
    def _execute_tools_node(self, state: AgentState) -> Dict:
        """
        Execute the tool specified by planning node (dataset-aware).
        Architecture Reference: Section 6.2 (Tool Catalog)
        """
        action = state["next_action"]
        dataset_id = state.get("dataset_id", "sales")
        logger.info(f"Execute tools node: action={action}, dataset={dataset_id}")
        
        # Map actions to tools with parameters (dataset-aware)
        tool_mapping = {
            "get_schema": ("get_schema", {"query": state["resolved_query"], "dataset_id": dataset_id}),
            "execute_sql": ("execute_sql", {"sql": state["sql_query"], "dataset_id": dataset_id}),
            "validate_results": ("validate_results", {
                "query": state["resolved_query"],
                "sql": state["sql_query"],
                "results": state["execution_result"]
            })
        }
        
        updates = {}
        
        if action not in tool_mapping:
            logger.warning(f"Unknown action '{action}', skipping tool execution")
            return updates
        
        # Execute tool (Architecture Section 6.1)
        tool_name, params = tool_mapping[action]
        logger.info(f"Executing tool: {tool_name}")
        
        tool_result = self.tools[tool_name].execute(**params)
        updates["tool_calls"] = [tool_result]
        
        # Update state based on tool (Architecture Section 6.2)
        if tool_result.get("success"):
            result = tool_result.get("result")
            
            if tool_name == "get_schema":
                updates["schema"] = result
                logger.info(f"Schema retrieved: {len(result)} chars")
            elif tool_name == "execute_sql":
                updates["execution_result"] = result
                # Note: QueryExecutor returns 'results' key, not 'data'
                row_count = len(result.get("results", []))
                logger.info(f"SQL executed: {row_count} rows returned")
            elif tool_name == "validate_results":
                updates["validation_result"] = result
                logger.info(f"Validation complete: valid={result.get('is_valid')}")
        else:
            # Tool failed (Architecture Section 6.1)
            error = tool_result.get("error", "Unknown error")
            logger.error(f"Tool '{tool_name}' failed: {error}")
            updates["error"] = f"Tool {tool_name}: {error}"
        
        return updates
    
    def _generate_sql_node(self, state: AgentState) -> Dict:
        """
        Generate SQL using Claude with collected context.
        Architecture Reference: Section 5.3 (SQL Generation Node)
        Performance Target: ≤2s (Section 13.1)
        Story: STORY-001 - Conversation Context for Follow-Up Queries
        """
        query = state["user_query"]
        schema = state.get("schema")
        session_id = state.get("session_id")  # NEW: Get session_id for context retrieval

        logger.info(f"Generating SQL for: '{query[:100]}'")
        logger.info(f"Using schema: {'Yes' if schema else 'No (using default)'}")

        # NEW: Format conversation context (STORY-001, AC1)
        conversation_context = None
        if session_id:
            conversation_context = self._format_conversation_context(session_id, max_entries=5)
            if conversation_context:
                logger.info(f"Including conversation context ({len(conversation_context)} chars)")

        start_time = datetime.now()

        try:
            # Call existing ClaudeService with custom schema (Architecture Section 11.1)
            sql_query = self.claude_service.generate_sql(
                natural_language_query=query,
                client_id=state.get("client_id", 1),
                client_name=state.get("client_name"),
                custom_schema=schema,  # Use schema from active dataset
                dataset_id=state.get("dataset_id", "sales"),  # Pass dataset for filtering instructions
                conversation_context=conversation_context  # NEW: Pass context to Claude (STORY-001, AC2)
            )

            # Log raw response for debugging
            logger.info(f"Raw Claude response (first 1000 chars): {sql_query[:1000]}...")
            logger.debug(f"Full Claude response: {sql_query}")

            # Extract clean SQL (Architecture Section 5.3)
            sql = self._extract_sql(sql_query)

            # Store raw response for chart metadata extraction
            raw_claude_response = sql_query
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"SQL generated in {elapsed:.2f}s: {sql[:100]}...")
            
            # Performance warning (Architecture Section 13.1)
            if elapsed > 2.0:
                logger.warning(f"SQL generation exceeded 2s target: {elapsed:.2f}s")
            
            # STORY: Query Expansion Architecture - Story 3 (Corp ID Safety Net)
            # Option C: Auto-inject corp_id if missing, with loud logging
            client_id = state.get("client_id", 1)
            sql = self._ensure_corp_id_filter(sql, client_id)
            
            # Security validation (runs after auto-injection as additional safety layer)
            dataset_id = state.get("dataset_id", "sales")
            security_validation = self._validate_sql_security(sql, client_id, dataset_id)
            
            # Check if security validation passed
            if not security_validation.get("passed", False):
                failed_checks = [c for c in security_validation.get("checks", []) if c.get("status") == "FAIL"]
                logger.error(f"Security validation failed: {len(failed_checks)} check(s) failed")
                
                # Return error and stop workflow
                return {
                    "error": f"Security validation failed: {', '.join([c['name'] for c in failed_checks])}",
                    "security_validation": security_validation,
                    "is_complete": True
                }
            
            logger.info("✓ Security validation passed")

            return {
                "sql_query": sql,
                "raw_sql_response": raw_claude_response,  # Store for chart metadata parsing
                "security_validation": security_validation
            }
            
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"SQL generation failed after {elapsed:.2f}s: {e}", exc_info=True)
            
            return {
                "error": f"SQL generation failed: {str(e)}",
                "is_complete": True  # Stop workflow on generation failure (Architecture Section 5.3)
            }
    
    def _extract_sql(self, sql_response: str) -> str:
        """
        Extract clean SQL from Claude response.
        Removes markdown code blocks, chart_metadata JSON, explanatory text, and extra whitespace.
        Architecture Reference: Section 5.3
        """
        logger.debug(f"Extracting SQL from response: {sql_response[:200]}...")

        sql = sql_response.strip()

        # CRITICAL FIX: If response contains markdown SQL block, extract ONLY the SQL
        # This handles cases where Claude adds explanatory text before the SQL
        if '```sql' in sql.lower() or '```\nselect' in sql.lower():
            # Find the start of the SQL block
            sql_block_start = sql.lower().find('```sql')
            if sql_block_start == -1:
                sql_block_start = sql.lower().find('```\nselect')

            if sql_block_start != -1:
                # Extract from the code block start
                sql = sql[sql_block_start:]

                # Find the closing ```
                closing_backticks = sql.find('```', 3)  # Start search after opening ```
                if closing_backticks != -1:
                    sql = sql[3:closing_backticks]  # Extract content between backticks
                    # Remove 'sql' language tag if present
                    if sql.lower().startswith('sql\n'):
                        sql = sql[4:]
                    elif sql.lower().startswith('sql '):
                        sql = sql[4:]
                else:
                    # No closing backticks found, remove opening ```
                    sql = sql[3:]
                    if sql.lower().startswith('sql\n'):
                        sql = sql[4:]
                    elif sql.lower().startswith('sql '):
                        sql = sql[4:]

                sql = sql.strip()
                logger.info("Extracted SQL from markdown code block, removed explanatory text")

        # Fallback: Handle simple ``` blocks without 'sql' tag
        elif sql.startswith('```'):
            lines = sql.split('\n')
            # Filter out lines that are just backticks or language tags
            sql_lines = []
            for line in lines:
                if line.strip() in ['```', '```sql', '```SQL']:
                    continue
                sql_lines.append(line)
            sql = '\n'.join(sql_lines).strip()
            logger.info("Extracted SQL from simple markdown block")

        # Remove chart_metadata JSON if present (it will be parsed separately)
        # Look for opening brace that starts the JSON object
        chart_meta_pos = sql.find('{')
        if chart_meta_pos != -1:
            # Check if this looks like chart_metadata JSON (contains "chart_metadata" key)
            remaining = sql[chart_meta_pos:]
            if '"chart_metadata"' in remaining or "'chart_metadata'" in remaining:
                # Remove everything from the opening brace onwards
                sql = sql[:chart_meta_pos].strip()
                logger.debug("Removed chart_metadata JSON from SQL")

        # Final validation: SQL should start with SELECT, WITH, or INSERT/UPDATE/DELETE
        sql_upper = sql.upper().strip()
        if not any(sql_upper.startswith(kw) for kw in ['SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE']):
            logger.warning(f"Extracted SQL doesn't start with valid keyword. First 100 chars: {sql[:100]}")
            # Try to find SELECT and extract from there
            select_pos = sql_upper.find('SELECT')
            if select_pos != -1:
                sql = sql[select_pos:]
                logger.info(f"Found SELECT at position {select_pos}, extracted from there")

        logger.debug(f"Final extracted SQL (first 200 chars): {sql[:200]}...")

        return sql

    def _parse_and_validate_chart_metadata(
        self,
        claude_response: str,
        sql: str,
        execution_result: Dict
    ) -> Dict:
        """
        Extract and validate chart metadata from Claude's response.

        Args:
            claude_response: Raw response from Claude (may contain JSON)
            sql: The generated SQL query
            execution_result: Actual query results with columns

        Returns:
            Valid chart_metadata dict or fallback
        """
        import json
        import re

        logger.debug(f"Parsing chart metadata from response: {claude_response[:500]}...")

        chart_metadata = None

        # Strategy: Use brace-matching to extract nested JSON
        # Find the position of "chart_metadata"
        chart_meta_pos = claude_response.find('"chart_metadata"')
        if chart_meta_pos != -1:
            # Find the opening brace after "chart_metadata":
            start_brace = claude_response.find('{', chart_meta_pos)
            if start_brace != -1:
                # Use a simple brace counter to find matching closing brace
                brace_count = 0
                i = start_brace
                while i < len(claude_response):
                    if claude_response[i] == '{':
                        brace_count += 1
                    elif claude_response[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # Found matching closing brace
                            json_str = claude_response[start_brace:i+1]
                            try:
                                chart_metadata = json.loads(json_str)
                                logger.info("Successfully extracted chart_metadata using brace matching")
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to parse chart_metadata JSON: {e}")
                                logger.debug(f"Attempted JSON: {json_str}")
                                return self._fallback_chart_metadata(execution_result)
                            break
                    i += 1

        if not chart_metadata:
            logger.warning("No chart_metadata found in Claude response, using fallback")
            return self._fallback_chart_metadata(execution_result)

        # Validation: Ensure referenced columns exist in SQL results
        # STORY-001: Defensive check - ensure execution_result is a dict
        if not execution_result or isinstance(execution_result, str):
            logger.warning(f"Invalid execution_result in chart validation: {type(execution_result)}")
            return self._fallback_chart_metadata({})

        actual_columns = execution_result.get("columns", [])

        x_axis = chart_metadata.get("x_axis")
        y_axes = chart_metadata.get("y_axes", [])

        # Validate x_axis
        if x_axis and x_axis not in actual_columns:
            logger.warning(f"x_axis '{x_axis}' not in query columns: {actual_columns}")
            chart_metadata["x_axis"] = actual_columns[0] if actual_columns else None

        # Validate y_axes
        valid_y_axes = [y for y in y_axes if y in actual_columns]
        if not valid_y_axes and len(actual_columns) > 1:
            valid_y_axes = actual_columns[1:]  # Fallback to remaining columns
        chart_metadata["y_axes"] = valid_y_axes

        # Add validation flag
        chart_metadata["validated"] = True

        logger.info(f"Chart metadata validated: type={chart_metadata.get('type')}, "
                   f"x_axis={chart_metadata.get('x_axis')}, "
                   f"y_axes={chart_metadata.get('y_axes')}, "
                   f"recommended={chart_metadata.get('recommended')}")

        return chart_metadata

    def _fallback_chart_metadata(self, execution_result: Dict) -> Dict:
        """
        Generate fallback chart metadata when LLM doesn't provide it.
        Uses simple heuristics similar to current frontend logic.

        Args:
            execution_result: Query execution results with columns and row_count

        Returns:
            Fallback chart metadata dict
        """
        # STORY-001: Defensive check - ensure execution_result is a dict
        if not execution_result or isinstance(execution_result, str):
            logger.warning(f"Invalid execution_result in _fallback_chart_metadata: {type(execution_result)}")
            return {
                "type": "table",
                "x_axis": None,
                "y_axes": [],
                "recommended": False,
                "reason": "Invalid execution result"
            }

        columns = execution_result.get("columns", [])
        row_count = execution_result.get("row_count", 0)

        logger.warning("Using fallback chart metadata - LLM did not provide valid metadata")

        if row_count > 100:
            return {
                "type": "table",
                "x_axis": None,
                "y_axes": [],
                "recommended": False,
                "reason": "Too many rows for effective visualization",
                "validated": False
            }

        if len(columns) < 2:
            return {
                "type": "metric",
                "x_axis": None,
                "y_axes": columns,
                "recommended": True,
                "reason": "Single value - displayed as metric card",
                "validated": False
            }

        # Simple heuristic: first col = x, rest = y
        return {
            "type": "bar",
            "x_axis": columns[0],
            "y_axes": columns[1:],
            "recommended": True,
            "reason": "Fallback visualization - LLM metadata unavailable",
            "validated": False
        }
    
    def _reflect_node(self, state: AgentState) -> Dict:
        """
        Evaluate SQL quality and decide if retry needed.
        Architecture Reference: Section 5.3.3 (Reflection Node Design)
        Performance Target: ≤200ms (Section 13.1)
        """
        start_time = datetime.now()
        
        sql = state.get("sql_query")
        execution_result = state.get("execution_result")
        validation_result = state.get("validation_result")
        iteration = state.get("iteration", 0)
        
        logger.info(f"Reflecting on SQL quality (iteration {iteration})...")
        logger.info(f"  SQL: {sql[:100] if sql else 'None'}...")
        
        should_refine = False
        issues = []
        
        # Critical error detection (Architecture Section 5.3.3)
        # STORY-001: Defensive check - ensure execution_result is a dict before calling .get()
        if execution_result and isinstance(execution_result, dict) and not execution_result.get("success"):
            error_msg = execution_result.get("error", "").lower()
            
            # Critical keywords from architecture
            critical_keywords = [
                "syntax error", "parse error", "invalid sql",
                "unknown column", "unknown table",
                "no such table", "no such column"
            ]
            
            # Check if critical error
            if any(kw in error_msg for kw in critical_keywords):
                should_refine = True
                issues.append(f"Critical SQL error: {error_msg}")
                logger.warning(f"Critical error detected: {error_msg}")
            else:
                # Non-critical error, proceed
                issues.append(f"{error_msg}")
                logger.info(f"Non-critical error (proceeding): {error_msg}")
        
        # Empty results check (informational, not critical)
        if validation_result and not validation_result.get("has_results"):
            issues.append("Query returned no results")
            logger.info("Empty results - might be correct, proceeding")
        
        # Build reflection result
        reflection = {
            "is_acceptable": not should_refine,
            "should_refine": should_refine,
            "issues": issues,
            "reasoning": "SQL has critical errors requiring retry" if should_refine else "SQL quality acceptable"
        }
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Reflection complete in {elapsed:.3f}s: acceptable={reflection['is_acceptable']}, refine={should_refine}, issues={len(issues)}")
        
        return {"reflection_result": reflection}
    
    def _generate_explanation_node(self, state: AgentState) -> Dict:
        """
        Generate natural language explanation of results.
        Architecture Reference: Section 5.3.4
        Performance Target: ≤2s (Section 13.1)
        """
        query = state["user_query"]
        sql = state["sql_query"]
        results = state["execution_result"]
        
        logger.info("Generating natural language explanation...")
        start_time = datetime.now()
        
        # Handle empty results (Architecture Section 5.3.4)
        # Note: QueryExecutor returns 'results' key, not 'data'
        if not results or not results.get("results"):
            explanation = "The query returned no results. This might indicate that no data matches the specified criteria."
            logger.info("Empty results - returning default explanation")
            return {"explanation": explanation}
        
        # Prepare data for Claude (limit sample, Architecture Section 5.3.4)
        data = results["results"]  # QueryExecutor returns 'results' key
        columns = results.get("columns", [])
        row_count = len(data)
        sample_data = data[:20]  # Performance: limit data sent to Claude
        
        logger.info(f"Explaining {row_count} rows (sample: {len(sample_data)})")
        
        try:
            # Format data for explanation prompt
            data_sample = self._format_data_for_explanation(sample_data, columns)
            
            explanation_prompt = f"""Analyze these query results and provide a clear explanation in 2-4 sentences.

User's Question: {query}

Generated SQL: {sql}

Results ({row_count} total rows, showing sample):
Columns: {', '.join(columns)}

Data Sample:
{data_sample}

Provide explanation that:
1. Directly answers the user's question
2. Highlights key findings (top values, trends, patterns)
3. Notes interesting comparisons or anomalies
4. Uses plain English for business stakeholders

Write as if explaining to a non-technical business user."""
            
            response = self.claude_service.client.messages.create(
                model=self.claude_service.model,
                max_tokens=300,
                temperature=0.7,
                system="You are a data insights analyst. Transform query results into clear, actionable insights.",
                messages=[{"role": "user", "content": explanation_prompt}]
            )
            
            explanation = response.content[0].text.strip()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Explanation generated in {elapsed:.2f}s: {explanation[:100]}...")
            
            # Performance warning (Architecture Section 13.1)
            if elapsed > 2.0:
                logger.warning(f"Explanation exceeded 2s target: {elapsed:.2f}s")
            
            return {"explanation": explanation}
            
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"Explanation generation failed after {elapsed:.2f}s: {e}", exc_info=True)
            
            # Graceful degradation (Architecture Section 2.1)
            fallback = f"Found {row_count} result(s) for your query."
            logger.warning(f"Using fallback explanation: {fallback}")
            return {"explanation": fallback}
    
    def _format_data_for_explanation(self, data: List[Dict], columns: List[str]) -> str:
        """Format data rows for explanation prompt"""
        if not data:
            return "No data"
        
        lines = []
        for row in data[:10]:  # Max 10 rows in prompt
            row_str = " | ".join([str(row.get(col, 'N/A')) for col in columns])
            lines.append(row_str)
        
        return "\n".join(lines)
    
    def _should_refine(self, state: AgentState) -> str:
        """
        Conditional routing: refine back to plan or continue to plan.
        Architecture Reference: Section 4.2 (Conditional Edges), Section 10.3 (Retry Flow)
        """
        reflection = state.get("reflection_result", {})
        iteration = state.get("iteration", 0)
        max_iterations = state.get("max_iterations", 3)
        
        should_refine = reflection.get("should_refine", False)
        
        # Refinement decision (Architecture Section 10.3)
        if should_refine and iteration < max_iterations:
            logger.info(f"Refining SQL (iteration {iteration}/{max_iterations})")
            
            # Reset state for retry (Architecture Section 10.3)
            state["sql_query"] = None
            state["execution_result"] = None
            state["validation_result"] = None
            
            return "refine"
        
        if iteration >= max_iterations:
            logger.warning(f"Max iterations reached, proceeding anyway")
        
        logger.info("Reflection complete, continuing workflow")
        return "continue"
    
    def _should_execute_or_generate(self, state: AgentState) -> str:
        """
        Conditional routing: execute_tools, generate_sql, reflect, generate_explanation, or complete.
        Architecture Reference: Section 4.2 (Conditional Edges)
        """
        action = state.get("next_action", "")
        
        if action == "generate_sql":
            return "generate_sql"
        elif action == "reflect":
            return "reflect"
        elif action == "generate_explanation":
            return "generate_explanation"
        elif action == "complete":
            return "complete"
        else:
            return "execute_tools"
    
    def _complete_node(self, state: AgentState) -> Dict:
        """
        Complete the workflow.
        Architecture Reference: Section 4.2
        
        Marks workflow as complete. Future stories will add explanation generation here.
        """
        logger.info("Complete node: workflow finished")
        return {"is_complete": True}
    
    def generate_sql_with_agent(
        self,
        user_query: str,
        session_id: str,
        client_id: int = 1,
        dataset_id: str = "sales",
        max_iterations: int = 3
    ) -> Dict:
        """
        Generate SQL using agentic approach with LangGraph orchestration and conversation context.
        
        Args:
            user_query: Natural language query from user
            session_id: Session identifier for conversation context
            client_id: Client ID for data isolation (default: 1)
            dataset_id: Dataset identifier (sales, market_size, etc., default: sales)
            max_iterations: Maximum retry attempts (default: 3)
            
        Returns:
            Dict with SQL, results, security validation, and workflow metadata
            
        Architecture Reference: Section 4.1 (AgentState), Section 7.1 (Session Management)
        """
        start_time = datetime.now()
        logger.info(f"Starting agentic workflow: session={session_id}, query='{user_query[:100]}'")
        
        # Get conversation history
        chat_history = self._get_chat_history(session_id)
        
        # Detect if this is a clarified query (has "Additional information:" or "Additional context:")
        # Check BEFORE expansion to handle clarification properly
        is_clarified_query = "Additional information:" in user_query or "Additional context:" in user_query
        
        # STORY: Query Expansion Architecture - Story 1
        # Expand query at natural language level (no SQL parsing needed)
        # For clarified queries, skip expansion or handle specially to preserve clarification context
        if is_clarified_query:
            logger.info("Clarified query detected - preserving clarification context in expansion")
            # For clarified queries, pass through expansion but preserve the clarification format
            expanded_query = self._expand_query_with_context(user_query, chat_history, is_clarified=True)
        else:
            expanded_query = self._expand_query_with_context(user_query, chat_history)
        
        # Track if query was expanded (for logging/debugging)
        is_expanded = (expanded_query != user_query)
        if is_expanded:
            logger.info(f"Query expanded: '{user_query}' → '{expanded_query}'")
        
        try:
            skip_clarification = is_clarified_query
            if skip_clarification:
                logger.info("Clarified query detected - skipping ambiguity detection")

            # Fetch client name from database
            client_name = self._fetch_client_name(client_id, dataset_id)
            logger.error(f"DEBUG: Fetched client_name='{client_name}' for client_id={client_id}, dataset={dataset_id}")
            
            # Initialize state (Architecture Section 4.1 + Query Expansion Architecture)
            initial_state: AgentState = {
                "user_query": user_query,  # Original user input
                "session_id": session_id,
                "resolved_query": expanded_query,  # Expanded/complete query for SQL generation
                "client_id": client_id,
                "client_name": client_name,
                "dataset_id": dataset_id,
                "chat_history": [],
                "iteration": 0,
                "max_iterations": max_iterations,
                "schema": None,
                "sample_data": {},
                "metadata_context": [],
                "sql_query": None,
                "execution_result": None,
                "validation_result": None,
                "security_validation": None,
                "explanation": None,
                "reflection_result": None,
                "clarification_needed": False,
                "clarification_questions": [],
                "is_followup": is_expanded,  # True if query was expanded
                "resolution_info": {"expanded_query": expanded_query, "was_expanded": is_expanded},
                "tool_calls": [],
                "next_action": "plan",
                "is_complete": False,
                "error": None,
                "skip_clarification_check": skip_clarification
            }
            
            # Run workflow (Architecture Section 4.2)
            final_state = self.workflow.invoke(initial_state)
            
            # Performance tracking (Architecture Section 13.3)
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Workflow completed in {elapsed:.2f}s, {final_state.get('iteration', 0)} iterations")
            
            # Store to session history (simplified - Query Expansion Architecture)
            if final_state.get("sql_query") and not final_state.get("clarification_needed"):
                # Simplified history entry - no filter extraction needed
                history_entry = {
                    "user_query": user_query,  # Original user input
                    "expanded_query": expanded_query,  # Expanded query (if any)
                    "sql_query": final_state.get("sql_query"),  # Generated SQL
                    "timestamp": datetime.now().isoformat(),
                    "was_expanded": is_expanded  # Track if expansion occurred
                }
                self._add_to_history(session_id, history_entry)
                logger.info(f"Added history entry: '{user_query}' (expanded: {is_expanded})")
            
            return self._format_response(final_state)
            
        except Exception as e:
            logger.error(f"Agentic workflow failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "method": "agentic",
                "session_id": session_id
            }
    
    def _format_response(self, state: AgentState) -> Dict:
        """
        Format the final response.
        
        Returns standardized response format for API endpoint.
        Handles clarification responses (Architecture Section 10.2).
        """
        # Check if clarification needed (AC5)
        if state.get("clarification_needed", False):
            return {
                "success": False,
                "needs_clarification": True,
                "questions": state.get("clarification_questions", []),
                "method": "agentic",
                "session_id": state["session_id"]
            }
        
        # Normal response (Architecture Section 8.1)
        response = {
            "success": True,
            "sql": state.get("sql_query"),
            "explanation": state.get("explanation"),
            "method": "agentic",
            "session_id": state["session_id"],
            "iterations": state.get("iteration", 0),
            "tool_calls": len(state.get("tool_calls", [])),
            "clarification_needed": False
        }
        
        # Include results if available (for frontend display)
        execution_result = state.get("execution_result")
        if execution_result:
            response["results"] = execution_result

            # Parse and validate chart metadata from Claude response
            try:
                raw_sql_response = state.get("raw_sql_response", "")
                chart_metadata = self._parse_and_validate_chart_metadata(
                    claude_response=raw_sql_response,
                    sql=state.get("sql_query", ""),
                    execution_result=execution_result
                )
                response["chart_metadata"] = chart_metadata
            except Exception as e:
                logger.error(f"Failed to parse chart metadata: {e}", exc_info=True)
                # Use fallback instead of failing the entire query
                response["chart_metadata"] = self._fallback_chart_metadata(execution_result)
        
        # Include validation if available
        validation = state.get("validation_result")
        if validation:
            response["validation"] = validation
        
        # Include reflection if available
        reflection = state.get("reflection_result")
        if reflection:
            response["reflection"] = reflection
        
        # Include security validation if available (NEW - POC enhancement)
        security_validation = state.get("security_validation")
        if security_validation:
            response["security_validation"] = security_validation
        
        # Include follow-up info (Story 7.1)
        response["is_followup"] = state.get("is_followup", False)
        resolution_info = state.get("resolution_info")
        if resolution_info and response["is_followup"]:
            response["resolution_info"] = {
                "interpreted_as": resolution_info.get("resolved_query"),
                "confidence": resolution_info.get("confidence", 0.0),
                "interpretation": resolution_info.get("interpretation")
            }
        
        # Add key details for Passport AI-style insights
        response["key_details"] = self._generate_key_details(state, execution_result)
        
        return response
    
    def _extract_filters_from_state(self, state: AgentState) -> List[str]:
        """
        Extract human-readable filters from SQL query in agent state.
        
        Args:
            state: Current agent state with SQL query
            
        Returns:
            List of filter descriptions
        """
        sql_query = state.get("sql_query", "")
        filters = []
        
        if not sql_query:
            return filters
        
        # Add client/corporation filter (always present)
        client_name = state.get("client_name", "Unknown")
        dataset_id = state.get("dataset_id", "")
        
        if dataset_id == "em_market":
            filters.append(f"Corporation: {client_name}")
        else:
            filters.append(f"Client: {client_name}")
        
        # Extract year filters
        import re
        year_pattern = r"(?:fiscal_year|year)\s*=\s*(\d{4})"
        year_matches = re.findall(year_pattern, sql_query, re.IGNORECASE)
        if year_matches:
            filters.append(f"Year: {', '.join(year_matches)}")
        
        # Extract product category filters
        category_pattern = r"(?:product_category|category_name)\s*=\s*['\"]([^'\"]+)['\"]"
        category_matches = re.findall(category_pattern, sql_query, re.IGNORECASE)
        if category_matches:
            filters.append(f"Product Category: {', '.join(category_matches)}")
        
        # Extract country/geography filters
        country_pattern = r"(?:country_name|country)\s*=\s*['\"]([^'\"]+)['\"]"
        country_matches = re.findall(country_pattern, sql_query, re.IGNORECASE)
        if country_matches:
            filters.append(f"Country: {', '.join(country_matches)}")
        
        # Extract brand filters
        brand_pattern = r"(?:brand_name|brand)\s*=\s*['\"]([^'\"]+)['\"]"
        brand_matches = re.findall(brand_pattern, sql_query, re.IGNORECASE)
        if brand_matches:
            filters.append(f"Brand: {', '.join(brand_matches)}")
        
        # Extract measure type from aggregations
        if "SUM(" in sql_query.upper():
            sum_pattern = r"SUM\(([^)]+)\)"
            sum_matches = re.findall(sum_pattern, sql_query, re.IGNORECASE)
            if sum_matches:
                # Clean up the field name
                measure = sum_matches[0].split('.')[-1].replace('_', ' ').title()
                filters.append(f"Measure: {measure}")
        
        return filters if filters else ["No specific filters applied"]
    
    def _format_result_summary(self, execution_result: Dict) -> str:
        """
        Format a human-readable summary of the query result.

        Args:
            execution_result: Query execution result with data

        Returns:
            Human-readable result summary
        """
        if not execution_result:
            return "No results found"

        # STORY-001: Defensive check - if execution_result is a string
        if isinstance(execution_result, str):
            logger.warning(f"execution_result is a string in _format_result_summary: {execution_result[:100]}")
            return execution_result

        if not execution_result.get("results"):
            return "No results found"

        results = execution_result["results"]
        row_count = len(results)
        
        if row_count == 0:
            return "No results found"
        elif row_count == 1:
            # Single result - try to extract the main value
            first_row = results[0]
            # Look for common value columns
            for key in first_row.keys():
                key_lower = key.lower()
                if any(term in key_lower for term in ['total', 'sum', 'value', 'count', 'sales', 'market', 'revenue']):
                    value = first_row[key]
                    if isinstance(value, (int, float)):
                        formatted_value = f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
                        return f"{formatted_value} ({key.replace('_', ' ').title()})"
            return f"Single result with {len(first_row)} columns"
        else:
            return f"{row_count} rows returned"
    
    def _fetch_client_name(self, client_id: int, dataset_id: str) -> str:
        """
        Fetch client/corporation name from the database.
        
        Args:
            client_id: Client or corporation ID
            dataset_id: Dataset identifier
            
        Returns:
            Client/corporation name or "Unknown"
        """
        logger.error(f"DEBUG: _fetch_client_name called with client_id={client_id}, dataset={dataset_id}")
        try:
            import sqlite3
            from config import Config
            
            dataset_config = Config.get_dataset(dataset_id)
            db_path = dataset_config['db_path']
            logger.error(f"DEBUG: db_path={db_path}")
            
            client_config = Config.get_client_config(dataset_id)
            logger.error(f"DEBUG: client_config={client_config}")
            
            # Get client table and field names
            client_table = client_config.get('client_table', 'clients')
            client_id_field = client_config.get('client_id_field', 'client_id')
            client_name_field = client_config.get('client_name_field', 'client_name')
            
            logger.error(f"DEBUG: Will query {client_table}.{client_name_field} WHERE {client_id_field}={client_id}")
            
            # Connect and query using sqlite3 directly
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            
            # Build safe query (client_id is validated as int)
            query = f"SELECT {client_name_field} FROM {client_table} WHERE {client_id_field} = ?"
            logger.error(f"DEBUG: Executing query: {query} with params ({int(client_id)},)")
            cursor.execute(query, (int(client_id),))
            
            result = cursor.fetchone()
            logger.error(f"DEBUG: Query result: {dict(result) if result else None}")
            conn.close()
            
            if result:
                name = result[client_name_field]
                logger.error(f"DEBUG: Successfully fetched client name: '{name}'")
                return name
            
            logger.error(f"DEBUG: No result found for client_id={client_id}")
            return "Unknown"
            
        except Exception as e:
            logger.error(f"DEBUG: Exception in _fetch_client_name: {e}", exc_info=True)
            return "Unknown"
    
    def _generate_key_details(self, state: AgentState, execution_result: Dict) -> Dict:
        """
        Generate key details object for Passport AI-style display.
        
        Args:
            state: Current agent state
            execution_result: Query execution result
            
        Returns:
            Key details dictionary
        """
        from config import Config
        
        dataset_id = state.get("dataset_id", "unknown")
        dataset_config = Config.get_dataset(dataset_id)
        
        key_details = {
            "dataset": dataset_config.get("name", dataset_id),
            "client": state.get("client_name", "Unknown"),
            "client_id": state.get("client_id"),
            "filters_applied": self._extract_filters_from_state(state),
            "result": self._format_result_summary(execution_result),
            # STORY-001: Defensive check - ensure execution_result is a dict
            "row_count": len(execution_result.get("results", [])) if execution_result and isinstance(execution_result, dict) else 0
        }
        
        return key_details
    
    def _initialize_tools(self) -> Dict[str, Tool]:
        """
        Initialize available tools.
        Architecture Reference: Section 6.2 (Tool Catalog)
        
        Returns:
            Dict mapping tool names to Tool instances
        """
        tools = {}
        
        # Tool: Get Schema
        tools['get_schema'] = Tool(
            name="get_schema",
            description="Retrieves database schema",
            function=self._get_schema_tool
        )
        
        # Tool: Execute SQL
        tools['execute_sql'] = Tool(
            name="execute_sql",
            description="Executes SQL query",
            function=self._execute_sql_tool
        )
        
        # Tool: Validate Results
        tools['validate_results'] = Tool(
            name="validate_results",
            description="Validates query results",
            function=self._validate_results_tool
        )
        
        logger.info(f"Initialized {len(tools)} tools: {list(tools.keys())}")
        return tools
    
    def _get_schema_tool(self, query: str = None, dataset_id: str = "sales") -> str:
        """
        Tool: Get database schema (dataset-aware).
        Architecture Reference: Section 6.2 (get_schema tool)
        Performance Target: ≤100ms
        """
        logger.info(f"Retrieving database schema for dataset: {dataset_id}...")
        
        try:
            from config import Config
            import sqlite3
            
            # Get dataset configuration
            dataset_config = Config.get_dataset(dataset_id)
            db_path = dataset_config['db_path']
            
            # Dynamically fetch schema from database
            schema = self._fetch_schema_from_db(db_path)
            logger.info(f"Schema retrieved from {dataset_id}: {len(schema)} characters")
            return schema
            
        except Exception as e:
            logger.error(f"Schema retrieval failed: {e}", exc_info=True)
            raise  # Re-raise for Tool class to handle
    
    def _fetch_schema_from_db(self, db_path: str) -> str:
        """
        Dynamically fetch schema from a SQLite database with data context.
        
        Args:
            db_path: Path to SQLite database file
            
        Returns:
            str: CREATE TABLE statements + data availability metadata
        """
        import sqlite3
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        schema_parts = []
        for (table_name,) in tables:
            # Get CREATE TABLE statement
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            create_stmt = cursor.fetchone()[0]
            schema_parts.append(create_stmt + ";")
        
        # Add data availability metadata
        metadata = ["\n-- DATA AVAILABILITY & GUIDANCE:"]
        
        # Check for dim_time table
        if any('dim_time' in str(t) for t in tables):
            cursor.execute("SELECT MIN(year), MAX(year) FROM dim_time WHERE is_forecast = 0")
            result = cursor.fetchone()
            if result and result[0]:
                metadata.append(f"-- Actual data years: {result[0]} to {result[1]}")
            
            cursor.execute("SELECT MIN(year), MAX(year) FROM dim_time WHERE is_forecast = 1")
            result = cursor.fetchone()
            if result and result[0]:
                metadata.append(f"-- Forecast years: {result[0]} to {result[1]}")
        
        # Check for fact tables with year columns
        fact_tables = [t[0] for t in tables if 'fact_' in t[0]]
        for fact_table in fact_tables:
            try:
                cursor.execute(f"SELECT MIN(year), MAX(year) FROM {fact_table}")
                result = cursor.fetchone()
                if result and result[0]:
                    metadata.append(f"-- {fact_table} data: {result[0]} to {result[1]}")
            except:
                pass
        
        metadata.append("-- IMPORTANT: For 'last N years' queries, use fact table's MAX(year) - N, not current date!")
        metadata.append("--   Example: year >= (SELECT MAX(year) - 1 FROM <fact_table> WHERE is_forecast = 0)")
        
        conn.close()
        
        schema_with_metadata = "\n\n".join(schema_parts) + "\n" + "\n".join(metadata)
        return schema_with_metadata
    
    def _execute_sql_tool(self, sql: str, dataset_id: str = "sales") -> Dict:
        """
        Tool: Execute SQL query safely (dataset-aware).
        Architecture Reference: Section 6.2 (execute_sql tool)
        Performance Target: ≤500ms
        """
        logger.info(f"Executing SQL on dataset {dataset_id}: {sql[:100]}...")
        
        try:
            from services.query_executor import QueryExecutor
            from config import Config
            
            # Get dataset configuration and database path
            dataset_config = Config.get_dataset(dataset_id)
            db_path = dataset_config['db_path']
            
            # Use QueryExecutor with dataset-specific database
            executor = QueryExecutor(database_path=db_path)
            result = executor.execute_query(sql)
            
            row_count = len(result.get("data", []))
            logger.info(f"SQL executed successfully: {row_count} rows")
            
            return result
            
        except Exception as e:
            logger.error(f"SQL execution failed: {e}", exc_info=True)
            raise  # Re-raise for Tool class to handle
    
    def _validate_results_tool(self, query: str, sql: str, results: Dict) -> Dict:
        """
        Tool: Validate SQL results.
        Architecture Reference: Section 6.2 (validate_results tool)
        Performance Target: ≤100ms
        """
        logger.info("Validating results...")
        
        try:
            # Note: QueryExecutor returns 'results' key, not 'data'
            validation = {
                "is_valid": True,
                "has_results": bool(results.get("results")),
                "row_count": len(results.get("results", [])),
                "issues": []
            }
            
            # Check for results (informational, not critical)
            if not validation["has_results"]:
                validation["issues"].append("No results returned")
                logger.info("Validation: No results (might be correct)")
            
            # Check for execution errors
            if not results.get("success", True):
                validation["issues"].append(f"Execution error: {results.get('error')}")
                logger.warning(f"Validation: Execution error detected")
            
            logger.info(f"Validation complete: {len(validation['issues'])} issue(s)")
            
            return validation
            
        except Exception as e:
            logger.error(f"Validation failed: {e}", exc_info=True)
            raise  # Re-raise for Tool class to handle
    
    def _ensure_corp_id_filter(self, sql: str, client_id: int) -> str:
        """
        Hybrid security approach (Option C): Ensure corp_id filter exists.
        Auto-inject if missing, but log LOUDLY for monitoring.
        
        Story: Query Expansion Architecture - Story 3
        Goal: Reduce auto-injection frequency to zero over time through prompt improvements.
        
        Args:
            sql: Generated SQL query
            client_id: Expected client/corporation ID
            
        Returns:
            SQL with corp_id filter guaranteed to exist
        """
        # Check if corp_id filter exists (case-insensitive)
        sql_lower = sql.lower()
        corp_id_patterns = [
            f"corp_id = {client_id}",
            f"corp_id={client_id}",
            f"corp_id = '{client_id}'",  # Sometimes might be quoted
        ]
        
        has_corp_id = any(pattern in sql_lower for pattern in [p.lower() for p in corp_id_patterns])
        
        if has_corp_id:
            return sql  # All good!
        
        # ⚠️ CORP_ID MISSING - AUTO-INJECT WITH LOUD LOGGING
        logger.warning("=" * 80)
        logger.warning("⚠️  CORP_ID AUTO-INJECTION TRIGGERED")
        logger.warning("=" * 80)
        logger.warning(f"Client ID: {client_id}")
        logger.warning(f"SQL (BEFORE): {sql[:200]}...")
        logger.warning("")
        logger.warning("Claude forgot to include the mandatory corp_id filter!")
        logger.warning("This indicates a prompt engineering issue that needs fixing.")
        logger.warning("")
        logger.warning("ACTION REQUIRED:")
        logger.warning("1. Review system prompt for corp_id emphasis")
        logger.warning("2. Check if conversation context mentions corp_id requirement")
        logger.warning("3. Monitor frequency - goal is to reduce this to ZERO")
        logger.warning("=" * 80)
        
        # Auto-inject corp_id into WHERE clause
        try:
            sql_upper = sql.upper()
            
            if "WHERE" in sql_upper:
                # Add corp_id to existing WHERE clause
                where_pos = sql_upper.find("WHERE")
                # Find position after WHERE keyword
                after_where = where_pos + 5  # len("WHERE")
                
                # Insert corp_id condition at start of WHERE clause
                sql = sql[:after_where] + f" corp_id = {client_id} AND " + sql[after_where:]
            else:
                # Add WHERE clause with corp_id
                # Find good insertion point (before GROUP BY, ORDER BY, LIMIT, or end)
                insertion_keywords = ["GROUP BY", "ORDER BY", "LIMIT", "HAVING"]
                insertion_pos = len(sql)
                
                for keyword in insertion_keywords:
                    pos = sql_upper.find(keyword)
                    if pos != -1 and pos < insertion_pos:
                        insertion_pos = pos
                
                # Insert WHERE clause
                sql = sql[:insertion_pos] + f" WHERE corp_id = {client_id} " + sql[insertion_pos:]
            
            logger.warning(f"SQL (AFTER):  {sql[:200]}...")
            logger.warning("✅ Corp ID filter auto-injected successfully")
            logger.warning("=" * 80)
            
        except Exception as e:
            logger.error(f"Failed to auto-inject corp_id: {e}", exc_info=True)
            logger.error("SQL remains unchanged - will likely fail security validation")
        
        return sql
    
    def _validate_sql_security(self, sql: str, client_id: int, dataset_id: str = "sales") -> Dict:
        """
        Validate SQL for security requirements (dataset-aware).
        Uses production-grade validator from sql_validator.py
        
        Security Checks:
        1. Client ID Filter - WHERE client_id = X required
        2. Single Client - No cross-client access
        3. Read-Only - No destructive operations
        
        Args:
            sql: SQL query to validate
            client_id: Expected client ID for isolation
            dataset_id: Dataset identifier for context
            
        Returns:
            Dict with validation results (passed, checks, warnings)
        """
        logger.info(f"Running security validation for client_id={client_id}, dataset={dataset_id}")
        
        try:
            from services.sql_validator import validate_sql_for_client_isolation
            from config import Config
            
            # Get dataset configuration
            dataset_config = Config.get_dataset(dataset_id)
            
            # Run full security validation with dataset context
            validation_result = validate_sql_for_client_isolation(sql, client_id, dataset_config)
            
            # Convert to dict format
            result = validation_result.to_dict()
            
            if validation_result.passed:
                logger.info("✓ Security validation PASSED")
            else:
                failed_checks = [c['name'] for c in validation_result.checks if c['status'] == 'FAIL']
                logger.error(f"✗ Security validation FAILED: {', '.join(failed_checks)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Security validation error: {e}", exc_info=True)
            raise

