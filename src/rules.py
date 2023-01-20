"""Rule Definitions for CX Lint."""

import logging
import re
import os


# logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

class RulesDefinitions:
    """All rule definitions used by CX Lint."""

    @staticmethod
    def create_link(resource):
        base = 'https://dialogflow.cloud.google.com/cx/'
        link = None

        if resource.resource_type == 'fulfillment':
            link_map = {
                'fulfillment': f'/flows/{resource.page.flow.resource_id}/flow_creation?'\
                    f'pageId={resource.page.resource_id}'
                    }

        else:
            link_map = {
                'test_case': f'/testCases/{resource.resource_id}',
                'intent': f'/intents?id={resource.resource_id}'
                }

        if resource.agent_id != '':
            link = base + resource.agent_id + link_map[resource.resource_type]

        return link

    def page_logger_output(self, resource, message: str) -> None:
        """Consolidated logging method for Page rules."""
        link = self.create_link(resource)

        # https://dialogflow.cloud.google.com/cx/{agent_id}/flows/468aa549-ae58-46a5-b9ca-a8ef30b4771f/flow_creation?pageId=c4b66bc4-71dc-4732-a8e6-23ddfdf2dd18
        if resource.verbose and link:
            logging.info(
                '%s:%s:%s: \n%s: \n%s\n%s\n',
                resource.page.flow.display_name,
                resource.page.display_name,
                resource.trigger,
                message,
                resource.text,
                link)

        elif resource.verbose:
            logging.info(
                '%s:%s:%s: \n%s: \n%s\n',
                resource.page.flow.display_name,
                resource.page.display_name,
                resource.trigger,
                message,
                resource.text)

        else:
            logging.info(
                '%s:%s:%s: %s',
                resource.page.flow.display_name,
                resource.page.display_name,
                resource.trigger,
                message)

    def intent_logger_output(self, intent, message: str) -> None:
        """Consolidated logging method for Intent rules."""
        link = None
        if intent.agent_id:
            link = self.create_link(intent)

        if intent.verbose and link:
            logging.info(
                '%s:%s\n%s\n',
                intent.display_name,
                message,
                link)
    
        elif intent.verbose:
            logging.info(
                '%s:%s',
                intent.display_name,
                message)
        else:
            logging.info(
                '%s:%s',
                intent.display_name,
                message)

    def test_case_logger_output(
        self, tc, phrase: str, intent: str, message: str) -> None:
        """Consolidated logging method for Test Case rules."""
        link = None
        
        if tc.agent_id:
            link = self.create_link(tc)

        if tc.verbose and link:
            logging.info(
                '%s \nTraining Phrase: %s \nIntent: %s\n%s\n%s\n',
                tc.display_name,
                phrase,
                intent,
                message,
                link)

        elif tc.verbose:
            logging.info(
                '%s \nTraining Phrase: %s \nIntent: %s\n%s\n',
                tc.display_name,
                phrase,
                intent,
                message)

        else:
            logging.info(
                '%s:%s',
                tc.display_name,
                message)

    @staticmethod
    def check_if_head_intent(intent):
        """Checks if Intent is Head Intent based on labels and name."""
        hid = False

        if 'head' in intent.display_name:
            hid = True

        return hid

    # RESPONSE MESSAGE RULES
    # closed-choice-alternative
    def closed_choice_alternative_parser(self, route, stats) -> object:
        """Identifies a Closed Choice Alternative Question."""
        message = 'R001: Closed-Choice Alternative Missing Intermediate `?` '\
            '(A? or B.)'

        # pattern = r'(\sare\s|\sdo\s|should\s|\swill\s|what).*\sor\s.*'

        # updated pattern
        pattern = r'^(What|Where|When|Who|Why|How|Would) (.*) or (.*)\?$'

        match = re.search(pattern, route.text, flags=re.IGNORECASE)

        if match:
            stats.total_issues += 1
            self.page_logger_output(route, message)

        return stats

    # wh-questions
    def wh_questions(self, route, stats) -> object:
        """Identifies a Wh- Question and checks for appropriate punctuation."""
        message = 'R002: Wh- Question Should Use `.` Instead of `?` Punctuation'

        # updated pattern
        pattern = r'^(what|when|where|who|why|how)\b.*\?$'

        match = re.search(pattern, route.text, flags=re.IGNORECASE)

        if match and 'event' not in route.trigger:
            stats.total_issues += 1
            self.page_logger_output(route, message)

        return stats

    # clarifying-questions
    def clarifying_questions(self, route, stats) -> object:
        """Identifies Clarifying Questions that are missing `?` Punctuation."""
        message = 'R003: Clarifying Question Should Use `?` Punctuation'

        # updated pattern
        pattern = r'^(what|when|where|who|why|how)\b.*\.$'

        match = re.search(pattern, route.text, flags=re.IGNORECASE)

        if match and 'event' in route.trigger:
            stats.total_issues += 1
            self.page_logger_output(route, message)

        return stats


    # INTENT RULES
    # intent-missing-tps
    def missing_training_phrases(self, intent, stats) -> object:
        """Checks for Intents that are Missing Training Phrases."""
        message = 'R004: Intent is Missing Training Phrases.'

        stats.total_inspected += 1
        stats.total_issues += 1
        self.intent_logger_output(intent, message)

        return stats

    # intent-min-tps
    def min_tps_head_intent(self, intent, lang_code, stats) -> object:
        """Determines if Intent has min recommended training phrases."""
        n_tps = len(intent.training_phrases[lang_code]['tps'])
        stats.total_inspected += 1

        hid = self.check_if_head_intent(intent)

        if hid and n_tps < 50:
            message = 'R005: Head Intent Does Not Have Minimum Training '\
                f'Phrases. ({n_tps} / 50)'

            stats.total_issues += 1
            self.intent_logger_output(intent, message)

        elif n_tps < 20:
            message = 'R005: Intent Does Not Have Minimum Training '\
                f'Phrases. ({n_tps} / 20)'

            stats.total_issues += 1
            self.intent_logger_output(intent, message)

        return stats

    # TEST CASE RULES
    # explicit-tps-in-test-cases
    def explicit_tps_in_tcs(self, tc, stats) -> object:
        """Checks that user utterance is an explicit intent training phrase."""
        
        for pair in tc.intent_data:
            stats.total_inspected += 1

            intent = pair['intent']
            phrase = pair['user_utterance']
            tps = pair['training_phrases']
            # tps = tc.associated_intent_data.get(intent, None)

            if phrase not in pair['training_phrases']:
                message = 'R007: Explicit Training Phrase Not in Test Case'

                stats.total_issues += 1
                self.test_case_logger_output(tc, phrase, intent, message)

        return stats

    # invalid-intent-in-test-cases
    def invalid_intent_in_tcs(self, tc, stats) -> object:
        """Check that a listed Intent in the Test Case exists in the agent."""

        for pair in tc.intent_data:
            if pair['status'] == 'invalid_intent':
                stats.total_inspected += 1
                stats.total_issues += 1

                intent = pair['intent']
                phrase = pair['user_utterance']

        message = 'R008: Invalid Intent in Test Case'
        self.test_case_logger_output(tc, phrase, intent, message)

        return stats