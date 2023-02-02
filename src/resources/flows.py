import json
import logging
import os

from configparser import ConfigParser
from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple

from common import Common, LintStats
from rules import RulesDefinitions

# logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

@dataclass
class Flow:
    """"Used to track current Flow Attributes."""
    agent_id: str = None
    data: Dict[str, Any] = None
    dir_path: str = None # Full Directory Path for this Flow
    display_name: str = None # Flow Display Name
    resource_id: str = None
    resource_type: str = 'flow'
    start_page_file: str = None # File Path Location of START_PAGE

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

@dataclass
class Fulfillment:
    """Used to track current Fulfillment Attributes."""
    agent_id: str = None
    data: Dict[str, Any] = None
    display_name: str = None # Inherit from Page easy logging
    fulfillment_type: str = None # transition_route | event
    page: Page = None
    text: str = None
    trigger: str = None
    resource_type: str = 'fulfillment'
    verbose: bool = False

class Flows:
    """Flow linter methods and functions."""
    def __init__(
        self,
        verbose: bool,
        config: ConfigParser):
        self.verbose = verbose
        self.config = config
        self.agent_type = Common.load_agent_type(config)
        self.disable_map = Common.load_message_controls(config)
        self.agent_id = Common.load_agent_id(config)
        self.rules = RulesDefinitions()
        self.route_parameters = {}

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
                    # self.route_parameters[route.page.flow.display_name] = {route.page.display_name: [item]}


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
        """Lint Entry Fulfillment on a single page file."""
        tf_key = 'triggerFulfillment'

        if not page.entry:
            return stats

        # The Entry Fulfillment to a Page only has 1 "route" (i.e. itself)
        # so there is no need to loop through multiple routes, as they don't
        # exist for Entry Fulfillment.

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

        with open(page.page_file, 'r', encoding='UTF-8') as page_file:
            page.data = json.load(page_file)
            page.verbose = self.verbose
            page.entry = page.data.get('entryFulfillment', None)
            page.events = page.data.get('eventHandlers', None)
            page.routes = page.data.get('transitionRoutes', None)

            page.resource_id = page.data.get('name', None)

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
            page.display_name = 'START_PAGE'

            page.data = json.load(flow_file)
            page.events = page.data.get('eventHandlers', None)
            page.routes = page.data.get('transitionRoutes', None)
            page.verbose = self.verbose

            flow.resource_id = page.data.get('name', None)
            page.agent_id = flow.agent_id
            page.resource_id = 'START_PAGE'

            # Order of linting is important
            stats = self.lint_routes(page, stats)
            stats = self.lint_events(page, stats)
            stats = self.lint_webhooks(page, stats)

            flow_file.close()


        return stats

    def lint_flow(self, flow: Flow, stats: LintStats):
        """Lint a Single Flow dir and all subdirectories."""
        
        flow.display_name = Common.parse_filepath(flow.dir_path, 'flow')

        message = f'{"*" * 15} Flow: {flow.display_name}'
        logging.info(message)

        flow.start_page_file = f'{flow.dir_path}/{flow.display_name}.json'

        stats = self.lint_start_page(flow, stats)
        stats = self.lint_pages_directory(flow, stats)

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
        logging.info(start_message)

        stats = LintStats()

        # Create a list of all Flow paths to iter through
        flow_paths = self.build_flow_path_list(agent_local_path)
        stats.total_flows = len(flow_paths)

        # linting happens here
        for flow_path in flow_paths:
            flow = Flow()
            flow.agent_id = self.agent_id
            flow.dir_path = flow_path
            stats = self.lint_flow(flow, stats)

        header = "-" * 20
        rating = Common.calculate_rating(
            stats.total_issues, stats.total_inspected)

        end_message = f'\n{header}\n{stats.total_flows} Flows linted.'\
            f'\n{stats.total_issues} issues found out of '\
            f'{stats.total_inspected} fulfillments inspected.'\
            f'\nYour Agent Flows rated at {rating:.2f}/10\n\n'
        logging.info(end_message)

    def lint_pages_directory(self, flow: Flow, stats: LintStats):
        """Linting the Pages dir inside a specific Flow dir."""
        # start_message = f'{"*" * 10} Begin Page Linter'
        # logging.info(start_message)

        # Some Flows may not contain Pages, so we check for the existence
        # of the directory before traversing
        if 'pages' in os.listdir(flow.dir_path):
            page_paths = self.build_page_path_list(flow.dir_path)

            for page_path in page_paths:
                page = Page(flow=flow)
                page.agent_id = flow.agent_id
                page.page_file = page_path
                stats.total_pages += 1
                stats = self.lint_page(page, stats)

        return stats
