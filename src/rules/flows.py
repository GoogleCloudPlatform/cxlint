"""Flow Rules and Definitions."""

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

from typing import Dict, Any
from resources.types import Flow, LintStats, Resource

from rules.logger import RulesLogger

class FlowRules:
    """Flow Rules and Definitions."""
    def __init__(
            self,
            console,
            disable_map: Dict[str, Any]):

        self.console = console
        self.disable_map = disable_map
        self.log = RulesLogger(console=console)

    # unused-pages
    def unused_pages(self, flow: Flow, stats: LintStats) -> LintStats:
        """Checks for Unusued Pages in Flow Graph."""
        rule = "R012: Unused Pages"

        for page in flow.unused_pages:
            resource = Resource()
            resource.agent_id = flow.agent_id
            resource.flow_display_name = flow.display_name
            resource.flow_id = flow.resource_id
            resource.page_display_name = page
            resource.page_id = flow.data.get(page, None)
            resource.resource_type = "page"

            message = ""
            stats.total_inspected += 1
            stats.total_issues += 1

            self.log.generic_logger(resource, rule, message)

        return stats

    # dangling-pages
    def dangling_pages(self, flow: Flow, stats: LintStats) -> LintStats:
        """Checks for Dangling Pages in Flow Graph."""
        rule = "R013: Dangling Pages"

        for page in flow.dangling_pages:
            resource = Resource()
            resource.agent_id = flow.agent_id
            resource.flow_display_name = flow.display_name
            resource.flow_id = flow.resource_id
            resource.page_display_name = page
            resource.page_id = flow.data.get(page, None)
            resource.resource_type = "page"

            message = ""
            stats.total_inspected += 1
            stats.total_issues += 1

            self.log.generic_logger(resource, rule, message)

        return stats

    # unreachable-pages
    def unreachable_pages(self, flow: Flow, stats: LintStats) -> LintStats:
        """Checks for Unreachable Pages in Flow Graph."""
        rule = "R014: Unreachable Pages"

        for page in flow.unreachable_pages:
            resource = Resource()
            resource.agent_id = flow.agent_id
            resource.flow_display_name = flow.display_name
            resource.flow_id = flow.resource_id
            resource.page_display_name = page
            resource.page_id = flow.data.get(page, None)
            resource.resource_type = "page"

            message = ""
            stats.total_inspected += 1
            stats.total_issues += 1

            self.log.generic_logger(resource, rule, message)

        return stats

    def run_flow_rules(self, flow: Flow, stats: LintStats) -> LintStats:
        """Checks and Executes all Flow level rules."""
        # unused-pages
        if self.disable_map.get("unused-pages", True):
            stats = self.unused_pages(flow, stats)

        # dangling-pages
        if self.disable_map.get("dangling-pages", True):
            stats = self.dangling_pages(flow, stats)

        # unreachable-pages
        if self.disable_map.get("unreachable-pages", True):
            stats = self.unreachable_pages(flow, stats)

        return stats
