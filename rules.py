"""Rule Definitions for CX Lint."""

import logging

# logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

class RulesDefinitions:
    """All rule definitions used by CX Lint."""

    @staticmethod
    def closed_choice_alternative_parser(
        resource: str,
        trigger: str,
        text: str,
        verbose: bool) -> None:
        """Identifies a Closed Choice Alternative Question."""

        counter = 0
        message = 'R001: Closed-Choice Alternative Missing Intermediate `?` (A? or B.)'

        if ' or ' in text:
            if verbose:
                logging.info('%s:%s: \n%s: \n%s\n', resource, trigger, message, text)
            else:
                logging.info('%s:%s: %s', resource, trigger, message)

            counter = 1

        return counter

    @staticmethod
    def something_else():
        """test"""
        return None
