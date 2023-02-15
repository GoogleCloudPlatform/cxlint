import json
import os

from configparser import ConfigParser
from typing import List

from common import Common
from rules import RulesDefinitions

from graph import Graph
from resources.types import Flow, Page, LintStats
from resources.pages import Pages
from resources.routes import Fulfillments

class Flows:
    """Flow linter methods and functions."""
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
        self.include_filter = self.load_include_filter(config)
        self.exclude_filter = self.load_exclude_filter(config)
        self.special_pages = [
            'End Session', 'End Flow', 'Start Page', 'Current Page',
            'Previous Page'
        ]

        self.pages = Pages(verbose, config, console)
        self.routes = Fulfillments(verbose, config, console)

    @staticmethod
    def load_include_filter(config: ConfigParser) -> str:
        """Loads the include pattern for Flow display names."""
        pattern = config['FLOWS']['include']

        return pattern

    @staticmethod
    def load_exclude_filter(config: ConfigParser) -> str:
        """Loads the exclude pattern for Flow display names."""
        pattern = config['FLOWS']['exclude']

        if pattern == '':
            pattern = None

        return pattern

    @staticmethod
    def build_flow_path_list(agent_local_path: str):
        """Builds a list of dirs, each representing a Flow directory.

        Ex: /path/to/agent/flows/<flow_dir>

        This dir path can then be used to find the next level of information
        in the directory by appending the appropriate next dir structures like:
        - <flow_name>.json, for the Flow object
        - /transitionRouteGroups, for the Route Groups dir
        - /pages, for the Pages dir
        """
        root_dir = agent_local_path + '/flows'

        flow_paths = []

        for flow_dir in os.listdir(root_dir):
            flow_dir_path = f'{root_dir}/{flow_dir}'
            flow_paths.append(flow_dir_path)

        return flow_paths
    
    @staticmethod
    def find_orphaned_pages(flow: Flow):
        """Find Orphaned Pages in the graph.
        
        An Orphaned Page is defined as:
          - A Page which has no incoming edge when traversed from Start Page.
            That is, it is unreachable in the graph by any practical means.
          - A Page which is connected to a root orphaned page. That is, a page
            that could have both incoming or outgoing routes, but due to its
            connectedness to the root orphan page, is unreachable in the graph.

        Here we will compute the symmetric difference of 2 sets:
          - Active Pages (i.e. Pages that were reachable in the graph)
          - Used Pages (i.e. Pages that were used by some Route)

        If an Orphaned Page has children that it routes to, those children will
        appear in Used Pages, although they will ultimately be unreachable.
        It's possible for an Orphaned Page to route back to an Active Page in
        the graph. For these instances, we don't want to count those pages as
        orphaned, because they are reachable via other sections of the graph.
        """
        filtered_set = flow.active_pages.symmetric_difference(flow.graph._used_nodes)
        flow.orphaned_pages.update(filtered_set)

        return flow

    def find_unused_pages(self, flow: Flow):
        """Find Unused Pages in the graph.
        
        An Unused Page is defined as:
          - A Page which has no incoming or outgoing edge AND
          - A Page which exists in the Agent design time, but which is not
            present anywhere in the graph, either visible or non-visible.

        Here we will compute the difference of 2 sets:
          - All Pages (i.e. Pages that exist in the Agent Design Time)
          - Used Pages (i.e. Pages that were used by some Route)

        The resulting set will consist of 2 types of Pages:
          - Truly Unused Pages
          - Orphaned Root Pages

        Orphaned Root Pages end up in the results due to the fact that no other
        Active Page is pointing to them. We remove these from the resulting set
        before presenting the Truly Unused Pages.
        """

        # Discard special pages as they are non-relevant for final outcome
        for page in self.special_pages:
            flow.all_pages.discard(page)

        prelim_unused = flow.all_pages.difference(flow.graph._used_nodes)

        # Filter out Orphaned Root Pages
        filtered_set = set()

        for page in prelim_unused:
            if page not in flow.graph._edges:
                filtered_set.add(page)
            else:
                flow.orphaned_pages.add(page)

        flow.unused_pages = filtered_set

        return flow
    
    def recurse_edges(
            self,
            edges: List,
            page: Page,
            dangling: set,
            visited: set):
        """Recursive method searching graph edges for Active / Dangling Pages.

        A byproduct of searching for Dangling Pages in the graph is that we can
        produce a set of Active Pages in the graph. These are pages that are
        reachable when traversing from the Start Page. These can then be used
        to determine Orphaned Pages in another method.
        """
        if page in edges:
            for inner_page in edges[page]:
                if inner_page not in visited:
                    visited.add(inner_page)
                    dangling, visited = self.recurse_edges(
                        edges, inner_page, dangling, visited)
                    
        else:
            dangling.add(page)

        return dangling, visited
    
    def find_dangling_pages(self, flow: Flow):
        """Find Dangling Pages in the graph.
        
        A Dangling Page is defined as:
          - Any page that exists in the graph that has no outgoing edge
          
        These pages can result in a conversational "dead end" which is
        potentially unrecoverable.
        """

        flow.dangling_pages, flow.active_pages = self.recurse_edges(
            flow.graph._edges,
            'Start Page',
            flow.dangling_pages,
            flow.active_pages
        )

        # Clean up Special Pages       
        for page in self.special_pages:
            flow.dangling_pages.discard(page)

        filtered_set = set()
        # Clean up any Flow Transitions
        for page in flow.dangling_pages:
            if 'FLOW' not in page:
                filtered_set.add(page)

        flow.dangling_pages = filtered_set

        return flow
    
    def check_flow_filters(self, flow: Flow):
        """Determines if the Flow should be filtered for linting."""
        if self.include_filter:
            if flow.display_name in self.include_filter:
                flow.filtered = False

            else:
                flow.filtered = True

        if self.exclude_filter:
            if flow.display_name in self.exclude_filter:
                flow.filtered = True

        return flow

    def lint_start_page(
        self,
        flow: Flow,
        stats: LintStats):
        """Process a single Flow Path file."""
        with open(flow.start_page_file, 'r', encoding='UTF-8') as flow_file:
            page = Page(flow=flow)
            page.display_name = 'Start Page'

            flow.graph.add_node(page.display_name)

            page.data = json.load(flow_file)
            page.events = page.data.get('eventHandlers', None)
            page.routes = page.data.get('transitionRoutes', None)
            page.verbose = self.verbose

            flow.resource_id = page.data.get('name', None)
            page.agent_id = flow.agent_id
            page.resource_id = 'START_PAGE'
            flow.data[page.display_name] = page.resource_id

            # Order of linting is important
            stats = self.routes.lint_routes(page, stats)
            stats = self.routes.lint_events(page, stats)
            stats = self.pages.lint_webhooks(page, stats)

            flow_file.close()

        return stats
    
    def lint_graph(self, flow:Flow, stats: LintStats):
        """Lint the graph structure for the specified Flow.
        
        In this method we are taking the completed Flow Graph that was built
        for this specific Flow and checking for any design inconsistencies.
        These include things like Unused, Dangling, and Orphaned pages.
        """

        # unused-pages
        if self.disable_map.get('unused-pages', True):
            stats = self.rules.unused_pages(flow, stats)

        # dangling-pages
        if self.disable_map.get('dangling-pages', True):
            stats = self.rules.dangling_pages(flow, stats)

        # orphaned-pages
        if self.disable_map.get('orphaned-pages', True):
            stats = self.rules.orphaned_pages(flow, stats)

        return stats


    def lint_flow(self, flow: Flow, stats: LintStats):
        """Lint a Single Flow dir and all subdirectories."""
        flow.display_name = Common.parse_filepath(flow.dir_path, 'flow')
        flow = self.check_flow_filters(flow)

        if not flow.filtered:
            message = f'{"*" * 15} Flow: {flow.display_name}'
            self.console.log(message)

            flow.start_page_file = f'{flow.dir_path}/{flow.display_name}.json'

            stats = self.lint_start_page(flow, stats)
            stats = self.pages.lint_pages_directory(flow, stats)

            # Order of Find Operations is important here!
            flow = self.find_unused_pages(flow)
            flow = self.find_dangling_pages(flow)
            flow = self.find_orphaned_pages(flow)

            stats = self.lint_graph(flow, stats)

        return stats

    def lint_flows_directory(self, agent_local_path: str):
        """Linting the top level Flows dir in the JSON Package structure.

        The following files/dirs exist under the `flows` dir:
        - Flow object (i.e. Flow START_PAGE)
        - transitionRouteGroups
        - pages

        In Dialogflow CX, the START_PAGE of each Flow is a special kind of Page
        that exists within the Flow object itself. In this method, we will lint
        the Flow object, all files in the transitionRouteGroups dir and all
        files in the pages dir.
        """
        start_message = f'{"#" * 10} Begin Flows Directory Linter'
        self.console.log(start_message)

        stats = LintStats()

        # Create a list of all Flow paths to iter through
        flow_paths = self.build_flow_path_list(agent_local_path)
        stats.total_flows = len(flow_paths)

        # linting happens here
        for flow_path in flow_paths:
            flow = Flow()
            flow.graph = Graph()
            flow.verbose = self.verbose
            flow.agent_id = self.agent_id
            flow.dir_path = flow_path
            stats = self.lint_flow(flow, stats)

        header = "-" * 20
        rating = Common.calculate_rating(
            stats.total_issues, stats.total_inspected)

        end_message = f'\n{header}\n{stats.total_flows} Flows linted.'\
            f'\n{stats.total_issues} issues found out of '\
            f'{stats.total_inspected} inspected.'\
            f'\nYour Agent Flows rated at {rating:.2f}/10\n\n'
        self.console.log(end_message)
