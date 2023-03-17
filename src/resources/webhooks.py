"""Webhook linter methods and functions."""

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

import json
import os

from configparser import ConfigParser

from common import Common
from rules.webhooks import WebhookRules
from resources.types import Webhook, LintStats

class Webhooks:
    """Webhook linter methods and functions."""

    def __init__(self, verbose: bool, config: ConfigParser, console):
        self.verbose = verbose
        self.console = console
        self.config = config
        self.agent_id = Common.load_agent_id(config)
        self.disable_map = Common.load_message_controls(config)
        self.naming_conventions = Common.load_naming_conventions(config)

        self.rules = WebhookRules(console, self.disable_map)

    @staticmethod
    def build_webhook_path_list(agent_local_path: str):
        """Builds a list of webhook file locations."""
        root_dir = agent_local_path + "/webhooks"

        webhook_paths = []

        for webhook_file in os.listdir(root_dir):
            webhook_file_path = f"{root_dir}/{webhook_file}"
            webhook_paths.append(webhook_file_path)

        return webhook_paths

    @staticmethod
    def get_service_type(webhook: Webhook) -> str:
        """Get the type of Webhook Service that is cofigured."""
        if "genericWebService" in webhook.data:
            webhook.service_type = "Generic Web Service"

        else:
            webhook.service_type = "Other"

        return webhook.service_type

    def lint_webhook(self, webhook: Webhook, stats: LintStats) -> LintStats:
        """Lint a single Webhook file."""

        with open(webhook.dir_path, "r", encoding="UTF-8") as webhook_file:
            webhook.data = json.load(webhook_file)
            webhook.resource_id = webhook.data.get("name", None)
            webhook.display_name = webhook.data.get("displayName", None)
            webhook.timeout = webhook.data.get(
                "timeout", None).get("seconds", None)
            webhook.service_type = self.get_service_type(webhook)

            webhook_file.close()

        stats = self.rules.run_webhook_rules(webhook, stats)

        return stats

    def lint_webhooks_directory(self, agent_local_path: str):
        """Linting the top level Webhooks Dir in the JSON Package structure.

        The following files exist under the `webhooks` dir:
        - <webhook-name>.json
        """
        start_message = f'{"#" * 10} Begin Webhooks Directory Linter'
        self.console.log(start_message)

        stats = LintStats()

        # Create a list of all Webhook paths to iter through
        webhook_paths = self.build_webhook_path_list(agent_local_path)

        # Linting Starts Here
        for webhook_path in webhook_paths:
            webhook = Webhook()
            webhook.verbose = self.verbose
            webhook.agent_id = self.agent_id
            webhook.dir_path = webhook_path
            webhook.naming_pattern = self.naming_conventions.get(
                "webhook_name", None)

            stats = self.lint_webhook(webhook, stats)

        header = "-" * 20
        rating = Common.calculate_rating(
            stats.total_issues, stats.total_inspected
        )

        end_message = (
            f"\n{header}\n{stats.total_intents} Webhooks linted."
            f"\n{stats.total_issues} issues found out of "
            f"{stats.total_inspected} inspected."
            f"\nYour Agent Webhooks rated at {rating:.2f}/10\n\n"
        )
        self.console.log(end_message)
