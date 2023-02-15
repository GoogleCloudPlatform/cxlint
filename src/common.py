import logging
import re

from configparser import ConfigParser
from typing import Dict, List

# logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

class Common:
    @staticmethod
    def load_message_controls(config: ConfigParser) -> Dict[str,str]:
        """Loads the config file for message control into a map."""
        msg_list = config['MESSAGES CONTROL']['disable'].replace(
            '\n', '').split(',')

        msg_dict = {msg:False for msg in msg_list}

        return msg_dict

    @staticmethod
    def load_agent_type(config: ConfigParser) -> Dict[str,str]:
        """Loads the config file for agent type."""
        agent_type = config['AGENT TYPE']['type']

        return agent_type

    @staticmethod
    def load_resource_filter(config: ConfigParser) -> List[str]:
        """Loads the config file for agent resource filtering."""
        resource_filter = config['AGENT RESOURCES']['include'].replace(
            '\n', '').split(',')

        resource_dict = {
            'entity_types': True,
            'flows': True,
            'intents': True,
            'test_cases': True,
            'webhooks': True
            }

        if len(resource_filter) == 1 and resource_filter[0] == '':
            resource_filter = None

        if resource_filter:
            for resource in resource_dict:
                if resource not in resource_filter:
                    resource_dict[resource] = False

        return resource_dict


    @staticmethod
    def load_agent_id(config: ConfigParser) -> str:
        """Loads the Agent ID from the config file if provided."""
        agent_id = config['AGENT ID']['id']
        
        return agent_id

    @staticmethod
    def calculate_rating(total_issues: int, total_inspected: int) -> float:
        """Calculate the final rating for the linter stats."""
        if total_inspected > 0:
            rating = (1-(total_issues/total_inspected))*10

        else:
            rating = 10

        return rating

    @staticmethod
    def parse_filepath(in_path: str, resource_type: str) -> str:
        """Parse file path to provide quick reference for linter log."""

        regex_map = {
            'flow': r'.*\/flows\/([^\/]*)',
            'page': r'.*\/pages\/([^\/]*)\.',
            'entity_type': r'.*\/entityTypes\/([^\/]*)',
            'intent': r'.*\/intents\/([^\/]*)'
        }
        resource_name = re.match(regex_map[resource_type], in_path).groups()[0]

        return resource_name
    
    @staticmethod
    def clean_display_name(display_name: str):
        """Replace cspecial haracters from map for the given display name."""
        patterns = {
            "%28": "(",
            "%29": ")",
            "%23": "#",
            "%2f": "/",
            "%3f": "?",
            "%3a": ":",
            "%2c": ","
            }

        for pattern in patterns:
            if pattern in display_name:
                display_name = display_name.replace(pattern, patterns[pattern])

        return display_name