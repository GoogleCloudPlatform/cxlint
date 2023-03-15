"""Route Groups linter methods and functions."""

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

import os
import json

from configparser import ConfigParser

from common import Common

from resources.types import RouteGroup, Flow, LintStats
from resources.routes import Fulfillments


class RouteGroups:
    """Route Groups linter methods and functions."""

    def __init__(self, verbose: bool, config: ConfigParser, console):
        self.verbose = verbose
        self.console = console
        self.config = config
        self.agent_type = Common.load_agent_type(config)
        self.disable_map = Common.load_message_controls(config)
        self.agent_id = Common.load_agent_id(config)
        self.special_pages = [
            "End Session",
            "End Flow",
            "Start Page",
            "Current Page",
            "Previous Page",
        ]

        self.routes = Fulfillments(verbose, config, console)

    @staticmethod
    def build_route_group_path_list(flow_local_path: str):
        """Builds a list of files, each representing a Route Group.

        Ex: /path/to/agent/flows/<flow_dir>/transitionRouteGroups/<rg.json>
        """
        root_dir = flow_local_path + "/transitionRouteGroups"

        if "transitionRouteGroups" in os.listdir(flow_local_path):
            rg_paths = []

            for rg_file in os.listdir(root_dir):
                rg_file_path = f"{root_dir}/{rg_file}"
                rg_paths.append(rg_file_path)

        return rg_paths

    def lint_route_group(self, rg: RouteGroup, stats: LintStats):
        """Lint a single Route Group."""
        rg.display_name = Common.parse_filepath(rg.rg_file, "route_group")
        rg.display_name = Common.clean_display_name(rg.display_name)

        with open(rg.rg_file, "r", encoding="UTF-8") as route_group_file:
            rg.data = json.load(route_group_file)
            rg.resource_id = rg.data.get("name", None)
            rg.display_name = rg.data.get("displayName", None)
            rg.routes = rg.data.get("transitionRoutes", None)

            stats = self.routes.lint_routes(rg, stats)

            route_group_file.close()

        return stats

    def lint_route_groups_directory(self, flow: Flow, stats: LintStats):
        """Linting Route Groups dir in the JSON Package structure."""
        if "transitionRouteGroups" in os.listdir(flow.dir_path):
            # Create a list of all Route Group paths to iter through
            rg_paths = self.build_route_group_path_list(flow.dir_path)
            stats.total_route_groups = len(rg_paths)

            # linting happens here
            for rg_path in rg_paths:
                rg = RouteGroup(flow=flow)
                rg.verbose = self.verbose
                rg.agent_id = self.agent_id
                rg.rg_file = rg_path
                stats = self.lint_route_group(rg, stats)

        return stats
