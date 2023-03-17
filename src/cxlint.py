"""Core class and methods for CX Linter."""

# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import configparser
import os
import logging

from rich.console import Console
from rich.logging import RichHandler

from typing import List, Any, Union, Dict

from common import Common
from gcs_utils import GcsUtils

from resources.agents import Agents
from resources.flows import Flows
from resources.entity_types import EntityTypes
from resources.intents import Intents
from resources.test_cases import TestCases
from resources.webhooks import Webhooks

console = Console(
    record=True,
    log_time=False,
    log_path=False,
    width=200,
    color_system="truecolor",
)

keywords = [
    "Flows Directory",
    "Entity Types Directory",
    "Test Cases Directory",
    "Intents Directory",
]
handler = RichHandler(
    enable_link_path=False,
    keywords=keywords,
    show_time=False,
    show_level=False,
    show_path=False,
    tracebacks_word_wrap=False,
)

# logging config
logging.basicConfig(
    level=logging.INFO, format="%(message)s", handlers=[handler], force=True
)

# configparser
config = configparser.ConfigParser()
config.sections()

config_filepath = os.path.join(os.path.dirname(__file__), "..", ".cxlintrc")
with open(config_filepath, encoding="UTF-8") as config_filepath_infile:
    config.read_file(config_filepath_infile)


class CxLint:
    """Core CX Linter methods and functions."""

    def __init__(
        self,
        agent_id: str = None,
        agent_type: str = None,
        intent_include_pattern: str = None,
        intent_exclude_pattern: str = None,
        flow_include_list: List[str] = None,
        flow_exclude_list: List[str] = None,
        language_code: Union[List[str], str] = None,
        load_gcs: bool = False,
        naming_conventions: Dict[str, str] = None,
        output_file: str = None,
        resource_filter: Union[List[str], str] = None,
        test_case_pattern: str = None,
        test_case_tags: Union[List[str], str] = None,
        verbose: bool = True,
    ):
        if load_gcs:
            self.gcs = GcsUtils()

        if agent_id:
            self.update_config("AGENT ID", agent_id)

        if agent_type:
            self.update_config("AGENT TYPE", agent_type)

        if flow_include_list or flow_exclude_list:
            self.update_flows_config(flow_include_list, flow_exclude_list)

        if intent_exclude_pattern or intent_include_pattern:
            self.update_intent_config(
                intent_include_pattern, intent_exclude_pattern
            )

        if language_code:
            self.update_config("INTENTS", language_code)

        if naming_conventions:
            self.update_naming_conventions_config(
                "NAMING CONVENTIONS", naming_conventions)

        if resource_filter:
            self.update_config("AGENT RESOURCES", resource_filter)

        if test_case_pattern:
            self.update_config(
                "TEST CASE DISPLAY NAME PATTERN", test_case_pattern
            )

        if test_case_tags:
            self.update_config("TEST CASE TAGS", test_case_tags)

        self.resource_filter = Common.load_resource_filter(config)
        self.output_file = output_file

        self.agents = Agents(verbose, config, console)
        self.entity_types = EntityTypes(verbose, config, console)
        self.intents = Intents(verbose, config, console)
        self.flows = Flows(verbose, config, console)
        self.test_cases = TestCases(verbose, config, console)
        self.webhooks = Webhooks(verbose, config, console)

    @staticmethod
    def read_and_append_to_config(section: str, key: str, data: Any):
        """Reads the existing config file and appends any new data."""
        existing_data = config[section][key]

        # Check for empty string from file and set to None
        if existing_data != "":
            data = existing_data + "," + data

        config.set(section, key, data)

    @staticmethod
    def transform_list_to_str(data: Union[List[str], str]):
        """Determine input data and parse accordingly for config update."""
        res = data

        if isinstance(data, List):
            res = ",".join(data)

        if not isinstance(res, str):
            raise TypeError(
                "Input must be one of the following formats: `str` | "
                "List[`str`]"
            )

        return res
    
    def update_naming_conventions_config(self, section: str, styles: Dict[str, Dict]):
        """Update the Naming Conventions config based on user inputs."""

        for key, value in styles.items():
            if not isinstance(value, str):
                raise TypeError("Naming Convention values must be type `string`")            

            config.set(section, key, value)


    def update_flows_config(self, include_pattern: str, exclude_pattern: str):
        """Handle updates to the Flow include/exclude lists."""
        if include_pattern:
            data = self.transform_list_to_str(include_pattern)
            config.set("FLOWS", "include", data)

        if exclude_pattern:
            data = self.transform_list_to_str(exclude_pattern)
            config.set("FLOWS", "exclude", data)

    def update_intent_config(self, include_pattern: str, exclude_pattern: str):
        """Handle updates to the Intent include/exclude lists."""
        if include_pattern:
            config.set("INTENTS", "include", include_pattern)

        if exclude_pattern:
            config.set("INTENTS", "exclude", exclude_pattern)

    def update_config(self, section: str, data: Any):
        """Update the Config file based on user provided kwargs."""
        if section == "AGENT ID":
            config.set(section, "id", data)

        if section == "AGENT RESOURCES":
            data = self.transform_list_to_str(data)
            config.set(section, "include", data)

        if section == "AGENT TYPE":
            config.set(section, "type", data)

        if section == "INTENTS":
            data = self.transform_list_to_str(data)
            config.set(section, "language_code", data)

        if section == "TEST CASE TAGS":
            data = self.transform_list_to_str(data)
            self.read_and_append_to_config(section, "include", data)

        if section == "TEST CASE DISPLAY NAME PATTERN":
            config.set(section, "pattern", data)

    def lint_agent(self, agent_local_path: str):
        """Linting the entire CX Agent and all resource directories."""
        # agent_file = agent_local_path + '/agent.json'
        # with open(agent_file, 'r', encoding='UTF-8') as agent_data:
        #     data = json.load(agent_data)

        start_message = f'{"=" * 5} LINTING AGENT {"=" * 5}\n'
        console.log(start_message)
        resources = Common.resource_precheck(
            agent_local_path, self.resource_filter)

        if resources["agents"]:
            self.agents.lint_agents_metadata(agent_local_path)

        if resources["flows"]:
            self.flows.lint_flows_directory(agent_local_path)

        if resources["entity_types"]:
            self.entity_types.lint_entity_types_directory(agent_local_path)

        if resources["intents"]:
            self.intents.lint_intents_directory(agent_local_path)

        if resources["test_cases"]:
            self.test_cases.lint_test_cases_directory(agent_local_path)

        if resources["webhooks"]:
            self.webhooks.lint_webhooks_directory(agent_local_path)

        if self.output_file:
            console.save_text(self.output_file)
