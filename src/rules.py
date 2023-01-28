"""Rule Definitions for CX Lint."""

import logging
import re
import os

from typing import Union, List
from rich.logging import RichHandler
from rich.console import Console
from rich.markdown import Markdown

console = Console(log_time=False, log_path=False, width=200, color_system='truecolor')

keywords = ['Flows Directory', 'Entity Types Directory', 'Test Cases Directory', 'Intents Directory']
handler = RichHandler(
    enable_link_path=False,
    keywords=keywords,
    show_time=False,
    show_level=False,
    show_path=False,
    tracebacks_word_wrap=False)

# logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[handler],
    force=True
    )

class RulesDefinitions:
    """All rule definitions used by CX Lint."""

    @staticmethod
    def create_link(resource):
        link = None

        if resource.agent_id and resource.agent_id != '':
            base = 'https://dialogflow.cloud.google.com/cx/'

            if resource.resource_type == 'fulfillment':
                link_map = {
                    'fulfillment': f'/flows/{resource.page.flow.resource_id}'\
                        f'/flow_creation?pageId={resource.page.resource_id}'
                        }

            else:
                link_map = {
                    'test_case': f'/testCases/{resource.resource_id}',
                    'intent': f'/intents?id={resource.resource_id}',
                    'entity_type': f'/entityTypes?id={resource.resource_id}'
                    }

            path = link_map.get(resource.resource_type, None)
            link = base + resource.agent_id + path

        return link

    @staticmethod
    def check_if_head_intent(intent):
        """Checks if Intent is Head Intent based on labels and name."""
        hid = False

        if 'head' in intent.display_name:
            hid = True

        return hid

    @staticmethod
    def entity_regex_matching(data: Union[List[str],str], pattern: str):
        """Checks Entities and synonyms for issues based on regex pattern."""
        issue_found = False

        if isinstance(data, str):
            data_match = re.search(pattern, data, flags=re.IGNORECASE)

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

    def generic_logger(self, resource, rule, message) -> None:
        """Generic Logger for various resources."""
        url = self.create_link(resource)

        if resource.resource_type == 'fulfillment':
            flow = resource.page.flow.display_name
            link = f'[link={url}]{flow} : {resource.display_name}[/link]'
        else:
            link = f'[link={url}]{resource.display_name}[/link]'

        if resource.verbose:
            output = f'{rule} : {link} : {message}'

        else:
            output = f'{rule} : {link}'

        console.log(output)


    # RESPONSE MESSAGE RULES
    # closed-choice-alternative
    def closed_choice_alternative_parser(self, route, stats) -> object:
        """Identifies a Closed Choice Alternative Question."""
        rule = 'R001: Closed-Choice Alternative Missing Intermediate `?` '\
            '(A? or B.)'
        message = f'{route.trigger}'

        pattern = r'^(What|Where|When|Who|Why|How|Would) (.*) or (.*)\?$'

        match = re.search(pattern, route.text, flags=re.IGNORECASE)

        if match:
            stats.total_issues += 1
            self.generic_logger(route, rule, message)

        return stats

    # wh-questions
    def wh_questions(self, route, stats) -> object:
        """Identifies a Wh- Question and checks for appropriate punctuation."""
        rule = 'R002: Wh- Question Should Use `.` Instead of `?` Punctuation'
        message = f'{route.trigger}'

        pattern = r'^(what|when|where|who|why|how)\b.*\?$'

        match = re.search(pattern, route.text, flags=re.IGNORECASE)

        if match and 'event' not in route.trigger:
            stats.total_issues += 1
            self.generic_logger(route, rule, message)

        return stats

    # clarifying-questions
    def clarifying_questions(self, route, stats) -> object:
        """Identifies Clarifying Questions that are missing `?` Punctuation."""
        rule = 'R003: Clarifying Question Should Use `?` Punctuation'
        message = f'{route.trigger}'

        # updated pattern
        pattern = r'^(what|when|where|who|why|how)\b.*\.$'

        match = re.search(pattern, route.text, flags=re.IGNORECASE)

        if match and 'event' in route.trigger:
            stats.total_issues += 1
            self.generic_logger(route, rule, message)

        return stats


    # INTENT RULES
    # intent-missing-tps
    def missing_training_phrases(self, intent, stats) -> object:
        """Checks for Intents that are Missing Training Phrases"""
        rule = 'R004: Intent is Missing Training Phrases.'
        message = ''

        stats.total_inspected += 1
        stats.total_issues += 1
        self.generic_logger(intent, rule, message)

        return stats

    # intent-min-tps
    def min_tps_head_intent(self, intent, lang_code, stats) -> object:
        """Determines if Intent has min recommended training phrases"""
        n_tps = len(intent.training_phrases[lang_code]['tps'])
        stats.total_inspected += 1

        hid = self.check_if_head_intent(intent)

        if hid and n_tps < 50:
            rule = 'R005: Head Intent Does Not Have Minimum Training Phrases.'
            message = f'({n_tps} / 50)'

            stats.total_issues += 1
            self.generic_logger(intent, rule, message)

        elif n_tps < 20:
            rule = 'R005: Intent Does Not Have Minimum Training Phrases.'
            message =  f'({n_tps} / 20)'

            stats.total_issues += 1
            self.generic_logger(intent, rule, message)

        return stats

    # intent-missing-metadata
    def intent_missing_metadata(self, intent, stats) -> object:
        """Flags Intent that has missing metadata file."""
        rule = 'R010: Missing Metadata file for Intent'
        message = ''

        stats.total_inspected += 1
        stats.total_issues += 1

        self.generic_logger(intent, rule, message)

        return stats

    # TEST CASE RULES
    # explicit-tps-in-test-cases
    def explicit_tps_in_tcs(self, tc, stats) -> object:
        """Checks that user utterance is an explicit intent training phrase."""
        rule = 'R007: Explicit Training Phrase Not in Test Case'
        
        for pair in tc.intent_data:
            stats.total_inspected += 1

            intent = pair['intent']
            phrase = pair['user_utterance']
            tps = pair['training_phrases']

            if phrase not in pair['training_phrases']:
                message = f'[Utterance: {phrase} | Intent: {intent}]'

                stats.total_issues += 1
                self.generic_logger(tc, rule, message)

        return stats

    # invalid-intent-in-test-cases
    def invalid_intent_in_tcs(self, tc, stats) -> object:
        """Check that a listed Intent in the Test Case exists in the agent."""
        rule = 'R008: Invalid Intent in Test Case'

        for pair in tc.intent_data:
            if pair['status'] == 'invalid_intent':
                stats.total_inspected += 1
                stats.total_issues += 1

                intent = pair['intent']
                phrase = pair['user_utterance']

        message = ''
        self.generic_logger(tc, rule, message)

        return stats

    # ENTITY TYPE RULES
    # yes-no-entities
    def yes_no_entities(self, etype, lang_code, stats) -> object:
        """Check that yes/no entities are not present in the agent."""
        yes_no = ['yes', 'no']
        issue_found = False
        stats.total_inspected += 1

        for entity in etype.entities[lang_code]['entities']:
            value = entity['value']
            synonyms = entity['synonyms']

            pattern = r'^(?:yes|no)$'

            issue_found = self.entity_regex_matching(value, pattern)

            value_match = re.search(pattern, value, flags=re.IGNORECASE)
            if value_match:
                issue_found = True

            issue_found = self.entity_regex_matching(synonyms, pattern)

            if issue_found:
                stats.total_issues += 1
                rule = 'R009: Yes/No Entities Present in Agent'
                message = f'{etype.kind}'
                self.generic_logger(etype, rule, message)

        return stats
