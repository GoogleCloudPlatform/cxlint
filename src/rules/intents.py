"""Intent Rules and Definitions."""

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
from resources.types import Intent, LintStats, Resource

from rules.logger import RulesLogger

class IntentRules:
    """Intent Rules and Definitions."""
    def __init__(
            self,
            console,
            disable_map: Dict[str, Any]):

        self.console = console
        self.disable_map = disable_map
        self.log = RulesLogger(console=console)

    @staticmethod
    def check_if_head_intent(intent: Intent):
        """Checks if Intent is Head Intent based on labels and name."""
        hid = False

        if "head" in intent.display_name:
            hid = True

        return hid
    
    # intent-missing-metadata
    def intent_missing_metadata(
        self,
        intent: Intent,
        stats: LintStats) -> LintStats:
        """Flags Intent that has missing metadata file.
        
        This rule is separate from the main group of Intent rules because it
        checks for the existence of Intent files and metadata prior to
        unpacking any language codes or training phrases. It will not be
        bundled in the `run_training_phrase_rules` method.
        """
        rule = "R010: Missing Metadata file for Intent"
        message = ""

        resource = Resource()
        resource.agent_id = intent.agent_id
        resource.intent_display_name = intent.display_name
        resource.intent_id = intent.resource_id
        resource.resource_type = "intent"

        stats.total_inspected += 1
        stats.total_issues += 1

        self.log.generic_logger(resource, rule, message)

        return stats

    # intent-missing-tps
    def missing_training_phrases(
        self,
        intent: Intent,
        stats: LintStats) -> LintStats:
        """Checks for Intents that are Missing Training Phrases

        This rule is separate from the main group of Intent rules because it
        checks for the existence of data inside a single language code file.
        If data is completely missing (i.e. no training phrases), the file
        is never opened and we only flag the missing phrases.
        """
        if self.disable_map.get("intent-missing-tps", True):
            rule = "R004: Intent is Missing Training Phrases."
            message = f": {intent.training_phrases}"

            resource = Resource()
            resource.agent_id = intent.agent_id
            resource.intent_display_name = intent.display_name
            resource.intent_id = intent.resource_id
            resource.resource_type = "intent"

            stats.total_inspected += 1
            stats.total_issues += 1
            self.log.generic_logger(resource, rule, message)

        return stats

    # intent-min-tps
    def min_tps_head_intent(
        self,
        intent: Intent,
        lang_code: str,
        stats: LintStats) -> LintStats:
        """Determines if Intent has min recommended training phrases"""
        n_tps = len(intent.training_phrases[lang_code]["tps"])
        stats.total_inspected += 1

        hid = self.check_if_head_intent(intent)

        resource = Resource()
        resource.agent_id = intent.agent_id
        resource.intent_display_name = intent.display_name
        resource.intent_id = intent.resource_id
        resource.resource_type = "intent"

        if hid and n_tps < 50:
            rule = "R005: Head Intent Does Not Have Minimum Training Phrases."
            message = f": {lang_code} : ({n_tps} / 50)"

            stats.total_issues += 1
            self.log.generic_logger(resource, rule, message)

        elif n_tps < 20:
            rule = "R005: Intent Does Not Have Minimum Training Phrases."
            message = f": {lang_code} : ({n_tps} / 20)"

            stats.total_issues += 1
            self.log.generic_logger(resource, rule, message)

        return stats

    def run_training_phrase_rules(
        self,
        intent: Intent,
        lang_code: str,
        stats: LintStats) -> LintStats:
        """Checks and Executes all Intent/Training Phrase level rules.
        
        The requirements for a rule in this section are:
          - Intent must have at least 1 langauge_code file
          - Intent must have at least 1 training phrase
        """

        # intent-min-tps
        if self.disable_map.get("intent-min-tps", True):
            stats = self.min_tps_head_intent(intent, lang_code, stats)

        return stats
