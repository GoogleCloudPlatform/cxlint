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
    display_name: str = None # Flow Display Name
    start_page_file: str = None # File Path Location of START_PAGE
    dir_path: str = None # Full Directory Path for this Flow
    data: Dict[str, Any] = None

@dataclass
class Page:
    """Used to track current Page Attributes."""
    flow: Flow = None
    display_name: str = None
    page_file: str = None
    data: Dict[str, Any] = None
    events: List[object] = None
    routes: List[object] = None

@dataclass
class Fulfillment:
    """Used to track current Fulfillment Attributes."""
    page: Page = None
    trigger: str = None
    text: str = None
    resource: str = None
    verbose: bool = False

class Flows:
    """Flow linter methods and functions."""
    def __init__(
        self,
        verbose: bool,
        config: ConfigParser):
        self.verbose = verbose
        self.config = config
        self.disable_map = Common.load_message_controls(config)
        self.rules = RulesDefinitions()

        # self.disable_map = self.load_message_controls()
        # self.test_case_tag_filter = self.load_test_case_tag_filter()
        # self.intent_map_for_tcs = None

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
        flows_path = agent_local_path + '/flows'

        flow_paths = []

        for flow_dir in os.listdir(flows_path):
            flow_dir_path = f'{flows_path}/{flow_dir}'
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

    def collect_transition_route_trigger(self, route):
        """Inspect route and return all Intent/Condition info."""
        # TODO: Clean up refactor elif logic

        if 'intent' in route and 'condition' in route:
            trigger = 'intent+condition'

        elif 'intent' in route:
            if self.verbose:
                trigger = f'intent:{route["intent"]}'
            else:
                trigger = 'intent'

        elif 'condition' in route:
            if self.verbose:
                trigger = f'condition:{route["condition"]}'
            else:
                trigger = 'condition'

        return trigger

    def get_trigger_info(self, resource, primary_key):
        """Extract trigger info from route based on primary key."""

        if primary_key == 'eventHandlers':
            trigger = f'event:{resource["event"]}'

        if primary_key == 'transitionRoutes':
            intent_condition = self.collect_transition_route_trigger(resource)
            trigger = f'route:{intent_condition}'

        return trigger

    def lint_agent_responses(self, route: Fulfillment, stats: LintStats) -> str:
        """Executes all Text-based Fulfillment linter rules."""

        route.verbose = self.verbose

        # closed-choice-alternative
        if self.disable_map.get('closed-choice-alternative', True):
            stats = self.rules.closed_choice_alternative_parser(route, stats)

        # wh-questions
        if self.disable_map.get('wh-questions', True):
            stats = self.rules.wh_questions(route, stats)

        # clarifying-questions
        if self.disable_map.get('clarifying-questions', True):
            stats = self.rules.clarifying_questions(route, stats)

        return stats

    def lint_fulfillment_type(
        self,
        stats: LintStats,
        route: Fulfillment,
        path: object,
        ftype: str):
        """Parse through specific fulfillment types and lint."""
        if ftype in path:
            for item in path[ftype]:
                if 'text' in item:
                    for text in item['text']['text']:
                        stats.total_inspected += 1
                        route.text = text

                        stats = self.lint_agent_responses(route, stats)

        return stats


    def lint_events(
        self,
        page: Page,
        stats: LintStats):
        """Parse through all Page Event Handlers and lint."""
        tf_key = 'triggerFulfillment'

        if not page.events:
            return stats

        for route_data in page.events:
            route = Fulfillment(page=page)
            route.trigger = self.get_trigger_info(route_data, 'eventHandlers')
            path = route_data.get(tf_key, None)

            if not path:
                continue

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
            route.trigger = self.get_trigger_info(route_data, 'transitionRoutes')
            path = route_data.get(tf_key, None)

            if not path:
                continue

            stats = self.lint_fulfillment_type(stats, route, path, 'messages')

        return stats

    def lint_page(self, page: Page, stats: LintStats):
        """Lint a Single Page file."""
        page.display_name = Common.parse_filepath(page.page_file, 'page')

        with open(page.page_file, 'r', encoding='UTF-8') as page_file:
            page.data = json.load(page_file)
            page.events = page.data.get('eventHandlers', None)
            page.routes = page.data.get('transitionRoutes', None)

            stats = self.lint_events(page, stats)
            stats = self.lint_routes(page, stats)

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

            stats = self.lint_events(page, stats)
            stats = self.lint_routes(page, stats)

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
        start_message = f'{"#" * 10} Begin Flow Directory Linter'
        logging.info(start_message)

        stats = LintStats()

        # Create a list of all Flow paths to iter through
        flow_paths = self.build_flow_path_list(agent_local_path)
        stats.total_flows = len(flow_paths)

        # linting happens here
        for flow_path in flow_paths:
            flow = Flow()
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
                page.page_file = page_path
                stats.total_pages += 1
                stats = self.lint_page(page, stats)

        return stats
