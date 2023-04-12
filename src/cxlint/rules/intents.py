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

import re

from typing import Dict, Any, List, Union
from cxlint.resources.types import Intent, LintStats, Resource

from cxlint.rules.logger import RulesLogger

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
    def check_if_head_intent(intent: Intent) -> bool:
        """Checks if Intent is Head Intent based on labels and name."""
        hid = False

        if "head" in intent.display_name:
            hid = True

        return hid

    @staticmethod
    def check_if_confirmation_intent(tps: List[str]) -> bool:
        """Check if the Intent contains yes/no phrases for confirmation."""
        confirm = False
        confirm_set = set(["yes", "no"])

        res = confirm_set.intersection(set(tps))
        if res:
            confirm = True

        return confirm

    @staticmethod
    def check_if_escalation_intent(tps: List[str]) -> bool:
        """Check if the Intent contains escalation phrases."""
        escalate = False
        escalate_set = set(["escalate", "operator"])

        res = escalate_set.intersection(set(tps))
        if res:
            escalate = True

        return escalate

    @staticmethod
    def flatten_training_phrase_parts(parts: Dict[str, Any]) -> List[str]:
        """Flatten the Training Phrase Parts proto to list of strings."""

        # If the TP Part has more than 1 part, we need to extract and
        # concat the data into a single string
        if len(parts) > 1:
            utterance = ""
            for part in parts:
                utterance += part.get("text", "")

        # Otherwise, there's just 1 part so we can take it as-is
        else:
            utterance = parts[0].get("text", None)

        return utterance

    def gather_training_phrases(
        self, intent: Intent, lang_code: str) -> List[str]:
        """Flatten the Training Phrase proto to a list of strings."""
        tps_flat = []
        tps_original = intent.training_phrases.get(lang_code, None)["tps"]

        for tp in tps_original:
            parts = tp.get("parts", None)
            utterance = self.flatten_training_phrase_parts(parts)
            tps_flat.append(utterance)

        return tps_flat

    def check_and_log_naming(
        self,
        intent: Intent,
        stats: LintStats,
        res: Union[re.Match, None],
        pattern: str):
        """Checks for final naming match and calls logger."""
        rule = "R015: Naming Conventions"

        if not res:
            resource = Resource()
            resource.agent_id = intent.agent_id
            resource.intent_display_name = intent.display_name
            resource.intent_id = intent.resource_id
            resource.resource_type = "intent"

            message = ": Intent Display Name does not meet the specified"\
                f" Convention : {pattern}"

            stats.total_issues += 1

            self.log.generic_logger(resource, rule, message)

        return stats

    # naming-conventions
    def intent_naming_convention(
        self,
        intent: Intent,
        lang_code: str,
        stats: LintStats) -> LintStats:
        """Check that the Display Name conforms to naming conventions."""

        hid = self.check_if_head_intent(intent)
        tps = self.gather_training_phrases(intent, lang_code)
        confirm = self.check_if_confirmation_intent(tps)
        escalate = self.check_if_escalation_intent(tps)

        # Head Intents
        if hid and intent.naming_pattern_head:
            pattern = intent.naming_pattern_head
            res = re.search(pattern, intent.display_name)
            stats.total_inspected += 1

            stats = self.check_and_log_naming(intent, stats, res, pattern)

        # Confirmation Intents
        elif confirm and intent.naming_pattern_confirmation:
            pattern = intent.naming_pattern_confirmation
            res = re.search(pattern, intent.display_name)
            stats.total_inspected += 1

            stats = self.check_and_log_naming(intent, stats, res, pattern)

        # Escalation Intents
        elif escalate and intent.naming_pattern_escalation:
            pattern = intent.naming_pattern_escalation
            res = re.search(pattern, intent.display_name)
            stats.total_inspected += 1

            stats = self.check_and_log_naming(intent, stats, res, pattern)

        # Generic Intents
        elif intent.naming_pattern_generic:
            pattern = intent.naming_pattern_generic
            res = re.search(pattern, intent.display_name)
            stats.total_inspected += 1

            stats = self.check_and_log_naming(intent, stats, res, pattern)

        return stats


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

    # extra-display-name-whitespace
    def intent_display_name_extra_whitespaces(
        self,
        intent: Intent,
        stats: LintStats) -> LintStats:
        """Check Intent display name for extra whitespace characters."""
        rule = "R016: Extra Whitespace in Display Name"

        stats.total_inspected += 1

        res = bool(intent.display_name.startswith(" ") or
                   intent.display_name.endswith(" ") or
                   re.search(r"\s{2,}", intent.display_name))

        if res :
            resource = Resource()
            resource.agent_id = intent.agent_id
            resource.intent_display_name = intent.display_name
            resource.intent_id = intent.resource_id
            resource.resource_type = "intent"

            message = ""
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
        # naming-conventions
        if self.disable_map.get("naming-conventions", True):
            stats = self.intent_naming_convention(intent, lang_code, stats)

        # intent-min-tps
        if self.disable_map.get("intent-min-tps", True):
            stats = self.min_tps_head_intent(intent, lang_code, stats)

        # extra-display-name-whitespace
        if self.disable_map.get("extra-display-name-whitespace", True):
            stats = self.intent_display_name_extra_whitespaces(intent, stats)

        return stats
