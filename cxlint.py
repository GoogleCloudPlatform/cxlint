"""Core class and methods for CX Linter."""

import os
import json
import logging
import re

from dataclasses import dataclass

from rules import RulesDefinitions # pylint: disable=E0401
from file_traversal import FileTraversal # pylint: disable=E0401

# logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

@dataclass
class LintStats: # pylint: disable=R0903
    """Used to track linter stats for each section processed."""
    def __init__(self):
        self.total_issues = 0
        self.total_inspected = 0
        self.total_flows = 0
        self.total_pages = 0

@dataclass
class Fulfillment:
    """Used to track current Fulfillment Attributes."""
    def __init__(self):
        self.trigger = None
        self.text = None
        self.resource = None
        self.verbose = None
class CxLint:
    """Core CX Linter methods and functions."""
    def __init__(
        self,
        verbose: bool = False):

        self.rules = RulesDefinitions()
        self.traverse = FileTraversal()

        self.verbose = verbose
        self.current_filepath = None
        self.current_flow = None
        self.current_page = None
        self.current_resource = None

    @staticmethod
    def update_stats(
        local_issues: int,
        local_inspected: int,
        stats: LintStats) -> LintStats:
        """Update the current LintStats object."""
        stats.total_issues += local_issues
        stats.total_inspected += local_inspected

        return stats

    @staticmethod
    def parse_filepath(in_path: str, resource_type: str) -> str:
        """Parse file path to provide quick reference for linter log."""

        regex_map = {
            'flow': r'.*\/flows\/([^\/]*)',
            'page': r'.*\/pages\/([^\/]*)\.'
        }
        resource_name = re.match(regex_map[resource_type], in_path).groups()[0]
        # resource_name = in_path.split('/')[-1]

        return resource_name

    def collect_transition_route_trigger(self, route):
        """Inspect route and return all Intent/Condition info."""

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


    def fulfillment_linter(self, trigger, text: str) -> str:
        """Executes all Text-based Fulfillment linter rules."""

        resource = self.current_resource
        verbose = self.verbose
        total_issues = 0

        # Closed-Choice Alternative
        total_issues += self.rules.closed_choice_alternative_parser(
            resource, trigger, text, verbose)

        # Wh- Questions
        total_issues += self.rules.wh_questions(
            resource, trigger, text, verbose)

        return total_issues

    def lint_fulfillments(self, stats, resource, primary_key: str):
        """Parse through Fulfillments structure and lint."""
        t2_key = 'triggerFulfillment'
        msg_key = 'messages'
        wh_key = 'webhook'
        param_key = 'setParameterActions'

        total_issues = 0
        total_inspected = 0

        routes = resource.get(primary_key, None)

        if routes:
            for route in routes:
                trigger = self.get_trigger_info(route, primary_key)
                path = route.get(t2_key, None)
                
                # check Messages
                if path and msg_key in path:
                    
                    for item in path[msg_key]:
                        if 'text' in item:
                            for text in item['text']['text']:
                                total_inspected += 1
                                # At this point, we can capture and store all the text elements for later processing
                                # Perhaps we build a map of protos that contain all the data nicely wrapped up that we can iter over?
                                # TODO (pmarlow) consider implementing a Fulfillment class that can store all these items in an object
                                total_issues += self.fulfillment_linter(trigger, text)

                elif path and wh_key in path:
                    None
                    # logging.info(path[wh_key])

        stats = self.update_stats(total_issues, total_inspected, stats)

        return stats

    def lint_start_page(
        self,
        flow_path: str,
        stats: LintStats):
        """Process a single Flow Path file."""
        with open(flow_path, 'r', encoding='UTF-8') as flow_file:
            data = json.load(flow_file)
            self.current_resource = f'{self.current_flow}:START_PAGE'

            stats = self.lint_fulfillments(stats, data, 'eventHandlers')
            stats = self.lint_fulfillments(stats, data, 'transitionRoutes')

        return stats

    def lint_flow(self, flow_path: str, stats: LintStats):
        """Lint a Single Flow dir and all subdirectories."""
        self.current_flow = self.parse_filepath(flow_path, 'flow')

        message = f'{"*" * 15} Flow: {self.current_flow}'
        logging.info(message)

        start_page_file = f'{flow_path}/{self.current_flow}.json'

        stats = self.lint_start_page(start_page_file, stats)
        stats = self.lint_pages_directory(flow_path, stats)

        return stats

    def lint_page(self, page_path: str, stats: LintStats):
        """Lint a Single Page file."""
        self.current_page = self.parse_filepath(page_path, 'page')

        with open(page_path, 'r', encoding='UTF-8') as page_file:
            data = json.load(page_file)
            self.current_resource = f'{self.current_flow}:{self.current_page}'

            stats = self.lint_fulfillments(stats, data, 'eventHandlers')
            stats = self.lint_fulfillments(stats, data, 'transitionRoutes')

        return stats

    def lint_pages_directory(self, flow_path: str, stats: LintStats):
        """Linting the Pages dir inside a specific Flow dir."""
        # start_message = f'{"*" * 10} Begin Page Linter'
        # logging.info(start_message)

        # Some Flows may not contain Pages, so we check for the existence
        # of the directory before traversing
        if 'pages' in os.listdir(flow_path):
            page_paths = self.traverse.build_page_path_list(flow_path)

            for page_path in page_paths:
                stats.total_pages += 1
                stats = self.lint_page(page_path, stats)

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
        flow_paths = self.traverse.build_flow_path_list(agent_local_path)
        stats.total_flows = len(flow_paths)

        # linting happens here
        for flow_path in flow_paths:
            stats = self.lint_flow(flow_path, stats)

        header = "-" * 20
        rating = (1-(stats.total_issues/stats.total_inspected))*10

        end_message = f'\n{header}\n{stats.total_flows} Flows linted.'\
            f'\n{stats.total_issues} issues found out of '\
            f'{stats.total_inspected} candidates inspected.'\
            f'\nYour Agent Flows rated at {rating:.2f}/10.0\n\n'
        logging.info(end_message)


# TODO: pmarlow - Build another class to traverse different file trees.
# Input: Type of file tree corresponding w/resource name (i.e. intents, testCases, etc.)
# Output: Root file path to start for traversal

    # def get_root_traversal_path(self, resource_type: str):
    #     """Provide resource name and get root traversal path."""
    #     if resource_type == 'flow':
    #         base_path = agent_path + 

    # def find_broken_intents(self, agent_path: str):
    #     base_path = agent_path + '/intents'
    #     for intent_dir in os.listdir(base_path):
    #         for tp_dir in os.listdir(base_path + f'/{intent_dir}'):
