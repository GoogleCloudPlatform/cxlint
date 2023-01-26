"""Core class and methods for CX Linter."""

import configparser
import os
import logging

from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple, Union

from common import Common
from gcs_utils import GcsUtils
from rules import RulesDefinitions # pylint: disable=E0401
from resources.flows import Flows
from resources.entity_types import EntityTypes
from resources.intents import Intents
from resources.test_cases import TestCases

# logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

# configparser
config = configparser.ConfigParser()
config.sections()

config.read_file(open(os.path.join(os.path.dirname(__file__), '..', '.cxlintrc')))

class CxLint:
    """Core CX Linter methods and functions."""
    def __init__(
        self,
        agent_id: str = None,
        intent_pattern: str = None,
        load_gcs: bool = False,
        report: bool = False,
        resource_filter: Union[List[str], str] = None,
        test_case_pattern: str = None,
        test_case_tags: Union[List[str], str] = None,
        verbose: bool = False):

        if load_gcs:
            self.gcs = GcsUtils()

        if test_case_pattern:
            self.update_config(
                'TEST CASE DISPLAY NAME PATTERN', test_case_pattern)

        if test_case_tags:
            self.update_config('TEST CASE TAGS', test_case_tags)

        if agent_id:
            self.update_config('AGENT ID', agent_id)

        if intent_pattern:
            self.update_config('INTENTS', intent_pattern)

        if resource_filter:
            self.update_config('AGENT RESOURCES', resource_filter)

        self.resource_filter = Common.load_resource_filter(config)

        self.entity_types = EntityTypes(verbose, config)
        self.intents = Intents(verbose, config)
        self.flows = Flows(verbose, config)
        self.test_cases = TestCases(verbose, config)

    @staticmethod
    def read_and_append_to_config(section: str, key: str, data: Any):
        """Reads the existing config file and appends any new data."""
        existing_data = config[section][key]

        # Check for empty string from file and set to None
        if existing_data != '':
            data = existing_data + ',' + data

        config.set(section, key, data)

    @staticmethod
    def transform_list_to_str(data: Union[List[str], str]):
        """Determine input data and parse accordingly for config update."""
        res = data

        if isinstance(data, List):
            res = ','.join(data)

        if not isinstance(res, str):
            raise ('Input must be one of the following formats: `str` | '\
                    'List[`str`]')

        return res

    def update_config(self, section: str, data: Any):
        """Update the Config file based on user provided kwargs."""
        if section == 'AGENT ID':
            config.set(section, 'id', data)

        if section == 'AGENT RESOURCES':
            data = self.transform_list_to_str(data)
            config.set(section, 'include', data)

        if section == 'INTENTS':
            config.set(section, 'pattern', data)

        if section == 'TEST CASE TAGS':
            data = self.transform_list_to_str(data)
            self.read_and_append_to_config(section, 'include', data)

            # if isinstance(data, str):
            #     self.read_and_append_to_config(section, 'include', data)
            # elif isinstance(data, List):
            #     tag_string = ','.join(data)
            #     self.read_and_append_to_config(section, 'include', tag_string)
            # else:
            #     raise ('Input must be one of the following formats: `str` | '\
            #         'List[`str`]')

        if section == 'TEST CASE DISPLAY NAME PATTERN':
            config.set(section, 'pattern', data)        

    def lint_agent(
        self,
        agent_local_path: str):
        """Linting the entire CX Agent and all resource directories."""
        # agent_file = agent_local_path + '/agent.json'
        # with open(agent_file, 'r', encoding='UTF-8') as agent_data:
        #     data = json.load(agent_data)

        start_message = f'{"=" * 5} LINTING AGENT {"=" * 5}\n'
        logging.info(start_message)

        if self.resource_filter.get('flows', False):
            self.flows.lint_flows_directory(agent_local_path)

        if self.resource_filter.get('entity_types', False):
            self.entity_types.lint_entity_types_directory(agent_local_path)

        if self.resource_filter.get('intents', False):
            self.intents.lint_intents_directory(agent_local_path)

        if self.resource_filter.get('test_cases', False):
            self.test_cases.lint_test_cases_directory(agent_local_path)
