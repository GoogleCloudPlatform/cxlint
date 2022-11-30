"""Core class and methods for CX Linter."""

import os
import json
import logging

from rules import RulesDefinitions # pylint: disable=E0401

# logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

class CxLint:
    """Core CX Linter methods and functions."""
    def __init__(
        self,
        verbose: bool = False):

        self.rules = RulesDefinitions()

        self.verbose = verbose
        self.current_filepath = None
        self.current_resource = None
        self.total_issues = 0

    def parse_filepath(self, in_path: str, resource_type: str) -> str:
        """Parse file path to provide quick reference for linter log."""

        slice_map = {
            'flow': 6,
            'flows': 6
        }

        self.current_filepath = '/'.join(in_path.split('/')[slice_map[resource_type]:])

        return self.current_filepath

    def collect_transition_route_trigger(self, route):
        """Inspect route and return all Intent/Condition info."""

        if 'intent' in route and 'condition' in route:
            trigger = 'intent+condition'

        elif 'intent' in route:
            if self.verbose:
                trigger = f'intent:{route["intent"]}'
            else:
                trigger = 'intent'

        elif 'condition' in route:
            if self.verbose:
                trigger = f'condition:{route["condition"]}'
            else:
                trigger = 'condition'

        return trigger

    def get_trigger_info(self, resource, primary_key):
        """Extract trigger info from route based on primary key."""

        if primary_key == 'eventHandlers':
            trigger = f'event:{resource["event"]}'

        if primary_key == 'transitionRoutes':
            intent_condition = self.collect_transition_route_trigger(resource)
            trigger = f'route:{intent_condition}'

        return trigger


    def fulfillment_linter(self, trigger, text: str) -> str:
        """Runs through all fulfillment lint rules."""

        resource = self.current_resource
        verbose = self.verbose
        total_issues = 0

        # Closed-Choice Alternative
        total_issues += self.rules.closed_choice_alternative_parser(
            resource, trigger, text, verbose)

        return total_issues

    def process_fulfillments(self, resource, primary_key: str):
        """Parse through Fulfillments structure"""
        t2_key = 'triggerFulfillment'
        t3_key = 'messages'
        total_issues = 0
        total_inspected = 0

        if primary_key in resource:
            for route in resource[primary_key]:
                trigger = self.get_trigger_info(route, primary_key)
                path = route.get(t2_key, None)

                if path and t3_key in path:
                    for item in path[t3_key]:
                        if 'text' in item:
                            for text in item['text']['text']:
                                total_inspected += 1
                                # At this point, we can capture and store all the text elements for later processing
                                # Perhaps we build a map of protos that contain all the data nicely wrapped up that we can iter over?
                                # TODO (pmarlow) consider implementing a Fulfillment class that can store all these items in an object
                                total_issues += self.fulfillment_linter(trigger, text)

        return total_issues, total_inspected

    def lint_flow_objects(self, agent_local_path: str):
        """Linting of the Flow objects only.

        In Dialogflow CX, the START_PAGE of each Flow is a special kind of Page
        that exists within the Flow object itself. This specific method will
        lint only these portions of the agent.
        """
        start_message = f'{"*" * 10} Begin Flow Linter'
        logging.info(start_message)

        total_issues = 0
        total_inspected = 0

        flows_path = agent_local_path + '/flows'

        for flow_dir in os.listdir(flows_path):
            start_page_flow_file = flow_dir + '.json'
            start_page_path = f'{flows_path}/{flow_dir}/{start_page_flow_file}'

            with open(start_page_path, 'r', encoding='UTF-8') as flow_file:
                data = json.load(flow_file)

                self.current_resource = f'{flow_dir}:START_PAGE'

                local_issues, local_inspected = self.process_fulfillments(data, 'eventHandlers', )
                total_issues += local_issues
                total_inspected += local_inspected

                local_issues, local_inspected = self.process_fulfillments(data, 'transitionRoutes')
                total_issues += local_issues
                total_inspected += local_inspected

        end_message = f'\n{"-" * 20}\n{len(os.listdir(flows_path))} Flows linted.'\
            f'\n{total_issues} issues out of {total_inspected} inspected.'\
            f'\nYour Agent Flows rated at {(1-(total_issues/total_inspected))*10:.2f}/10.0'\
            '\n\n'
        logging.info(end_message)

    def lint_page_objects(self, agent_local_path: str):
        """Linting all Page objects."""
        start_message = f'{"*" * 10} Begin Page Linter'
        logging.info(start_message)

        total_pages = 0
        total_issues = 0
        total_inspected = 0

        flows_path = agent_local_path + '/flows'

        # iter through each flow
        for flow in os.listdir(flows_path):

            # in a single flow dir, set the path for that flow's pages
            # then iter through all of those pages in the flow
            flow_dir = f'{flows_path}/{flow}'

            # some flows may not contain pages
            if 'pages' in os.listdir(flow_dir):

                # iter through pages if they exist
                pages_path = f'{flow_dir}/pages'
                for page in os.listdir(pages_path):
                    page_path = f'{pages_path}/{page}'

                    with open(page_path, 'r', encoding='UTF-8') as page_file:
                        data = json.load(page_file)

                        self.current_resource = f'{flow}:{page.rstrip(".json")}'

                        local_issues, local_inspected = self.process_fulfillments(data, 'eventHandlers')
                        total_issues += local_issues
                        total_inspected += local_inspected

                        local_issues, local_inspected = self.process_fulfillments(data, 'transitionRoutes')
                        total_issues += local_issues
                        total_inspected += local_inspected

                total_pages += len(os.listdir(pages_path))

        end_message = f'\n{"-" * 20}\n{total_pages} Pages linted.'\
            f'\n{total_issues} issues out of {total_inspected} inspected.'\
            f'\nYour Agent Pages rated at {(1-(total_issues/total_inspected))*10:.2f}/10.0'\
            '\n\n'

        logging.info(end_message)


# TODO: pmarlow - Build another class to traverse different file trees.
# Input: Type of file tree corresponding w/resource name (i.e. intents, testCases, etc.)
# Output: Root file path to start for traversal

    # def get_root_traversal_path(self, resource_type: str):
    #     """Provide resource name and get root traversal path."""
    #     if resource_type == 'flow':
    #         base_path = agent_path + 

    # def find_broken_intents(self, agent_path: str):
    #     base_path = agent_path + '/intents'
    #     for intent_dir in os.listdir(base_path):
    #         for tp_dir in os.listdir(base_path + f'/{intent_dir}'):
