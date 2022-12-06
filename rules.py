"""Rule Definitions for CX Lint."""

import logging
import re

# logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

class RulesDefinitions:
    """All rule definitions used by CX Lint."""
    @staticmethod
    def regex_logger_output(
        match,
        resource: str,
        trigger: str,
        message: str,
        text: str,
        verbose: bool) -> int:
        """Consolidated logging method for rules."""
        counter = 0
        if match:
            if verbose:
                logging.info(
                    '%s:%s: \n%s: \n%s\n', resource, trigger, message, text)
            else:
                logging.info('%s:%s: %s', resource, trigger, message)

            counter = 1

        return counter

    def closed_choice_alternative_parser(
        self,
        resource: str,
        trigger: str,
        text: str,
        verbose: bool) -> None:
        """Identifies a Closed Choice Alternative Question."""
        message = 'R001: Closed-Choice Alternative Missing Intermediate `?` '\
            '(A? or B.)'

        pattern = r'(\sare\s|\sdo\s|should\s|\swill\s|what).*\sor\s.*'
        match = re.search(pattern, text, flags=re.IGNORECASE)

        counter = self.regex_logger_output(
            match, resource, trigger, message, text, verbose)

        return counter

    def wh_questions(
        self,
        resource: str,
        trigger: str,
        text: str,
        verbose: bool) -> None:
        """Identifies a Wh- Question and checks for appropriate punctuation."""
        counter = 0
        message = 'R002: Wh- Question Should Use `.` Instead of `?` Punctuation'

        pattern = r'(How|Which|What|Where|When|Why).*(\?)'
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match and 'event' not in trigger:
            counter = self.regex_logger_output(
                match, resource, trigger, message, text, verbose)

        return counter

    # def clarifying_questions(
    #     self,
    # )
