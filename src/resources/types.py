"""Collection of Type Classes used for CX Linter."""
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field

from graph import Graph

@dataclass
class Flow:
    """"Used to track current Flow Attributes."""
    agent_id: str = None
    all_pages: set = field(default_factory=set)
    active_pages: set = field(default_factory=set)
    data: Dict[str, Any] = field(default_factory=dict)
    dangling_pages: set = field(default_factory=set)
    dir_path: str = None # Full Directory Path for this Flow
    display_name: str = None # Cleaned Flow Display Name (removed special chars)
    file_name: str = None # Original File Name of the Flow file (includes special chars)
    filtered: bool = False
    graph: Graph = None
    orphaned_pages: set = field(default_factory=set)
    resource_id: str = None
    resource_type: str = 'flow'
    start_page_file: str = None # File Path Location of START_PAGE
    unused_pages: set = field(default_factory=set)
    verbose: bool = False

@dataclass
class Page:
    """Used to track current Page Attributes."""
    agent_id: str = None
    data: Dict[str, Any] = None
    display_name: str = None
    entry: Dict[str, Any] = None
    events: List[object] = None
    flow: Flow = None
    has_webhook: bool = False
    has_webhook_event_handler: bool = False
    page_file: str = None
    resource_id: str = None
    resource_type: str = 'page'
    routes: List[object] = None
    verbose: bool = False

@dataclass
class Fulfillment:
    """Used to track current Fulfillment Attributes."""
    agent_id: str = None
    data: Dict[str, Any] = None
    display_name: str = None # Inherit from Page easy logging
    fulfillment_type: str = None # transition_route | event
    page: Page = None
    target_flow: str = None
    target_page: str = None
    text: str = None
    trigger: str = None
    resource_type: str = 'fulfillment'
    verbose: bool = False

@dataclass
class Intent:
    """Used to track current Intent Attributes."""
    agent_id: str = None
    data: Dict[str, Any] = None
    description: str = None
    display_name: str = None
    dir_path: str = None
    filtered: bool = False
    labels: Dict[str, str] = None
    metadata_file: str = None
    resource_id: str = None
    resource_type: str = 'intent'
    training_phrases: Dict[str, Any] = field(default_factory=dict)
    verbose: bool = False

@dataclass
class EntityType:
    """"Used to track current Flow Attributes."""
    agent_id: str = None
    data: Dict[str, Any] = None
    dir_path: str = None # Full Directory Path for this Entity Type
    display_name: str = None # Entity Type Display Name
    entities: Dict[str, Any] = field(default_factory=dict) # Map of lang codes, entities, and values
    kind: str = None # The kind of Entity Type represented
    resource_id: str = None
    resource_type: str = 'entity_type'
    verbose: bool = False

@dataclass
class TestCase:
    """Used to track current Test Case Attributes."""
    associated_intent_data: Dict[str, Any] = None
    agent_id: str = None
    agent_path: str = None
    conversation_turns: List[Any] = None
    data: Dict[str, Any] = None
    display_name: str = None
    has_invalid_intent: bool = False
    intent_data: List[str] = None
    qualified: bool = False
    resource_id: str = None
    resource_type: str = 'test_case'
    tags: List[str] = None
    test_config: Dict[str, Any] = None
    verbose: bool = False

@dataclass
class Resource:
    """Generic class to store basic Resource data.
    
    Since each core class has such varied parameters, this generic class will
    help to standardize the data fed to the generic logger and the maps used
    therein.
    """
    agent_id: str = None
    entity_type_display_name: str = None
    entity_type_id: str = None
    flow_display_name: str = None
    flow_id: str = None
    intent_display_name: str = None
    intent_id: str = None
    page_display_name: str = None
    page_id: str = None
    resource_type: str = None
    test_case_display_name: str = None
    test_case_id: str = None
    webhook_display_name: str = None
    webhook_id: str = None

@dataclass
class LintStats:
    """Used to track linter stats for each section processed."""
    total_issues: int = 0
    total_inspected: int = 0
    total_flows: int = 0
    total_pages: int = 0
    total_intents: int = 0
    total_training_phrases: int = 0
    total_entity_types: int = 0
    total_route_groups: int = 0
    total_test_cases: int = 0
    total_webhooks: int = 0