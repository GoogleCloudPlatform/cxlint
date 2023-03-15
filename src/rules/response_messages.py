"""Response Message Rules and Definitions."""

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

import re

from typing import Dict, Any
from resources.types import Fulfillment, LintStats, Resource

from rules.logger import RulesLogger

class ResponseMessageRules:
    """Response Message Rules and Definitions."""
    def __init__(
            self,
            console,
            disable_map: Dict[str, Any]):

        self.console = console
        self.disable_map = disable_map
        self.log = RulesLogger(console=console)

   # RESPONSE MESSAGE RULES
    # closed-choice-alternative
    def closed_choice_alternative_parser(
        self, route: Fulfillment, stats: LintStats
    ) -> LintStats:
        """Identifies a Closed Choice Alternative Question."""
        rule = (
            "R001: Closed-Choice Alternative Missing Intermediate `?` "
            "(A? or B.)"
        )
        message = f": {route.trigger}"

        pattern = r"^(What|Where|When|Who|Why|How|Would) (.*) or (.*)\?$"

        match = re.search(pattern, route.text, flags=re.IGNORECASE)

        if match:
            resource = Resource()
            resource.agent_id = route.agent_id
            resource.flow_display_name = route.page.flow.display_name
            resource.flow_id = route.page.flow.resource_id
            resource.page_display_name = route.page.display_name
            resource.page_id = route.page.resource_id
            resource.resource_type = "fulfillment"

            stats.total_issues += 1
            self.log.generic_logger(resource, rule, message)

        return stats

    # wh-questions
    def wh_questions(self, route: Fulfillment, stats: LintStats) -> LintStats:
        """Identifies a Wh- Question and checks for appropriate punctuation."""
        rule = "R002: Wh- Question Should Use `.` Instead of `?` Punctuation"
        message = f": {route.trigger}"

        pattern = r"^(what|when|where|who|why|how)\b.*\?$"

        match = re.search(pattern, route.text, flags=re.IGNORECASE)

        if match and "event" not in route.trigger:
            resource = Resource()
            resource.agent_id = route.agent_id
            resource.flow_display_name = route.page.flow.display_name
            resource.flow_id = route.page.flow.resource_id
            resource.page_display_name = route.page.display_name
            resource.page_id = route.page.resource_id
            resource.resource_type = "fulfillment"

            stats.total_issues += 1
            self.log.generic_logger(resource, rule, message)

        return stats

    # clarifying-questions
    def clarifying_questions(
        self, route: Fulfillment, stats: LintStats
    ) -> LintStats:
        """Identifies Clarifying Questions that are missing `?` Punctuation."""
        rule = "R003: Clarifying Question Should Use `?` Punctuation"
        message = f": {route.trigger}"

        # updated pattern
        pattern = r"^(what|when|where|who|why|how)\b.*\.$"

        match = re.search(pattern, route.text, flags=re.IGNORECASE)

        if match and "event" in route.trigger:
            resource = Resource()
            resource.agent_id = route.agent_id
            resource.flow_display_name = route.page.flow.display_name
            resource.flow_id = route.page.flow.resource_id
            resource.page_display_name = route.page.display_name
            resource.page_id = route.page.resource_id
            resource.resource_type = "fulfillment"

            stats.total_issues += 1
            self.log.generic_logger(resource, rule, message)

        return stats

    def run_rm_text_rules(
        self,
        route: Fulfillment,
        stats: LintStats) -> LintStats:
        """Checks and Executes all Response Message level rules.

        This set of rules will be executed against the Response Messages that
        are of type `text`. This is equivalent to the "Agent Says" sections of
        the agent design-time console.
        """
        voice = False

        if route.agent_type == "voice":
            voice = True

        # Some rules are only appropriate to lint for Voice agents.
        # For example, rules that deal with SSML, DTMF, STT intonation, etc.
        # We will use the `voice` bool value to filter these rules out for
        # non-voice agents.

        # closed-choice-alternative
        if self.disable_map.get("closed-choice-alternative", True) and voice:
            stats = self.closed_choice_alternative_parser(route, stats)

        # wh-questions
        if self.disable_map.get("wh-questions", True) and voice:
            stats = self.wh_questions(route, stats)

        # clarifying-questions
        if self.disable_map.get("clarifying-questions", True) and voice:
            stats = self.clarifying_questions(route, stats)

        return stats
