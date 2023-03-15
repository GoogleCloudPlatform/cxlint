"""Common methods and helper functions used throughout library."""

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

import logging
import os
import re

from configparser import ConfigParser
from typing import Dict, List, Union
from resources.types import Intent, EntityType

# logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)


class Common:
    """Common methods and helper functions used throughout library."""

    @staticmethod
    def load_message_controls(config: ConfigParser) -> Dict[str, str]:
        """Loads the config file for message control into a map."""
        msg_list = (
            config["MESSAGES CONTROL"]["disable"].replace("\n", "").split(",")
        )

        msg_dict = {msg: False for msg in msg_list}

        return msg_dict

    @staticmethod
    def load_agent_type(config: ConfigParser) -> Dict[str, str]:
        """Loads the config file for agent type."""
        agent_type = config["AGENT TYPE"]["type"]

        return agent_type

    @staticmethod
    def load_resource_filter(config: ConfigParser) -> List[str]:
        """Loads the config file for agent resource filtering."""
        resource_filter = (
            config["AGENT RESOURCES"]["include"].replace("\n", "").split(",")
        )

        resource_dict = {
            "entity_types": True,
            "flows": True,
            "intents": True,
            "test_cases": True,
            "webhooks": True,
        }

        if len(resource_filter) == 1 and resource_filter[0] == "":
            resource_filter = None

        if resource_filter:
            for resource in resource_dict:
                if resource not in resource_filter:
                    resource_dict[resource] = False

        return resource_dict

    @staticmethod
    def load_agent_id(config: ConfigParser) -> str:
        """Loads the Agent ID from the config file if provided."""
        agent_id = config["AGENT ID"]["id"]

        return agent_id

    @staticmethod
    def calculate_rating(total_issues: int, total_inspected: int) -> float:
        """Calculate the final rating for the linter stats."""
        if total_inspected > 0:
            rating = (1 - (total_issues / total_inspected)) * 10

        else:
            rating = 10

        return rating

    @staticmethod
    def parse_filepath(in_path: str, resource_type: str) -> str:
        """Parse file path to provide quick reference for linter log."""

        regex_map = {
            "flow": r".*\/flows\/([^\/]*)",
            "page": r".*\/pages\/([^\/]*)\.",
            "entity_type": r".*\/entityTypes\/([^\/]*)",
            "intent": r".*\/intents\/([^\/]*)",
            "route_group": r".*\/transitionRouteGroups\/([^\/]*)",
        }
        resource_name = re.match(regex_map[resource_type], in_path).groups()[0]

        return resource_name

    @staticmethod
    def clean_display_name(display_name: str):
        """Replace cspecial haracters from map for the given display name."""
        patterns = {
            "%22": '"',
            "%23": "#",
            "%24": "$",
            "%26": "&",
            "%27": "'",
            "%28": "(",
            "%29": ")",
            "%2c": ",",
            "%2f": "/",
            "%3a": ":",
            "%3c": "<",
            "%3d": "=",
            "%3e": ">",
            "%3f": "?",
            "%5b": "[",
            "%5d": "]",
            "%e2%80%9c": "“",
            "%e2%80%9d": "”",
        }

        for key, value in patterns.items():
            if key in display_name:
                display_name = display_name.replace(key, value)

        return display_name

    @staticmethod
    def load_lang_code_filter(config: ConfigParser) -> str:
        """Loads the language code filter for Intent Training Phrases."""
        lang_codes = config["INTENTS"]["language_code"]
        lang_code_list = lang_codes.split(",")

        if len(lang_code_list) == 1 and lang_code_list[0] == "":
            lang_code_list = None

        return lang_code_list

    @staticmethod
    def get_file_based_on_lang_code_filter(
        resource: Union[Intent, EntityType], lang_code, lang_code_filter
    ) -> Union[Intent, EntityType]:
        """Gets the file if it qualifies for lang_code filter."""
        # TODO pmarlow: Refactor for better readability

        if lang_code_filter:
            if lang_code in lang_code_filter:
                if isinstance(resource, Intent):
                    filename = resource.training_phrases[lang_code]["file_path"]

                if isinstance(resource, EntityType):
                    filename = resource.entities[lang_code]["file_path"]
            else:
                filename = None

        else:
            if isinstance(resource, Intent):
                filename = resource.training_phrases[lang_code]["file_path"]

            if isinstance(resource, EntityType):
                filename = resource.entities[lang_code]["file_path"]

        return filename

    @staticmethod
    def resource_precheck(
        agent_local_path: str,
        resource_filter: Dict[str, bool]):
        """PreLint Check to ensure the resource directory exists.

        The `resources` dict uses camelCase because the file structure is in
        camelCase. The `resource_filter` uses snake_case because the incoming
        .cxlintrc file stores the data this way. There is some minor string
        manipulation for resources that have 2 names to ensure we're checking
        everything appropriately."""
        resources = {
            "flows": False,
            "entityTypes": False,
            "intents": False,
            "testCases": False,
            "webhooks": False
        }

        # Ensure resource directories exist
        for resource, _ in resources.items():
            if resource in os.listdir(agent_local_path):
                resources[resource] = True

        # Clean up dict so we can use snake_case from here on
        resources["entity_types"] = resources["entityTypes"]
        resources["test_cases"] = resources["testCases"]
        resources.pop("entityTypes", None)
        resources.pop("testCases", None)

        # Check against user requrest filters
        for resource, value in resource_filter.items():
            if not value:
                resources[resource] = False

        return resources
