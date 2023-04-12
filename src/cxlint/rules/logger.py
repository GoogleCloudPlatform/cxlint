"""Common Logger for Rules Definitions"""

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

from cxlint.resources.types import Resource

class RulesLogger:
    """Common Logger for Rules output."""
    def __init__(
            self,
            console):

        self.console = console

    @staticmethod
    def create_link(resource):
        link = None

        if resource.agent_id and resource.agent_id != "":
            base = "https://dialogflow.cloud.google.com/cx/"

            link_map = {
                "entity_type": f"/entityTypes?id={resource.entity_type_id}",
                "flow": f"/flows/{resource.flow_id}",
                "fulfillment": f"/flows/{resource.flow_id}"
                f"/flow_creation?pageId={resource.page_id}",
                "intent": f"/intents?id={resource.intent_id}",
                "page": f"/flows/{resource.flow_id}"
                f"/flow_creation?pageId={resource.page_id}",
                "test_case": f"/testCases/{resource.test_case_id}",
                "webhook": f"/webhooks/{resource.webhook_id}"
            }

            path = link_map.get(resource.resource_type, None)
            link = base + resource.agent_id + path

        return link

    def generic_logger(
        self, resource: Resource, rule: str, message: str
    ) -> None:
        """Generic Logger for various resources."""
        url = self.create_link(resource)

        link_map = {
            "entity_type": f"[link={url}]"\
                f"{resource.entity_type_display_name}[/link]",
            "flow": f"[link={url}]{resource.flow_display_name}[/link]",
            "fulfillment": f"[link={url}]{resource.flow_display_name} : "\
                f"{resource.page_display_name}[/link]",
            "intent": f"[link={url}]{resource.intent_display_name}[/link]",
            "page": f"[link={url}]{resource.flow_display_name} : "\
                f"{resource.page_display_name}[/link]",
            "test_case": f"[link={url}]"\
                f"{resource.test_case_display_name}[/link]",
            "webhook": f"[link={url}]{resource.webhook_display_name}[/link]",
        }

        final_link = link_map.get(resource.resource_type, None)
        output = f"{rule} : {final_link} {message}"

        self.console.log(output)
