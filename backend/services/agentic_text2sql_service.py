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
    
    def __init__(self):
        """Initialize service with existing dependencies and session storage."""
        self.claude_service = ClaudeService()
        self.db_engine = get_engine()
        self.tools = self._initialize_tools()
        self.workflow = self._build_workflow()
        
        # Session storage (Architecture Section 7.1 - in-memory for POC)
        self.chat_sessions = {}
        logger.info("AgenticText2SQLService initialized with session storage")
    
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
        entity_keywords = [
            "product", "products", "sales", "sale", "revenue", "client", "clients",
            "region", "regions", "category", "categories", "customer", "customers",
            "segment", "segments", "order", "orders", "transaction", "transactions",
            "metric", "metrics", "data", "records", "report", "reports"
        ]
        
        # Action keywords that indicate complete queries
        complete_action_keywords = [
            "list all", "show all", "get all", "display all",
            "show me all", "give me all", "find all"
        ]
        
        # Dimension modifiers that indicate follow-ups (overrides entity check)
        dimension_modifiers = [
            "by region", "by category", "by product", "by client",
            "by customer", "by segment", "for region", "for category"
        ]
        
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
        has_entity = any(word in query_lower for word in [
            "product", "products", "sales", "sale", "customer", "customers",
            "client", "clients", "order", "orders", "transaction", "transactions",
            "market", "markets", "region", "regions", "country", "countries"
        ])
        has_metric = any(word in query_lower for word in [
            "revenue", "quantity", "profit", "count", "total", "sum", "average",
            "how much", "how many", "all", "list"
        ])
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
            location_words = ["north", "south", "east", "west", "q1", "q2", "q3", "q4"]
            category_words = ["electronics", "furniture", "appliances", "fashion"]
            has_only_location = any(word in query_lower for word in location_words + category_words)
            
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
            if not (has_year or has_time_keyword):
                questions.append("Which time period?")
        
        # Check for performance without metric
        if "performance" in query_lower:
            has_metric = any(word in query_lower for word in ["revenue", "sales", "quantity", "profit", "growth", "margin"])
            if not has_metric:
                questions.append("Which metric (revenue, quantity, growth)?")
        
        # Check for top/best without sufficient criteria
        if ("top" in query_lower or "best" in query_lower):
            has_entity_specific = any(word in query_lower for word in [
                "product", "products", "sales", "sale", "customer", "customers",
                "client", "clients", "market", "markets", "region", "regions", "country", "countries"
            ])
            has_metric_specific = any(word in query_lower for word in [
                "revenue", "sales", "sold", "quantity", "profit", "popular", "selling",
                "value", "units", "growth", "share", "size"
            ])
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
        """
        query = state["user_query"]
        schema = state.get("schema")
        
        logger.info(f"Generating SQL for: '{query[:100]}'")
        logger.info(f"Using schema: {'Yes' if schema else 'No (using default)'}")
        
        start_time = datetime.now()
        
        try:
            # Call existing ClaudeService with custom schema (Architecture Section 11.1)
            sql_query = self.claude_service.generate_sql(
                natural_language_query=query,
                client_id=state.get("client_id", 1),
                client_name=state.get("client_name"),
                custom_schema=schema  # Use schema from active dataset
            )
            
            # Extract clean SQL (Architecture Section 5.3)
            sql = self._extract_sql(sql_query)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"SQL generated in {elapsed:.2f}s: {sql[:100]}...")
            
            # Performance warning (Architecture Section 13.1)
            if elapsed > 2.0:
                logger.warning(f"SQL generation exceeded 2s target: {elapsed:.2f}s")
            
            # Security validation (NEW - POC enhancement)
            # Validate SQL for client isolation and security requirements
            client_id = state.get("client_id", 1)
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
        Removes markdown code blocks and extra whitespace.
        Architecture Reference: Section 5.3
        """
        logger.debug(f"Extracting SQL from response: {sql_response[:100]}...")
        
        sql = sql_response.strip()
        
        # Remove markdown code blocks (```sql ... ``` or ``` ... ```)
        if sql.startswith('```'):
            lines = sql.split('\n')
            # Filter out lines that are just backticks or language tags
            sql_lines = []
            for line in lines:
                if line.strip() in ['```', '```sql', '```SQL']:
                    continue
                sql_lines.append(line)
            sql = '\n'.join(sql_lines).strip()
        
        logger.debug(f"Extracted SQL: {sql[:100]}...")
        
        return sql
    
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
        if execution_result and not execution_result.get("success"):
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
                issues.append(f"Non-critical error: {error_msg}")
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
        
        # Get conversation history (Architecture Section 7.1)
        chat_history = self._get_chat_history(session_id)
        
        # Story 7.1: Detect and resolve follow-up queries
        is_followup, confidence = self._detect_followup(user_query, chat_history)
        resolution = None
        
        if is_followup:
            logger.info(f"Follow-up detected (confidence: {confidence:.2f})")
            resolution = self._resolve_query_with_history(user_query, chat_history)
            resolved_query = resolution['resolved_query']
            resolution_confidence = resolution.get('confidence', 0.5)
            
            # Low confidence warning (Story 7.1 spec)
            if resolution_confidence < 0.8:
                logger.warning(f"Low resolution confidence: {resolution_confidence:.2f}, may need clarification")
        else:
            logger.info("New query (not a follow-up)")
            resolved_query = user_query
        
        try:
            # Detect if this is a clarified query (has "Additional context:")
            skip_clarification = "Additional context:" in user_query
            if skip_clarification:
                logger.info("Clarified query detected - skipping ambiguity detection")

            # Initialize state (Architecture Section 4.1 + Story 7.1 + Dataset Support)
            initial_state: AgentState = {
                "user_query": user_query,
                "session_id": session_id,
                "resolved_query": resolved_query,
                "client_id": client_id,
                "client_name": None,  # Could be fetched from DB if needed
                "dataset_id": dataset_id,  # Dataset support
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
                "is_followup": is_followup,
                "resolution_info": resolution,
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
            
            # Store to session history with enhanced metadata (Story 7.2)
            if final_state.get("sql_query") and not final_state.get("clarification_needed"):
                execution_result = final_state.get("execution_result", {})
                
                # Story 7.2: Extract entities from SQL
                key_entities = self._extract_entities(final_state)
                
                # Story 7.2: Summarize results
                results_summary = self._summarize_results(execution_result)
                
                # Build enhanced history entry (Story 7.2 - AC1)
                history_entry = {
                    "user_query": user_query,
                    "resolved_query": resolved_query,
                    "sql": final_state.get("sql_query"),
                    "results_summary": results_summary,
                    "key_entities": key_entities,
                    "timestamp": datetime.now().isoformat(),
                    "is_followup": is_followup
                }
                self._add_to_history(session_id, history_entry)
                logger.info(f"Added enhanced history entry with {len(key_entities.get('dimensions', []))} dimensions, {len(key_entities.get('metrics', []))} metrics")
            
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
        
        return response
    
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
            from datasets.dataset_config import get_dataset
            import sqlite3
            
            # Get dataset configuration
            dataset_config = get_dataset(dataset_id)
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
        metadata.append("--   Example: year >= (SELECT MAX(year) - 1 FROM fact_market_size WHERE is_forecast = 0)")
        
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
            from datasets.dataset_config import get_dataset
            
            # Get dataset configuration and database path
            dataset_config = get_dataset(dataset_id)
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
            from datasets.dataset_config import get_dataset
            
            # Get dataset configuration
            dataset_config = get_dataset(dataset_id)
            
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

