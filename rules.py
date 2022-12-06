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
    def regex_logger_output(route, message: str) -> None:
        """Consolidated logging method for rules."""
        if route.verbose:
            logging.info(
                '%s:%s:%s: \n%s: \n%s\n',
                route.page.flow.display_name,
                route.page.display_name,
                route.trigger,
                message,
                route.text)
        else:
            logging.info(
                '%s:%s:%s: %s',
                route.page.flow.display_name,
                route.page.display_name,
                route.trigger,
                message)

    def closed_choice_alternative_parser(self, route, stats) -> object:
        """Identifies a Closed Choice Alternative Question."""
        message = 'R001: Closed-Choice Alternative Missing Intermediate `?` '\
            '(A? or B.)'

        pattern = r'(\sare\s|\sdo\s|should\s|\swill\s|what).*\sor\s.*'
        match = re.search(pattern, route.text, flags=re.IGNORECASE)

        if match:
            stats.total_issues += 1
            self.regex_logger_output(route, message)

        return stats

    def wh_questions(self, route, stats) -> object:
        """Identifies a Wh- Question and checks for appropriate punctuation."""
        message = 'R002: Wh- Question Should Use `.` Instead of `?` Punctuation'

        pattern = r'(How|Which|What|Where|When|Why).*(\?)'
        match = re.search(pattern, route.text, flags=re.IGNORECASE)

        if match and 'event' not in route.trigger:
            stats.total_issues += 1
            self.regex_logger_output(route, message)

        return stats

    # def clarifying_questions(
    #     self,
    # )
