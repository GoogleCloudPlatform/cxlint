"""Core class and methods for CX Linter."""

import configparser
import os
import json
import logging
import re

from dataclasses import dataclass, field
from typing import Dict, List, Any

from cxlint.rules import RulesDefinitions # pylint: disable=E0401
# from file_traversal import FileTraversal # pylint: disable=E0401

# logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

# configparser
config = configparser.ConfigParser()
config.read('cxlint/.cxlintrc')

@dataclass
class LintStats:
    """Used to track linter stats for each section processed."""
    total_issues: int = 0
    total_inspected: int = 0
    total_flows: int = 0
    total_pages: int = 0
    total_intents: int = 0
    total_training_phrases: int = 0
    total_entities: int = 0
    total_route_groups: int = 0

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

@dataclass
class Intent:
    """Used to track current Intent Attributes."""
    display_name: str = None
    dir_path: str = None
    metadata_file: str = None
    labels: Dict[str, str] = None
    description: str = None
    training_phrases: Dict[str, Any] = field(default_factory=dict)
    verbose: bool = False
    data: Dict[str, Any] = None

# @dataclass
# class TrainingPhrases:
#     """Used to track current Training Phrase Attributes."""


class CxLint:
    """Core CX Linter methods and functions."""
    def __init__(
        self,
        verbose: bool = False):

        self.rules = RulesDefinitions()
        self.verbose = verbose
        self.disable_map = self.load_message_controls()

    @staticmethod
    def load_message_controls() -> Dict[str,str]:
        """Loads the config file for message control into a map."""
        msg_list = config['MESSAGES CONTROL']['disable'].replace(
            '\n', '').split(',')

        msg_dict = {msg:False for msg in msg_list}

        return msg_dict

    @staticmethod
    def calculate_rating(total_issues: int, total_inspected: int) -> float:
        """Calculate the final rating for the linter stats."""
        rating = (1-(total_issues/total_inspected))*10

        return rating

    @staticmethod
    def parse_lang_code(lang_code_path: str) -> str:
        """Extract the language_code from the given file path."""

        first_parse = lang_code_path.split('/')[-1]
        lang_code = first_parse.split('.')[0]

        return lang_code

    @staticmethod
    def build_lang_code_paths(intent: Intent):
        """Builds dict of lang codes and file locations.

        The language_codes and paths for each file are stored in a dictionary
        inside of the Intent dataclass. This dict is access later to lint each
        file and provide reporting based on each language code.
        """
        training_phrases_path = intent.dir_path + '/trainingPhrases'

        for lang_file in os.listdir(training_phrases_path):
            lang_code = lang_file.split('.')[0]
            lang_code_path = f'{training_phrases_path}/{lang_file}'
            intent.training_phrases[lang_code] = {'file_path': lang_code_path}

    @staticmethod
    def build_intent_path_list(agent_local_path: str):
        """Builds a list of dirs, each representing an Intent directory.

        Ex: /path/to/agent/intents/<intent_dir>

        This dir path can be used to find the next level of information
        in the directory by appending the appropriate next dir structures like:
        - <intent_name>.json, for the Intent object metadata
        - /trainingPhrases, for the Training Phrases dir
        """
        intents_path = agent_local_path + '/intents'

        intent_paths = []

        for intent_dir in os.listdir(intents_path):
            intent_dir_path = f'{intents_path}/{intent_dir}'
            intent_paths.append(intent_dir_path)

        return intent_paths

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
            # start_page_flow_file = flow_dir + '.json'
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

    # @staticmethod
    # def update_stats(
    #     local_issues: int,
    #     local_inspected: int,
    #     stats: LintStats) -> LintStats:
    #     """Update the current LintStats object."""
    #     stats.total_issues += local_issues
    #     stats.total_inspected += local_inspected

    #     return stats

    @staticmethod
    def parse_filepath(in_path: str, resource_type: str) -> str:
        """Parse file path to provide quick reference for linter log."""

        regex_map = {
            'flow': r'.*\/flows\/([^\/]*)',
            'page': r'.*\/pages\/([^\/]*)\.',
            'intent': r'.*\/intents\/([^\/]*)'
        }
        resource_name = re.match(regex_map[resource_type], in_path).groups()[0]

        return resource_name

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
        # total_issues = 0

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


        return stats

    def lint_flow(self, flow: Flow, stats: LintStats):
        """Lint a Single Flow dir and all subdirectories."""
        flow.display_name = self.parse_filepath(flow.dir_path, 'flow')

        message = f'{"*" * 15} Flow: {flow.display_name}'
        logging.info(message)

        flow.start_page_file = f'{flow.dir_path}/{flow.display_name}.json'

        stats = self.lint_start_page(flow, stats)
        stats = self.lint_pages_directory(flow, stats)

        return stats

    def lint_page(self, page: Page, stats: LintStats):
        """Lint a Single Page file."""
        page.display_name = self.parse_filepath(page.page_file, 'page')

        with open(page.page_file, 'r', encoding='UTF-8') as page_file:
            page.data = json.load(page_file)
            page.events = page.data.get('eventHandlers', None)
            page.routes = page.data.get('transitionRoutes', None)

            stats = self.lint_events(page, stats)
            stats = self.lint_routes(page, stats)

        return stats

    def lint_intent_metadata(self, intent: Intent, stats: LintStats):
        """Lint the metadata file for a single Intent."""
        intent.metadata_file = f'{intent.dir_path}/{intent.display_name}.json'

        with open(intent.metadata_file, 'r', encoding='UTF-8') as meta_file:
            intent.data = json.load(meta_file)
            intent.labels = intent.data.get('labels', None)
            intent.description = intent.data.get('description', None)

            # TODO: Linting rules for Intent Metadata

        return stats

    def lint_language_codes(self, intent: Intent, stats: LintStats):
        """Executes all Training Phrase based linter rules."""

        for lang_code in intent.training_phrases:
            tp_file = intent.training_phrases[lang_code]['file_path']

            with open(tp_file, 'r', encoding='UTF-8') as tps:
                data = json.load(tps)
                intent.training_phrases[lang_code]['tps'] = data['trainingPhrases']

                # intent-min-tps
                if self.disable_map.get('intent-min-tps', True):
                    stats = self.rules.min_tps_head_intent(
                        intent, lang_code, stats)


        return stats

    def lint_training_phrases(self, intent: Intent, stats: LintStats):
        """Lint the Training Phrase dir for a single Intent."""
        if 'trainingPhrases' in os.listdir(intent.dir_path):
            self.build_lang_code_paths(intent)
            stats = self.lint_language_codes(intent, stats)

        # intent-missing-tps
        elif self.disable_map.get('intent-missing-tps', True):
            stats = self.rules.missing_training_phrases(intent, stats)

        return stats


    def lint_intent(self, intent: Intent, stats: LintStats):
        """Lint a single Intent directory and associated files."""
        intent.display_name = self.parse_filepath(intent.dir_path, 'intent')

        stats = self.lint_intent_metadata(intent, stats)
        stats = self.lint_training_phrases(intent, stats)

        return stats

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
        rating = self.calculate_rating(
            stats.total_issues, stats.total_inspected)

        end_message = f'\n{header}\n{stats.total_flows} Flows linted.'\
            f'\n{stats.total_issues} issues found out of '\
            f'{stats.total_inspected} fulfillments inspected.'\
            f'\nYour Agent Flows rated at {rating:.2f}/10.0\n\n'
        logging.info(end_message)

    def lint_intents_directory(self, agent_local_path: str):
        """Linting the top level Intents Dir in the JSON Package structure.

        The following files/dirs exist under the `intents` dir:
        - <intent_display_name> Directory
          - trainingPhrases
            - <language-code>.json
          - <intent_display_name> Object

        In Dialogflow CX, the Training Phrases of each Intent are stored in
        individual .json files by language code under each Intent Display
        Name. In this method, we will lint all Intent dirs, including the
        training phrase files and metadata objects for each Intent.
        """
        start_message = f'{"#" * 10} Begin Intents Directory Linter'
        logging.info(start_message)

        stats = LintStats()

        # Create a list of all Intent paths to iter through
        intent_paths = self.build_intent_path_list(agent_local_path)
        stats.total_intents = len(intent_paths)

        # Linting Starts Here
        for intent_path in intent_paths:
            intent = Intent()
            intent.verbose = self.verbose
            intent.dir_path = intent_path
            stats = self.lint_intent(intent, stats)
            stats.total_inspected += 1

        header = "-" * 20
        rating = self.calculate_rating(
            stats.total_issues, stats.total_inspected)

        end_message = f'\n{header}\n{stats.total_intents} Intents linted.'\
            f'\n{stats.total_issues} issues found out of '\
            f'{stats.total_inspected} Intents inspected.'\
            f'\nYour Agent Intents rated at {rating:.2f}/10.0\n\n'
        logging.info(end_message)

    def lint_agent(self, agent_local_path: str):
        """Linting the entire CX Agent and all resource directories."""
        # agent_file = agent_local_path + '/agent.json'
        # with open(agent_file, 'r', encoding='UTF-8') as agent_data:
        #     data = json.load(agent_data)

        start_message = f'{"=" * 5} LINTING AGENT {"=" * 5}\n'
        logging.info(start_message)


        self.lint_flows_directory(agent_local_path)
        self.lint_intents_directory(agent_local_path)
