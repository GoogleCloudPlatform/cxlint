"""Rule Definitions for CX Lint."""

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

from typing import Union, List
from resources.types import EntityType, Flow, Fulfillment, Intent, LintStats, Page, Resource, TestCase

class RulesDefinitions:
    """All rule definitions used by CX Lint."""
    def __init__(self, console):
        self.console = console

    @staticmethod
    def create_link(resource):
        link = None

        if resource.agent_id and resource.agent_id != '':
            base = 'https://dialogflow.cloud.google.com/cx/'

            link_map = {
                'entity_type': f'/entityTypes?id={resource.entity_type_id}',
                'flow': f'/flows/{resource.flow_id}',
                'fulfillment': f'/flows/{resource.flow_id}'\
                    f'/flow_creation?pageId={resource.page_id}',
                'intent': f'/intents?id={resource.intent_id}',
                'page': f'/flows/{resource.flow_id}'\
                    f'/flow_creation?pageId={resource.page_id}',
                'test_case': f'/testCases/{resource.test_case_id}',

                }

            path = link_map.get(resource.resource_type, None)
            link = base + resource.agent_id + path

        return link

    @staticmethod
    def check_if_head_intent(intent: Intent):
        """Checks if Intent is Head Intent based on labels and name."""
        hid = False

        if 'head' in intent.display_name:
            hid = True

        return hid

    @staticmethod
    def entity_regex_matching(data: Union[List[str],str]):
        """Checks Entities and synonyms for issues based on regex pattern."""
        issue_found = False
        pattern = r'^(?:yes|no)$'

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

    def generic_logger(self, resource: Resource, rule: str, message: str) -> None:
        """Generic Logger for various resources."""
        url = self.create_link(resource)

        link_map = {
            'entity_type': f'[link={url}]{resource.entity_type_display_name}[/link]',
            'flow': f'[link={url}]{resource.flow_display_name}[/link]',
            'fulfillment': f'[link={url}]{resource.flow_display_name} : {resource.page_display_name}[/link]',
            'intent': f'[link={url}]{resource.intent_display_name}[/link]',
            'page': f'[link={url}]{resource.flow_display_name} : {resource.page_display_name}[/link]',
            'test_case': f'[link={url}]{resource.test_case_display_name}[/link]',
            'webhook': f'[link={url}]{resource.webhook_display_name}[/link]',
        }

        final_link = link_map.get(resource.resource_type, None)
        output = f'{rule} : {final_link} {message}'

        self.console.log(output)

    # FLOW RULES
    # unused-pages
    def unused_pages(self, flow: Flow, stats: LintStats) -> LintStats:
        """Checks for Unusued Pages in Flow Graph."""
        rule = 'R012: Unused Pages'

        for page in flow.unused_pages:
            resource = Resource()
            resource.agent_id = flow.agent_id
            resource.flow_display_name = flow.display_name
            resource.flow_id = flow.resource_id
            resource.page_display_name = page
            resource.page_id = flow.data.get(page, None)
            resource.resource_type = 'page'

            message = ''
            stats.total_inspected += 1
            stats.total_issues += 1

            self.generic_logger(resource, rule, message)

        return stats
    
    # dangling-pages
    def dangling_pages(self, flow: Flow, stats: LintStats) -> LintStats:
        """Checks for Dangling Pages in Flow Graph."""
        rule = 'R013: Dangling Pages'

        for page in flow.dangling_pages:
            resource = Resource()
            resource.agent_id = flow.agent_id
            resource.flow_display_name = flow.display_name
            resource.flow_id = flow.resource_id
            resource.page_display_name = page
            resource.page_id = flow.data.get(page, None)
            resource.resource_type = 'page'

            message = ''
            stats.total_inspected += 1
            stats.total_issues += 1

            self.generic_logger(resource, rule, message)

        return stats
    
    # unreachable-pages
    def unreachable_pages(self, flow: Flow, stats: LintStats) -> LintStats:
        """Checks for Unreachable Pages in Flow Graph."""
        rule = 'R014: Unreachable Pages'

        for page in flow.unreachable_pages:
            resource = Resource()
            resource.agent_id = flow.agent_id
            resource.flow_display_name = flow.display_name
            resource.flow_id = flow.resource_id
            resource.page_display_name = page
            resource.page_id = flow.data.get(page, None)
            resource.resource_type = 'page'

            message = ''
            stats.total_inspected += 1
            stats.total_issues += 1

            self.generic_logger(resource, rule, message)

        return stats


    # PAGE RULES
    # missing-webhook-event-handlers
    def missing_webhook_event_handlers(
            self, page: Page, stats: LintStats) -> LintStats:
        """Checks for missing Event Handlers on pages that use Webhooks."""
        rule = 'R011: Missing Webhook Event Handlers'

        stats.total_inspected += 1

        if page.has_webhook and not page.has_webhook_event_handler:
            resource = Resource()
            resource.agent_id = page.agent_id
            resource.flow_display_name = page.flow.display_name
            resource.flow_id = page.flow.resource_id
            resource.page_display_name = page.display_name
            resource.page_id = page.resource_id
            resource.resource_type = 'page'

            message = ''

            stats.total_issues += 1
            self.generic_logger(resource, rule, message)

        return stats


    # RESPONSE MESSAGE RULES
    # closed-choice-alternative
    def closed_choice_alternative_parser(
            self, route: Fulfillment, stats: LintStats) -> LintStats:
        """Identifies a Closed Choice Alternative Question."""
        rule = 'R001: Closed-Choice Alternative Missing Intermediate `?` '\
            '(A? or B.)'
        message = f': {route.trigger}'

        pattern = r'^(What|Where|When|Who|Why|How|Would) (.*) or (.*)\?$'

        match = re.search(pattern, route.text, flags=re.IGNORECASE)

        if match:
            resource = Resource()
            resource.agent_id = route.agent_id
            resource.flow_display_name = route.page.flow.display_name
            resource.flow_id = route.page.flow.resource_id
            resource.page_display_name = route.page.display_name
            resource.page_id = route.page.resource_id
            resource.resource_type = 'fulfillment'

            stats.total_issues += 1
            self.generic_logger(resource, rule, message)

        return stats

    # wh-questions
    def wh_questions(self, route: Fulfillment, stats: LintStats) -> LintStats:
        """Identifies a Wh- Question and checks for appropriate punctuation."""
        rule = 'R002: Wh- Question Should Use `.` Instead of `?` Punctuation'
        message = f': {route.trigger}'

        pattern = r'^(what|when|where|who|why|how)\b.*\?$'

        match = re.search(pattern, route.text, flags=re.IGNORECASE)

        if match and 'event' not in route.trigger:
            resource = Resource()
            resource.agent_id = route.agent_id
            resource.flow_display_name = route.page.flow.display_name
            resource.flow_id = route.page.flow.resource_id
            resource.page_display_name = route.page.display_name
            resource.page_id = route.page.resource_id
            resource.resource_type = 'fulfillment'

            stats.total_issues += 1
            self.generic_logger(resource, rule, message)

        return stats

    # clarifying-questions
    def clarifying_questions(
            self, route: Fulfillment, stats: LintStats) -> LintStats:
        """Identifies Clarifying Questions that are missing `?` Punctuation."""
        rule = 'R003: Clarifying Question Should Use `?` Punctuation'
        message = f': {route.trigger}'

        # updated pattern
        pattern = r'^(what|when|where|who|why|how)\b.*\.$'

        match = re.search(pattern, route.text, flags=re.IGNORECASE)

        if match and 'event' in route.trigger:
            resource = Resource()
            resource.agent_id = route.agent_id
            resource.flow_display_name = route.page.flow.display_name
            resource.flow_id = route.page.flow.resource_id
            resource.page_display_name = route.page.display_name
            resource.page_id = route.page.resource_id
            resource.resource_type = 'fulfillment'

            stats.total_issues += 1
            self.generic_logger(resource, rule, message)

        return stats


    # INTENT RULES
    # intent-missing-tps
    def missing_training_phrases(
            self, intent: Intent, stats: LintStats) -> LintStats:
        """Checks for Intents that are Missing Training Phrases"""
        rule = 'R004: Intent is Missing Training Phrases.'
        message = f': {intent.training_phrases}'

        resource = Resource()
        resource.agent_id = intent.agent_id
        resource.intent_display_name = intent.display_name
        resource.intent_id = intent.resource_id
        resource.resource_type = 'intent'

        stats.total_inspected += 1
        stats.total_issues += 1
        self.generic_logger(resource, rule, message)

        return stats

    # intent-min-tps
    def min_tps_head_intent(
            self,
            intent: Intent,
            lang_code: str,
            stats: LintStats) -> LintStats:
        """Determines if Intent has min recommended training phrases"""
        n_tps = len(intent.training_phrases[lang_code]['tps'])
        stats.total_inspected += 1

        hid = self.check_if_head_intent(intent)

        resource = Resource()
        resource.agent_id = intent.agent_id
        resource.intent_display_name = intent.display_name
        resource.intent_id = intent.resource_id
        resource.resource_type = 'intent'

        if hid and n_tps < 50:
            rule = 'R005: Head Intent Does Not Have Minimum Training Phrases.'
            message = f': {lang_code} : ({n_tps} / 50)'

            stats.total_issues += 1
            self.generic_logger(resource, rule, message)

        elif n_tps < 20:
            rule = 'R005: Intent Does Not Have Minimum Training Phrases.'
            message =  f': {lang_code} : ({n_tps} / 20)'

            stats.total_issues += 1
            self.generic_logger(resource, rule, message)

        return stats

    # intent-missing-metadata
    def intent_missing_metadata(
            self, intent: Intent, stats: LintStats) -> LintStats:
        """Flags Intent that has missing metadata file."""
        rule = 'R010: Missing Metadata file for Intent'
        message = ''

        resource = Resource()
        resource.agent_id = intent.agent_id
        resource.intent_display_name = intent.display_name
        resource.intent_id = intent.resource_id
        resource.resource_type = 'intent'

        stats.total_inspected += 1
        stats.total_issues += 1

        self.generic_logger(resource, rule, message)

        return stats

    # TEST CASE RULES
    # explicit-tps-in-test-cases
    def explicit_tps_in_tcs(self, tc: TestCase, stats: LintStats) -> LintStats:
        """Checks that user utterance is an explicit intent training phrase."""
        rule = 'R007: Explicit Training Phrase Not in Test Case'
        
        for pair in tc.intent_data:
            stats.total_inspected += 1

            intent = pair['intent']
            phrase = pair['user_utterance']
            tps = pair['training_phrases']

            if phrase not in pair['training_phrases']:
                message = f': [Utterance: {phrase} | Intent: {intent}]'

                resource = Resource()
                resource.agent_id = tc.agent_id
                resource.test_case_display_name = tc.display_name
                resource.test_case_id = tc.resource_id
                resource.resource_type = 'test_case'

                stats.total_issues += 1
                self.generic_logger(resource, rule, message)

        return stats

    # invalid-intent-in-test-cases
    def invalid_intent_in_tcs(
            self, tc: TestCase, stats: LintStats) -> LintStats:
        """Check that a listed Intent in the Test Case exists in the agent."""
        rule = 'R008: Invalid Intent in Test Case'

        for pair in tc.intent_data:
            if pair['status'] == 'invalid_intent':
                stats.total_inspected += 1
                stats.total_issues += 1

                intent = pair['intent']
                phrase = pair['user_utterance']

        resource = Resource()
        resource.agent_id = tc.agent_id
        resource.test_case_display_name = tc.display_name
        resource.test_case_id = tc.resource_id
        resource.resource_type = 'test_case'

        message = ''
        self.generic_logger(resource, rule, message)

        return stats

    # ENTITY TYPE RULES
    def _yes_no_entity_check(
            self,
            etype: EntityType,
            entity: str,
            lang_code: str,
            stats: LintStats):
        """Check the Entity inside the Entity Type for yes/no phrases."""
        stats.total_inspected += 1

        issue_found = self.entity_regex_matching(entity)

        if issue_found:
            stats.total_issues += 1
            rule = 'R009: Yes/No Entities Present in Agent'
            message = f': {lang_code} : Entity : {entity}'

            resource = Resource()
            resource.agent_id = etype.agent_id
            resource.entity_type_display_name = etype.display_name
            resource.entity_type_id = etype.resource_id
            resource.resource_type = 'entity_type'

            self.generic_logger(resource, rule, message) 

        return stats
    
    def _yes_no_synonym_check(
            self,
            etype: EntityType,
            synonyms: List[str],
            lang_code: str,
            stats: LintStats):
        """Check the Synonyms of the Entity for yes/no phrases."""
        stats.total_inspected += 1

        issue_found = self.entity_regex_matching(synonyms)

        if issue_found:
            stats.total_issues += 1
            rule = 'R009: Yes/No Entities Present in Agent'
            message = f': {lang_code} : Synonyms : {synonyms}'

            resource = Resource()
            resource.agent_id = etype.agent_id
            resource.entity_type_display_name = etype.display_name
            resource.entity_type_id = etype.resource_id
            resource.resource_type = 'entity_type'

            self.generic_logger(resource, rule, message) 

        return stats

    # yes-no-entities
    def yes_no_entities(
            self,
            etype: EntityType,
            lang_code: str,
            stats: LintStats) -> LintStats:
        """Check that yes/no Entities or Synonyms aren't used in the agent."""
        for entity in etype.entities[lang_code]['entities']:
            value = entity['value']
            synonyms = entity['synonyms']

            stats = self._yes_no_entity_check(etype, value, lang_code, stats)
            stats = self._yes_no_synonym_check(
                etype, synonyms, lang_code, stats)

        return stats
