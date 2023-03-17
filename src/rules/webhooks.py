"""Webhook Rules and Definitions."""

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
from resources.types import Webhook, LintStats, Resource

from rules.logger import RulesLogger

class WebhookRules:
    """Webhook Rules and Definitions."""
    def __init__(
            self,
            console,
            disable_map: Dict[str, Any]):

        self.console = console
        self.disable_map = disable_map
        self.log = RulesLogger(console=console)

    # naming-conventions
    def webhook_naming_conventions(
        self, webhook: Webhook, stats: LintStats) -> LintStats:
        """Check the Webhook Display Name conforms to naming convention."""
        rule = "R015: Naming Conventions"

        if webhook.naming_pattern:
            res = re.search(webhook.naming_pattern, webhook.display_name)

            stats.total_inspected += 1

        if not res:
            resource = Resource()
            resource.agent_id = webhook.agent_id
            resource.webhook_display_name = webhook.display_name
            resource.webhook_id = webhook.resource_id
            resource.resource_type = "webhook"

            message = ": Webhook Display Name does not meet the specified"\
                f" Naming Convention : {webhook.naming_pattern}"
            stats.total_issues += 1

            self.log.generic_logger(resource, rule, message)

        return stats

    def run_webhook_rules(
        self, webhook: Webhook, stats: LintStats) -> LintStats:
        """Checks and Executes all Webhook level rules."""

        # naming-conventions
        if self.disable_map.get("naming-conventions", True):
            stats = self.webhook_naming_conventions(webhook, stats)

        return stats
