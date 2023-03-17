"""Agent Metadata linter methods and functions."""

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

from configparser import ConfigParser

from common import Common



class Agents:
    """Agent Metadata linter methods and functions."""

    def __init__(self, verbose: bool, config: ConfigParser, console):
        self.verbose = verbose
        self.console = console
        self.config = config
        self.agent_type = Common.load_agent_type(config)
        self.disable_map = Common.load_message_controls(config)
        self.agent_id = Common.load_agent_id(config)
        self.naming_conventions = Common.load_naming_conventions(config)

    def lint_agents_metadata(self, agent_local_path: str):
        """Linting the Agent Metadata file."""

        # TODO (pmarlow):  Add Agent Metadata lint methods
