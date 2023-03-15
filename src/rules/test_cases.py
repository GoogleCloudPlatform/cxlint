"""Test Case Rules and Definitions."""

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
from resources.types import TestCase, LintStats, Resource

from rules.logger import RulesLogger

class TestCaseRules:
    """Test Case Rules and Definitions."""
    def __init__(
            self,
            console,
            disable_map: Dict[str, Any]):

        self.console = console
        self.disable_map = disable_map
        self.log = RulesLogger(console=console)

    # explicit-tps-in-test-cases
    def explicit_tps_in_tcs(self, tc: TestCase, stats: LintStats) -> LintStats:
        """Checks that user utterance is an explicit intent training phrase."""
        rule = "R007: Explicit Training Phrase Not in Test Case"

        for pair in tc.intent_data:
            stats.total_inspected += 1

            intent = pair["intent"]
            phrase = pair["user_utterance"]

            if phrase not in pair["training_phrases"]:
                message = f": [Utterance: {phrase} | Intent: {intent}]"

                resource = Resource()
                resource.agent_id = tc.agent_id
                resource.test_case_display_name = tc.display_name
                resource.test_case_id = tc.resource_id
                resource.resource_type = "test_case"

                stats.total_issues += 1
                self.log.generic_logger(resource, rule, message)

        return stats

    # invalid-intent-in-test-cases
    def invalid_intent_in_tcs(
        self, tc: TestCase, stats: LintStats
    ) -> LintStats:
        """Check that a listed Intent in the Test Case exists in the agent."""
        rule = "R008: Invalid Intent in Test Case"

        for pair in tc.intent_data:
            if pair["status"] == "invalid_intent":
                stats.total_inspected += 1
                stats.total_issues += 1

        resource = Resource()
        resource.agent_id = tc.agent_id
        resource.test_case_display_name = tc.display_name
        resource.test_case_id = tc.resource_id
        resource.resource_type = "test_case"

        message = ""
        self.log.generic_logger(resource, rule, message)

        return stats

    def run_test_case_rules(self, tc: TestCase, stats: LintStats) -> LintStats:
        """Checks and Executes all Test Case level rules."""
        if tc.qualified:
            # R007 explicit-tps-in-test-cases
            if self.disable_map.get("explicit-tps-in-test-cases", True):
                stats.total_test_cases += 1
                stats = self.explicit_tps_in_tcs(tc, stats)

        if tc.has_invalid_intent:
            # R008 invalid-intent-in-test-cases
            if self.disable_map.get("invalid-intent-in-test-cases", True):
                stats.total_test_cases += 1
                stats = self.invalid_intent_in_tcs(tc, stats)

        return stats
