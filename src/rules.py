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
    def page_logger_output(resource, message: str) -> None:
        """Consolidated logging method for Page rules."""
        if resource.verbose:
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

    @staticmethod
    def intent_logger_output(intent, message: str) -> None:
        """Consolidated logging method for Intent rules."""
        if intent.verbose:
            logging.info(
                '%s:%s',
                intent.display_name,
                message)
        else:
            logging.info(
                '%s:%s',
                intent.display_name,
                message)

    @staticmethod
    def check_if_head_intent(intent):
        """Checks if Intent is Head Intent based on labels and name."""
        hid = False

        if 'head' in intent.display_name:
            hid = True
        # elif intent.labels:
        #     for label in intent.labels:
        #         if 'head' in label['key']:
        #             hid = True
        #         if 'head' in label['value']:
        #             hid = True

        return hid

    # RESPONSE MESSAGE RULES
    def closed_choice_alternative_parser(self, route, stats) -> object:
        """Identifies a Closed Choice Alternative Question."""
        message = 'R001: Closed-Choice Alternative Missing Intermediate `?` '\
            '(A? or B.)'

        # pattern = r'(\sare\s|\sdo\s|should\s|\swill\s|what).*\sor\s.*'

        # updated pattern
        pattern = r'^(What|Where|When|Who|Why|How) (.*) or (.*)\?$'

        match = re.search(pattern, route.text, flags=re.IGNORECASE)

        if match:
            stats.total_issues += 1
            self.page_logger_output(route, message)

        return stats

    def wh_questions(self, route, stats) -> object:
        """Identifies a Wh- Question and checks for appropriate punctuation."""
        message = 'R002: Wh- Question Should Use `.` Instead of `?` Punctuation'

        # pattern = r'(How|Which|What|Where|When|Why).*(\?)'

        # updated pattern
        pattern = r'^(what|when|where|who|why|how)\b.*\?$'

        match = re.search(pattern, route.text, flags=re.IGNORECASE)

        if match and 'event' not in route.trigger:
            stats.total_issues += 1
            self.page_logger_output(route, message)

        return stats

    def clarifying_questions(self, route, stats) -> object:
        """Identifies Clarifying Questions that are missing `?` Punctuation."""
        message = 'R003: Clarifying Question Should Use `?` Punctuation'

        # pattern = r'^(How|Which|What|Where|When|Why).*(\.)$'

        # updated pattern
        pattern = r'^(what|when|where|who|why|how)\b.*\.$'

        match = re.search(pattern, route.text, flags=re.IGNORECASE)

        if match and 'event' in route.trigger:
            stats.total_issues += 1
            self.page_logger_output(route, message)

        return stats


    # INTENT RULES
    def missing_training_phrases(self, intent, stats) -> object:
        """Checks for Intents that are Missing Training Phrases."""
        message = 'R004: Intent is Missing Training Phrases.'

        stats.total_inspected += 1
        stats.total_issues += 1
        self.intent_logger_output(intent, message)

        return stats

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
