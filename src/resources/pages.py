import json
import os

from configparser import ConfigParser

from common import Common
from rules import RulesDefinitions
from resources.types import Flow, Page, LintStats
from resources.routes import Fulfillments

class Pages:
    """Pages linter methods and functions."""
    def __init__(
            self,
            verbose: bool,
            config: ConfigParser,
            console):
        self.verbose = verbose
        self.console = console
        self.config = config
        self.agent_type = Common.load_agent_type(config)
        self.disable_map = Common.load_message_controls(config)
        self.agent_id = Common.load_agent_id(config)
        self.rules = RulesDefinitions(self.console)

        self.routes = Fulfillments(verbose, config, console)

    @staticmethod
    def build_page_path_list(flow_path: str):
        """Builds a list of files, each representing a Page.

        Ex: /path/to/agent/flows/<flow_dir>/pages/<page_name>.json
        """
        pages_path = f'{flow_path}/pages'

        page_paths = []

        for page in os.listdir(pages_path):
            page_file_path = f'{pages_path}/{page}'
            page_paths.append(page_file_path)

        return page_paths
    
    @staticmethod
    def clean_page_display_name(display_name: str):
        """Replace characters from map for the given page name."""
        patterns = {
            "%28": "(",
            "%29": ")",
            "%23": "#",
            "%2f": "/",
            "%3f": "?"
            }

        for pattern in patterns:
            if pattern in display_name:
                display_name = display_name.replace(pattern, patterns[pattern])

        return display_name
    
    def lint_webhooks(self, page: Page, stats: LintStats):
        """Lint a Page with Webhook setup best practice rules."""

        # missing-webhook-event-handlers
        if self.disable_map.get('missing-webhook-event-handlers', True):
            stats = self.rules.missing_webhook_event_handlers(page, stats)

        return stats
    
    def lint_page(self, page: Page, stats: LintStats):
        """Lint a Single Page file."""
        page.display_name = Common.parse_filepath(page.page_file, 'page')
        page.display_name = self.clean_page_display_name(page.display_name)

        page.flow.graph.add_node(page.display_name)

        # TODO
        # Page Display Name from Filename contains special characters so it will
        # not match against page display names stored inside the proto objects
        # Need to implement a parser for symbol translation.
        page.flow.all_pages.add(page.display_name)

        with open(page.page_file, 'r', encoding='UTF-8') as page_file:
            page.data = json.load(page_file)
            page.verbose = self.verbose
            page.entry = page.data.get('entryFulfillment', None)
            page.events = page.data.get('eventHandlers', None)
            page.routes = page.data.get('transitionRoutes', None)

            page.resource_id = page.data.get('name', None)
            page.flow.data[page.display_name] = page.resource_id

            # Order of linting is important here
            stats = self.routes.lint_entry(page, stats)
            stats = self.routes.lint_routes(page, stats)
            stats = self.routes.lint_events(page, stats)
            stats = self.lint_webhooks(page, stats)


            page_file.close()

        return stats

    def lint_pages_directory(self, flow: Flow, stats: LintStats):
        """Linting the Pages dir inside a specific Flow dir.
        
        Some Flows may not contain Pages, so we check for the existence
        of the directory before traversing
        """
        if 'pages' in os.listdir(flow.dir_path):
            page_paths = self.build_page_path_list(flow.dir_path)

            for page_path in page_paths:
                page = Page(flow=flow)
                page.agent_id = flow.agent_id
                page.page_file = page_path
                stats.total_pages += 1
                stats = self.lint_page(page, stats)

        return stats