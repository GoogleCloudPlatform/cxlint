"""Entity Type Rules and Definitions."""

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
from resources.types import EntityType, LintStats, Resource

from rules.logger import RulesLogger

class EntityTypeRules:
    """Entity Type Rules and Definitions."""
    def __init__(
            self,
            console,
            disable_map: Dict[str, Any]):

        self.console = console
        self.disable_map = disable_map
        self.log = RulesLogger(console=console)

    @staticmethod
    def entity_regex_matching(data: Union[List[str], str]) -> bool:
        """Checks Entities and synonyms for issues based on regex pattern."""
        issue_found = False
        pattern = r"^(?:yes|no)$"

        # Checks the individual Entity key
        if isinstance(data, str):
            data_match = re.search(pattern, data, flags=re.IGNORECASE)
            if data_match:
                issue_found = True

        # Checks the list of synonyms if available
        elif isinstance(data, List):
            n = len(data)
            i = 0
            while i != n:
                data_match = re.search(pattern, data[i], flags=re.IGNORECASE)
                if data_match:
                    issue_found = True
                    break

                i += 1

        return issue_found

    def _yes_no_entity_check(
            self,
            etype: EntityType,
            entity: str,
            lang_code: str,
            stats: LintStats) -> LintStats:
        """Check the Entity inside the Entity Type for yes/no phrases."""
        stats.total_inspected += 1

        issue_found = self.entity_regex_matching(entity)

        if issue_found:
            stats.total_issues += 1
            rule = "R009: Yes/No Entities Present in Agent"
            message = f": {lang_code} : Entity : {entity}"

            resource = Resource()
            resource.agent_id = etype.agent_id
            resource.entity_type_display_name = etype.display_name
            resource.entity_type_id = etype.resource_id
            resource.resource_type = "entity_type"

            self.log.generic_logger(resource, rule, message)

        return stats

    def _yes_no_synonym_check(
        self,
        etype: EntityType,
        synonyms: List[str],
        lang_code: str,
        stats: LintStats) -> LintStats:
        """Check the Synonyms of the Entity for yes/no phrases."""
        stats.total_inspected += 1

        issue_found = self.entity_regex_matching(synonyms)

        if issue_found:
            stats.total_issues += 1
            rule = "R009: Yes/No Entities Present in Agent"
            message = f": {lang_code} : Synonyms : {synonyms}"

            resource = Resource()
            resource.agent_id = etype.agent_id
            resource.entity_type_display_name = etype.display_name
            resource.entity_type_id = etype.resource_id
            resource.resource_type = "entity_type"

            self.log.generic_logger(resource, rule, message)

        return stats

    # naming-conventions
    def entity_type_naming_convention(
        self,
        etype: EntityType,
        stats: LintStats) -> LintStats:
        """Check that the Entity Type display name conform to given pattern."""
        rule = "R015: Naming Conventions"

        if etype.naming_pattern:
            res = re.search(etype.naming_pattern, etype.display_name)

            stats.total_inspected += 1

        if not res:
            resource = Resource()
            resource.agent_id = etype.agent_id
            resource.entity_type_display_name = etype.display_name
            resource.entity_type_id = etype.resource_id
            resource.resource_type = "entity_type"

            message = ": Entity Type Display Name does not meet the specified"\
                f" Convention : {etype.naming_pattern}"
            stats.total_issues += 1

            self.log.generic_logger(resource, rule, message)

        return stats

    # extra-display-name-whitespace
    def entity_display_name_extra_whitespaces(
        self,
        etype: EntityType,
        stats: LintStats) -> LintStats:
        """Check Entity display name for extra whitespace characters."""
        rule = "R016: Extra Whitespace in Display Name"

        stats.total_inspected += 1

        res = bool(etype.display_name.startswith(" ") or
                   etype.display_name.endswith(" ") or
                   re.search(r"\s{2,}", etype.display_name))

        if res :
            resource = Resource()
            resource.agent_id = etype.agent_id
            resource.entity_type_display_name = etype.display_name
            resource.entity_type_id = etype.resource_id
            resource.resource_type = "entity_type"

            message = ""
            stats.total_issues += 1

            self.log.generic_logger(resource, rule, message)

        return stats

    # yes-no-entities
    def yes_no_entities(
        self,
        etype: EntityType,
        lang_code: str,
        stats: LintStats) -> LintStats:
        """Check that yes/no Entities or Synonyms aren't used in the agent."""
        for entity in etype.entities[lang_code]["entities"]:
            value = entity["value"]
            synonyms = entity["synonyms"]

            stats = self._yes_no_entity_check(etype, value, lang_code, stats)
            stats = self._yes_no_synonym_check(
                etype, synonyms, lang_code, stats
            )

        return stats

    def run_entity_type_rules(
        self,
        etype: EntityType,
        lang_code: str,
        stats: LintStats) -> LintStats:
        """Checks and Executes all Entity Type level rules."""
        # naming-conventions
        if self.disable_map.get("naming-conventions", True):
            stats = self.entity_type_naming_convention(etype, stats)

        # yes-no-entities
        if self.disable_map.get("yes-no-entities", True):
            stats = self.yes_no_entities(etype, lang_code, stats)

        # extra-display-name-whitespace
        if self.disable_map.get("extra-display-name-whitespace", True):
            stats = self.entity_display_name_extra_whitespaces(etype, stats)

        return stats
