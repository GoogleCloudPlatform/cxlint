import json
import logging
import os

from configparser import ConfigParser
from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple

from common import Common, LintStats
from rules import RulesDefinitions
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
    display_name: str = None # Flow Display Name
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

class Flows:
    """Flow linter methods and functions."""
    def __init__(
        self,
        verbose: bool,
        config: ConfigParser,
        console):
        self.verbose = verbose
        self.console = console
        self.config = config
        self.agent_type = Common.load_agent_type(config)
        self.disable_map = Common.load_message_controls(config)
        self.agent_id = Common.load_agent_id(config)
        self.rules = RulesDefinitions(self.console)
        self.include_filter = self.load_include_filter(config)
        self.exclude_filter = self.load_exclude_filter(config)
        self.route_parameters = {}
        self.special_pages = [
            'End Session', 'End Flow', 'Start Page', 'Current Page',
            'Previous Page'
        ]

    @staticmethod
    def load_include_filter(config: ConfigParser) -> str:
        """Loads the include pattern for Flow display names."""
        pattern = config['FLOWS']['include']

        return pattern

    @staticmethod
    def load_exclude_filter(config: ConfigParser) -> str:
        """Loads the exclude pattern for Flow display names."""
        pattern = config['FLOWS']['exclude']

        if pattern == '':
            pattern = None

        return pattern

    @staticmethod
    def build_flow_path_list(agent_local_path: str):
        """Builds a list of dirs, each representing a Flow directory.

        Ex: /path/to/agent/flows/<flow_dir>

        This dir path can then be used to find the next level of information
        in the directory by appending the appropriate next dir structures like:
        - <flow_name>.json, for the Flow object
        - /transitionRouteGroups, for the Route Groups dir
        - /pages, for the Pages dir
        """
        root_dir = agent_local_path + '/flows'

        flow_paths = []

        for flow_dir in os.listdir(root_dir):
            flow_dir_path = f'{root_dir}/{flow_dir}'
            flow_paths.append(flow_dir_path)

        return flow_paths

    @staticmethod
    def build_page_path_list(flow_path: str):
        """Builds a list of files, each representing a Page.

        Ex: /path/to/agent/flows/<flow_dir>/pages/<page_name>.json
        """
        pages_path = f'{flow_path}/pages'

        page_paths = []

        for page in os.listdir(pages_path):
            page_file_path = f'{pages_path}/{page}'
            page_paths.append(page_file_path)

        return page_paths

    @staticmethod
    def check_for_webhook(page: Page, path: Dict[str, Any]):
        """Check the current route for existence of webhook."""
        if 'webhook' in path:
            page.has_webhook = True

    @staticmethod
    def check_for_webhook_event_handlers(route: Fulfillment):
        """Check for Webhook Error Event Handler on Page.
        
        In this method, we're interested in the following conditions:
         - Page is currently flagged w/webhook = True
         - Page HAS NOT been flagged w/having a webhook error handler
         - The trigger MATCHES the pattern 'webhook.error'
         
        If a Page and its Route meet all the criteria, we'll flip the bit.
        Otherwise, the webhook handler bit will remain False, causing a rule
        flag."""

        if all(
            [route.page.has_webhook,
            not route.page.has_webhook_event_handler,
            'webhook.error' in route.trigger]):
            
            route.page.has_webhook_event_handler = True

    @staticmethod
    def clean_page_display_name(display_name: str):
        """Replace characters from map for the given page name."""
        patterns = {
            "%28": "(",
            "%29": ")",
            "%23": "#",
            "%2f": "/",
            "%3f": "?"
            }

        for pattern in patterns:
            if pattern in display_name:
                display_name = display_name.replace(pattern, patterns[pattern])

        return display_name
    
    @staticmethod
    def find_orphaned_pages(flow: Flow):
        """Find Orphaned Pages in the graph.
        
        An Orphaned Page is defined as:
          - A Page which has no incoming edge when traversed from Start Page.
            That is, it is unreachable in the graph by any practical means.
          - A Page which is connected to a root orphaned page. That is, a page
            that could have both incoming or outgoing routes, but due to its
            connectedness to the root orphan page, is unreachable in the graph.

        Here we will compute the symmetric difference of 2 sets:
          - Active Pages (i.e. Pages that were reachable in the graph)
          - Used Pages (i.e. Pages that were used by some Route)

        If an Orphaned Page has children that it routes to, those children will
        appear in Used Pages, although they will ultimately be unreachable.
        It's possible for an Orphaned Page to route back to an Active Page in
        the graph. For these instances, we don't want to count those pages as
        orphaned, because they are reachable via other sections of the graph.
        """
        filtered_set = flow.active_pages.symmetric_difference(flow.graph._used_nodes)
        flow.orphaned_pages.update(filtered_set)

        return flow

    def find_unused_pages(self, flow: Flow):
        """Find Unused Pages in the graph.
        
        An Unused Page is defined as:
          - A Page which has no incoming or outgoing edge AND
          - A Page which exists in the Agent design time, but which is not
            present anywhere in the graph, either visible or non-visible.

        Here we will compute the difference of 2 sets:
          - All Pages (i.e. Pages that exist in the Agent Design Time)
          - Used Pages (i.e. Pages that were used by some Route)

        The resulting set will consist of 2 types of Pages:
          - Truly Unused Pages
          - Orphaned Root Pages

        Orphaned Root Pages end up in the results due to the fact that no other
        Active Page is pointing to them. We remove these from the resulting set
        before presenting the Truly Unused Pages.
        """

        # Discard special pages as they are non-relevant for final outcome
        for page in self.special_pages:
            flow.all_pages.discard(page)

        prelim_unused = flow.all_pages.difference(flow.graph._used_nodes)

        # Filter out Orphaned Root Pages
        filtered_set = set()

        for page in prelim_unused:
            if page not in flow.graph._edges:
                filtered_set.add(page)
            else:
                flow.orphaned_pages.add(page)

        flow.unused_pages = filtered_set

        return flow
    
    def recurse_edges(
            self,
            edges: List,
            page: Page,
            dangling: set,
            visited: set):
        """Recursive method searching graph edges for Active / Dangling Pages.

        A byproduct of searching for Dangling Pages in the graph is that we can
        produce a set of Active Pages in the graph. These are pages that are
        reachable when traversing from the Start Page. These can then be used
        to determine Orphaned Pages in another method.
        """
        if page in edges:
            for inner_page in edges[page]:
                if inner_page not in visited:
                    visited.add(inner_page)
                    dangling, visited = self.recurse_edges(
                        edges, inner_page, dangling, visited)
                    
        else:
            dangling.add(page)

        return dangling, visited
    
    def find_dangling_pages(self, flow: Flow):
        """Find Dangling Pages in the graph.
        
        A Dangling Page is defined as:
          - Any page that exists in the graph that has no outgoing edge
          
        These pages can result in a conversational "dead end" which is
        potentially unrecoverable.
        """

        flow.dangling_pages, flow.active_pages = self.recurse_edges(
            flow.graph._edges,
            'Start Page',
            flow.dangling_pages,
            flow.active_pages
        )

        # Clean up Special Pages       
        for page in self.special_pages:
            flow.dangling_pages.discard(page)

        filtered_set = set()
        # Clean up any Flow Transitions
        for page in flow.dangling_pages:
            if 'FLOW' not in page:
                filtered_set.add(page)

        flow.dangling_pages = filtered_set

        return flow
    
    def check_flow_filters(self, flow: Flow):
        """Determines if the Flow should be filtered for linting."""
        if self.include_filter:
            if flow.display_name in self.include_filter:
                flow.filtered = False

            else:
                flow.filtered = True

        if self.exclude_filter:
            if flow.display_name in self.exclude_filter:
                flow.filtered = True

        return flow

    def set_route_targets(self, route: Fulfillment):
        """Determine the Route Targets for the specified route.
        
        This method is what will primary build out the graph structure for the
        Flow based on the current page and where the routes are pointing to.
        The graph structure can then be traversed later to determine any errors
        or inconsistencies in design.
        """
        current_page = route.page.display_name

        route.target_flow = route.data.get('targetFlow', None)
        route.target_page = route.data.get('targetPage', None)

        if route.target_page:
            route.page.flow.graph.add_edge(current_page, route.target_page)
            route.page.flow.graph.add_used_node(route.target_page)

        if route.target_flow:
            route.page.flow.graph.add_edge(current_page, f'FLOW: {route.target_flow}')
            route.page.flow.graph.add_used_node(f'FLOW: {route.target_flow}')

        return route 


    def update_route_parameters(self, route: Fulfillment, item: Dict[str,str]):
        """Update the Route Parameters map based on new info."""
        flow_name = route.page.flow.display_name
        page_name = route.page.display_name

        flow_data = self.route_parameters.get(flow_name, None)
        page_data = None

        if flow_data:
            page_data = flow_data.get(page_name, None)

        # Flow and Page already exists, append to existing list.
        if page_data:
            self.route_parameters[flow_name][page_name].append(item)

        # Flow data exists, but not Page, so only create the Page list.
        elif flow_data and not page_data:
            self.route_parameters[flow_name][page_name] = [item]

        # Neither the Flow or Page data exists, so create it all.
        else:
            self.route_parameters[flow_name] = {page_name: [item]}


    def collect_transition_route_trigger(self, route):
        """Inspect route and return all Intent/Condition info."""

        trigger = []
        intent_name = None

        if 'intent' in route.data:
            trigger.append('intent')
            intent_name = route.data.get("intent", None)

        if 'condition' in route.data:
            trigger.append('condition')
    
        if len(trigger) > 0:
            trigger = '+'.join(trigger)
        
        if self.verbose and intent_name:
            return f'{trigger} : {intent_name}'

        else:
            return trigger

    def get_trigger_info(self, route):
        """Extract trigger info from route based on primary key."""

        if route.fulfillment_type == 'event':
            trigger = f'event : {route.data.get("event", None)}'

        if route.fulfillment_type == 'transition_route':
            intent_condition = self.collect_transition_route_trigger(route)
            trigger = f'route : {intent_condition}'

        return trigger

    def lint_agent_responses(self, route: Fulfillment, stats: LintStats) -> str:
        """Executes all Text-based Fulfillment linter rules."""
        voice = False
        route.verbose = self.verbose

        if self.agent_type == 'voice':
            voice = True

        # closed-choice-alternative
        if self.disable_map.get('closed-choice-alternative', True) and voice:
            stats = self.rules.closed_choice_alternative_parser(route, stats)

        # wh-questions
        if self.disable_map.get('wh-questions', True) and voice:
            stats = self.rules.wh_questions(route, stats)

        # clarifying-questions
        if self.disable_map.get('clarifying-questions', True) and voice:
            stats = self.rules.clarifying_questions(route, stats)

        return stats

    def lint_fulfillment_type(
        self,
        stats: LintStats,
        route: Fulfillment,
        path: object,
        key: str):
        """Parse through specific fulfillment types and lint."""
        fulfillment_data = path.get(key, None)

        if fulfillment_data:
            for item in fulfillment_data:
                # This is where each message type will exist
                # text, custom payload, etc.

                # TODO pmarlow: create sub-method parsers per type
                if 'text' in item:
                    for text in item['text']['text']:
                        stats.total_inspected += 1
                        route.text = text

                        stats = self.lint_agent_responses(route, stats)

                if 'parameter' in item:
                    self.update_route_parameters(route, item)


        return stats


    def lint_events(
        self,
        page: Page,
        stats: LintStats):
        """Parse through all Page Event Handlers and lint."""
        if not page.events:
            return stats

        for route_data in page.events:
            route = Fulfillment(page=page)
            route.data = route_data
            route.agent_id = page.agent_id
            route.fulfillment_type = 'event'
            route.trigger = self.get_trigger_info(route)
            route = self.set_route_targets(route)
            path = route.data.get('triggerFulfillment', None)
            event = route.data.get('event', None)

            if not path and not event:
                continue

            # Flag for Webhook Handler
            self.check_for_webhook_event_handlers(route)

            stats = self.lint_fulfillment_type(stats, route, path, 'messages')

        return stats

    def lint_routes(
        self,
        page: Page,
        stats: LintStats):
        """Parse through all Transition Routes and lint."""
        tf_key = 'triggerFulfillment'

        if not page.routes:
            return stats

        for route_data in page.routes:
            route = Fulfillment(page=page)
            route.data = route_data
            route.agent_id = page.agent_id
            route.fulfillment_type = 'transition_route'
            route.trigger = self.get_trigger_info(route)
            route = self.set_route_targets(route)

            path = route.data.get(tf_key, None)

            if not path:
                continue

            # Flag for Webhook Handler
            self.check_for_webhook(page, path)

            stats = self.lint_fulfillment_type(stats, route, path, 'messages')

            # Preset Params can be linted here
            stats = self.lint_fulfillment_type(stats, route, path, 'setParameterActions')

        return stats

    def lint_entry(self, page: Page, stats: LintStats):
        """Lint Entry Fulfillment on a single page file.
        
        The Entry Fulfillment to a Page only has 1 "route" (i.e. itself) so
        there is no need to loop through multiple routes, as they don't
        exist for Entry Fulfillment.
        """
        tf_key = 'triggerFulfillment'

        if not page.entry:
            return stats

        route = Fulfillment(page=page)
        route.data = page.entry
        route.agent_id = page.agent_id
        route.fulfillment_type = 'entry'
        route.trigger = 'entry'
        path = route.data

        self.check_for_webhook(page, path)

        stats = self.lint_fulfillment_type(stats, route, path, 'messages')

        return stats

    def lint_webhooks(self, page: Page, stats: LintStats):
        """Lint a Page with Webhook setup best practice rules."""

        # missing-webhook-event-handlers
        if self.disable_map.get('missing-webhook-event-handlers', True):
            stats = self.rules.missing_webhook_event_handlers(page, stats)

        return stats
        

    def lint_page(self, page: Page, stats: LintStats):
        """Lint a Single Page file."""
        page.display_name = Common.parse_filepath(page.page_file, 'page')
        page.display_name = self.clean_page_display_name(page.display_name)

        page.flow.graph.add_node(page.display_name)

        # TODO
        # Page Display Name from Filename contains special characters so it will
        # not match against page display names stored inside the proto objects
        # Need to implement a parser for symbol translation.
        page.flow.all_pages.add(page.display_name)

        with open(page.page_file, 'r', encoding='UTF-8') as page_file:
            page.data = json.load(page_file)
            page.verbose = self.verbose
            page.entry = page.data.get('entryFulfillment', None)
            page.events = page.data.get('eventHandlers', None)
            page.routes = page.data.get('transitionRoutes', None)

            page.resource_id = page.data.get('name', None)
            page.flow.data[page.display_name] = page.resource_id

            # Order of linting is important here
            stats = self.lint_entry(page, stats)
            stats = self.lint_routes(page, stats)
            stats = self.lint_events(page, stats)
            stats = self.lint_webhooks(page, stats)


            page_file.close()

        return stats

    def lint_start_page(
        self,
        flow: Flow,
        stats: LintStats):
        """Process a single Flow Path file."""
        with open(flow.start_page_file, 'r', encoding='UTF-8') as flow_file:
            page = Page(flow=flow)
            page.display_name = 'Start Page'

            flow.graph.add_node(page.display_name)

            page.data = json.load(flow_file)
            page.events = page.data.get('eventHandlers', None)
            page.routes = page.data.get('transitionRoutes', None)
            page.verbose = self.verbose

            flow.resource_id = page.data.get('name', None)
            page.agent_id = flow.agent_id
            page.resource_id = 'START_PAGE'
            flow.data[page.display_name] = page.resource_id

            # Order of linting is important
            stats = self.lint_routes(page, stats)
            stats = self.lint_events(page, stats)
            stats = self.lint_webhooks(page, stats)

            flow_file.close()


        return stats
    
    def lint_graph(self, flow:Flow, stats: LintStats):
        """Lint the graph structure for the specified Flow.
        
        In this method we are taking the completed Flow Graph that was built
        for this specific Flow and checking for any design inconsistencies.
        These include things like Unused, Dangling, and Orphaned pages.
        """

        # unused-pages
        if self.disable_map.get('unused-pages', True):
            stats = self.rules.unused_pages(flow, stats)

        # dangling-pages
        if self.disable_map.get('dangling-pages', True):
            stats = self.rules.dangling_pages(flow, stats)

        # orphaned-pages
        if self.disable_map.get('orphaned-pages', True):
            stats = self.rules.orphaned_pages(flow, stats)

        return stats


    def lint_flow(self, flow: Flow, stats: LintStats):
        """Lint a Single Flow dir and all subdirectories."""
        flow.display_name = Common.parse_filepath(flow.dir_path, 'flow')
        flow = self.check_flow_filters(flow)

        if not flow.filtered:
            message = f'{"*" * 15} Flow: {flow.display_name}'
            self.console.log(message)

            flow.start_page_file = f'{flow.dir_path}/{flow.display_name}.json'

            stats = self.lint_start_page(flow, stats)
            stats = self.lint_pages_directory(flow, stats)

            # Order of Find Operations is important here!
            flow = self.find_unused_pages(flow)
            flow = self.find_dangling_pages(flow)
            flow = self.find_orphaned_pages(flow)

            stats = self.lint_graph(flow, stats)

        return stats

    def lint_flows_directory(self, agent_local_path: str):
        """Linting the top level Flows dir in the JSON Package structure.

        The following files/dirs exist under the `flows` dir:
        - Flow object (i.e. Flow START_PAGE)
        - transitionRouteGroups
        - pages

        In Dialogflow CX, the START_PAGE of each Flow is a special kind of Page
        that exists within the Flow object itself. In this method, we will lint
        the Flow object, all files in the transitionRouteGroups dir and all
        files in the pages dir.
        """
        start_message = f'{"#" * 10} Begin Flows Directory Linter'
        self.console.log(start_message)

        stats = LintStats()

        # Create a list of all Flow paths to iter through
        flow_paths = self.build_flow_path_list(agent_local_path)
        stats.total_flows = len(flow_paths)

        # linting happens here
        for flow_path in flow_paths:
            flow = Flow()
            flow.graph = Graph()
            flow.verbose = self.verbose
            flow.agent_id = self.agent_id
            flow.dir_path = flow_path
            stats = self.lint_flow(flow, stats)

        header = "-" * 20
        rating = Common.calculate_rating(
            stats.total_issues, stats.total_inspected)

        end_message = f'\n{header}\n{stats.total_flows} Flows linted.'\
            f'\n{stats.total_issues} issues found out of '\
            f'{stats.total_inspected} inspected.'\
            f'\nYour Agent Flows rated at {rating:.2f}/10\n\n'
        self.console.log(end_message)

    def lint_pages_directory(self, flow: Flow, stats: LintStats):
        """Linting the Pages dir inside a specific Flow dir.
        
        Some Flows may not contain Pages, so we check for the existence
        of the directory before traversing
        """
        if 'pages' in os.listdir(flow.dir_path):
            page_paths = self.build_page_path_list(flow.dir_path)

            for page_path in page_paths:
                page = Page(flow=flow)
                page.agent_id = flow.agent_id
                page.page_file = page_path
                stats.total_pages += 1
                stats = self.lint_page(page, stats)

        return stats
