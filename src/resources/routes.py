"""Fulfillment routes linter methods and functions."""

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

from configparser import ConfigParser
from typing import Dict, Any

from common import Common
from rules import RulesDefinitions
from resources.types import Page, Fulfillment, LintStats, FormParameter


class Fulfillments:
    """Fulfillment routes linter methods and functions."""

    def __init__(self, verbose: bool, config: ConfigParser, console):
        self.verbose = verbose
        self.console = console
        self.config = config
        self.agent_type = Common.load_agent_type(config)
        self.disable_map = Common.load_message_controls(config)
        self.agent_id = Common.load_agent_id(config)
        self.rules = RulesDefinitions(self.console)
        self.route_parameters = {}

    @staticmethod
    def check_for_webhook(page: Page, path: Dict[str, Any]):
        """Check the current route for existence of webhook."""
        if "webhook" in path:
            page.has_webhook = True

    @staticmethod
    def check_for_webhook_event_handlers(route: Fulfillment):
        """Check for Webhook Error Event Handler on Page.

        In this method, we're interested in the following conditions:
         - Page is currently flagged w/webhook = True
         - Page HAS NOT been flagged w/having a webhook error handler
         - The trigger MATCHES the pattern 'webhook.error'

        If a Page and its Route meet all the criteria, we'll flip the bit.
        Otherwise, the webhook handler bit will remain False, causing a rule
        flag."""

        if all(
            [
                route.page.has_webhook,
                not route.page.has_webhook_event_handler,
                "webhook.error" in route.trigger,
            ]
        ):
            route.page.has_webhook_event_handler = True

    def collect_transition_route_trigger(self, route):
        """Inspect route and return all Intent/Condition info."""

        trigger = []
        intent_name = None

        if "intent" in route.data:
            trigger.append("intent")
            intent_name = route.data.get("intent", None)

        if "condition" in route.data:
            trigger.append("condition")

        if len(trigger) > 0:
            trigger = "+".join(trigger)

        if self.verbose and intent_name:
            return f"{trigger} : {intent_name}"

        else:
            return trigger

    def get_trigger_info(self, route):
        """Extract trigger info from route based on primary key."""

        if route.fulfillment_type == "event":
            trigger = f"event : {route.data.get('event', None)}"

        if route.fulfillment_type == "reprompt_handler":
            trigger = f"{route.parameter} : event : "\
                f"{route.data.get('event', None)}"

        if route.fulfillment_type == "transition_route":
            intent_condition = self.collect_transition_route_trigger(route)
            trigger = f"route : {intent_condition}"

        return trigger

    def set_route_group_targets(self, page: Page):
        """Determine Route Targets for Route Group routes."""
        current_page = page.display_name

        for route_group in page.route_groups:
            page.flow.graph.add_edge(current_page, route_group)
            page.flow.graph.add_used_node(route_group)

        return page

    def set_route_targets(self, route: Fulfillment):
        """Determine the Route Targets for the specified route.

        Primary function is to build out the graph structure for the
        Flow based on the current page and where the routes are pointing to.
        The graph structure can then be traversed later to determine any errors
        or inconsistencies in design.
        """
        current_page = route.page.display_name

        route.target_flow = route.data.get("targetFlow", None)
        route.target_page = route.data.get("targetPage", None)

        if route.target_page:
            route.page.flow.graph.add_edge(current_page, route.target_page)
            route.page.flow.graph.add_used_node(route.target_page)

        if route.target_flow:
            route.page.flow.graph.add_edge(
                current_page, f"FLOW: {route.target_flow}"
            )
            route.page.flow.graph.add_used_node(f"FLOW: {route.target_flow}")

        return route

    def update_route_parameters(self, route: Fulfillment, item: Dict[str, str]):
        """Update the Route Parameters map based on new info."""
        flow_name = route.page.flow.display_name
        page_name = route.page.display_name

        flow_data = self.route_parameters.get(flow_name, None)
        page_data = None

        if flow_data:
            page_data = flow_data.get(page_name, None)

        # Flow and Page already exists, append to existing list.
        if page_data:
            self.route_parameters[flow_name][page_name].append(item)

        # Flow data exists, but not Page, so only create the Page list.
        elif flow_data and not page_data:
            self.route_parameters[flow_name][page_name] = [item]

        # Neither the Flow or Page data exists, so create it all.
        else:
            self.route_parameters[flow_name] = {page_name: [item]}

    def lint_agent_responses(self, route: Fulfillment, stats: LintStats) -> str:
        """Executes all Text-based Fulfillment linter rules."""
        voice = False
        route.verbose = self.verbose

        if self.agent_type == "voice":
            voice = True

        # closed-choice-alternative
        if self.disable_map.get("closed-choice-alternative", True) and voice:
            stats = self.rules.closed_choice_alternative_parser(route, stats)

        # wh-questions
        if self.disable_map.get("wh-questions", True) and voice:
            stats = self.rules.wh_questions(route, stats)

        # clarifying-questions
        if self.disable_map.get("clarifying-questions", True) and voice:
            stats = self.rules.clarifying_questions(route, stats)

        return stats

    def lint_fulfillment_type(
        self, stats: LintStats, route: Fulfillment, path: object, key: str
    ):
        """Parse through specific fulfillment types and lint."""
        fulfillment_data = path.get(key, None)

        if fulfillment_data:
            for item in fulfillment_data:
                # This is where each message type will exist
                # text, custom payload, etc.

                # TODO pmarlow: create sub-method parsers per type
                if "text" in item:
                    for text in item["text"]["text"]:
                        stats.total_inspected += 1
                        route.text = text

                        stats = self.lint_agent_responses(route, stats)

                if "parameter" in item:
                    self.update_route_parameters(route, item)

        return stats

    def lint_reprompt_handlers(self, fp: FormParameter, stats: LintStats):
        """Lint for Reprompt Event Handlers inside Form parameters.

        While Reprompt Event Handlers are technically Events, they differ from
        standard Page level Events because they act on the FormParameter data
        structure, not Fulfillment Route data structure as standard Events do.
        """
        if not fp.reprompt_handlers:
            return stats

        for handler in fp.reprompt_handlers:
            route = Fulfillment(page=fp.page)
            route.data = handler
            route.agent_id = fp.page.agent_id
            route.fulfillment_type = "reprompt_handler"
            route.parameter = fp.display_name
            route.trigger = self.get_trigger_info(route)
            route = self.set_route_targets(route)
            path = route.data.get("triggerFulfillment", None)
            event = route.data.get("event", None)

            if not path and not event:
                continue

            # Flag for Webhook Handler
            self.check_for_webhook(fp.page, path)

            stats = self.lint_fulfillment_type(stats, route, path, "messages")

        return stats

    def lint_events(self, page: Page, stats: LintStats):
        """Parse through all Page Event Handlers and lint."""
        if not page.events:
            return stats

        for route_data in page.events:
            route = Fulfillment(page=page)
            route.data = route_data
            route.agent_id = page.agent_id
            route.fulfillment_type = "event"
            route.trigger = self.get_trigger_info(route)
            route = self.set_route_targets(route)
            path = route.data.get("triggerFulfillment", None)
            event = route.data.get("event", None)

            if not path and not event:
                continue

            # Flag for Webhook Handler
            self.check_for_webhook_event_handlers(route)

            stats = self.lint_fulfillment_type(stats, route, path, "messages")

        return stats

    def lint_routes(self, page: Page, stats: LintStats):
        """Parse through all Transition Routes and lint."""
        tf_key = "triggerFulfillment"

        if not page.routes:
            return stats

        for route_data in page.routes:
            route = Fulfillment(page=page)
            route.data = route_data
            route.agent_id = page.agent_id
            route.fulfillment_type = "transition_route"
            route.trigger = self.get_trigger_info(route)
            route = self.set_route_targets(route)

            path = route.data.get(tf_key, None)

            if not path:
                continue

            # Flag for Webhook Handler
            self.check_for_webhook(page, path)

            stats = self.lint_fulfillment_type(stats, route, path, "messages")

            # Preset Params can be linted here
            stats = self.lint_fulfillment_type(
                stats, route, path, "setParameterActions"
            )

        return stats

    def lint_entry(self, page: Page, stats: LintStats):
        """Lint Entry Fulfillment on a single page file.

        The Entry Fulfillment to a Page only has 1 "route" (i.e. itself) so
        there is no need to loop through multiple routes, as they don't
        exist for Entry Fulfillment.
        """

        if not page.entry:
            return stats

        route = Fulfillment(page=page)
        route.data = page.entry
        route.agent_id = page.agent_id
        route.fulfillment_type = "entry"
        route.trigger = "entry"
        path = route.data

        self.check_for_webhook(page, path)

        stats = self.lint_fulfillment_type(stats, route, path, "messages")

        return stats
