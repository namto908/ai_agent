from typing import List, Dict, Any, Set, Optional
from enum import Enum
from pydantic import BaseModel, Field

class Action(str, Enum):
    """Enum for valid agent actions."""
    KG_QUERY = "kg.query"
    RAG_SEARCH = "rag.search"
    SQL_QUERY = "sql.query"
    HTTP_GET = "http.get"
    PLAN_NOTE = "plan.note"
    MILVUS_LIST_COLLECTIONS = "milvus.list_collections"
    GITHUB_REQUEST = "github.request"
    MILVUS_DESCRIBE_INDEX = "milvus.describe_index"
    GOOGLE_SEARCH = "google.search"
    SQL_GET_SCHEMA = "sql.get_schema"
    SQL_LIST_TABLES = "sql.list_tables"
    SQL_DESCRIBE_TABLE = "sql.describe_table"
    SQL_GET_TABLE_INFO = "sql.get_table_info"
    SQL_SEARCH_IN_TABLE = "sql.search_in_table"
    SQL_GET_DISTINCT_VALUES = "sql.get_distinct_values"
    SQL_GET_TABLE_STATS = "sql.get_table_stats"
    SQL_FIND_RELATED_TABLES = "sql.find_related_tables"
    SQL_CUSTOM_QUERY = "sql.custom_query"

class Step(BaseModel):
    """Represents a single step in the execution plan."""
    # Core fields
    title: str
    action: Action
    input: Dict[str, Any]
    expect: Dict[str, Any]
    
    # Optional fields with defaults
    timeout_s: int = 60
    max_retries: int = 2
    retries_left: int = Field(default=2, exclude=True)
    
    # Additional fields that LLM might provide
    id: Optional[str] = None
    description: Optional[str] = None
    reason: Optional[str] = None
    tool: Optional[str] = None
    success_criteria: Optional[str] = None
    depends_on: Optional[List[str]] = Field(default_factory=list)

class Evidence(BaseModel):
    """Represents the summarized output of a step."""
    step_title: str
    source_action: Action
    preview: str
    metrics: Dict[str, Any]

class Task(BaseModel):
    intent_summary: str
    constraints: List[str] = Field(default_factory=list)
    acceptance: Dict[str, Any]
    missing_info: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    priority: str
    risk_flags: List[str] = Field(default_factory=list)
    tool_inventory_ack: List[str] = Field(default_factory=list)

class Observation(BaseModel):
    step_id: str
    tool: str
    attempt: int
    ok: bool
    data: Dict[str, Any]
    error: Optional[Dict[str, Any]] = None
    metrics: Dict[str, Any]
    safety: Dict[str, Any]

class ProgressSummary(BaseModel):
    # Define fields based on how it will be used in Reflection
    pass # Placeholder for now

class FailureContext(BaseModel):
    # Define fields based on how it will be used in Replan/Repair
    pass # Placeholder for now

class Limits(BaseModel):
    max_steps: int
    max_retries_per_step: int
    time_budget_hint: str

class ExecutionContext(BaseModel):
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    timeout: Optional[int] = None
    pii_policy: Optional[str] = None

class Plan(BaseModel):
    rationale: str
    steps: List[Step]
    plan_score: Dict[str, Any]
    risks: List[str] = Field(default_factory=list)
    missing_tools: List[str] = Field(default_factory=list)
    alternatives: List[Dict[str, Any]] = Field(default_factory=list)

class AgentState(BaseModel):
    """Represents the full state of the agent's execution graph."""
    question: str
    plan: Optional[Plan] = None
    step_idx: int = 0
    evidence: List[Evidence] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    visited_signatures: Set[str] = Field(default_factory=set)
    final_answer: Optional[str] = None
    last_result: Optional[Any] = None
    history: List[Dict[str, Any]] = Field(default_factory=list)
    chat_history: List[Dict[str, str]] = Field(default_factory=list)  # [{'role': 'user'|'assistant', 'content': str}]
    
    # Optional context
    context: Optional[Dict[str, Any]] = None
    profile: Dict[str, Any] = Field(default_factory=dict)
    tool_policies: Optional[Dict[str, Any]] = None
    run_id: Optional[str] = None

    # Fields for routing
    intent: str = "complex_query" # Default to complex query

    # Dynamic catalog of the database schema
    catalog: Optional[str] = None
    db_introspection_result: Optional[str] = None

    # New fields for Plan-Act-Reflect
    task: Optional[Task] = None
    last_observation: Optional[Observation] = None
    progress_summary: Optional[ProgressSummary] = None
    failure_context: Optional[FailureContext] = None
    observations: List[Observation] = Field(default_factory=list)
    tool_inventory: List[str] = Field(default_factory=list)
    limits: Optional[Limits] = None
    execution_context: Optional[ExecutionContext] = None
    reflection_status: Optional[str] = None
    all_criteria_met: Optional[bool] = None
    has_more_steps: Optional[bool] = None
    can_replan_repair: Optional[bool] = None
    
    # Memory fields
    memory_id: Optional[str] = None
    similar_memories: List[Dict[str, Any]] = Field(default_factory=list)
    memory_context: Optional[str] = None
