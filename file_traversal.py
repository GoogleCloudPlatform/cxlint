"""Helper utils for traversing JSON Package file structure."""

import os
import logging

# logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

class FileTraversal:
    """Traverse file structures in the JSON Package."""

    @staticmethod
    def build_flow_path_list(agent_local_path: str):
        """Builds a list of dirs, each representing a Flow directory.

        Ex: /path/to/something/flows/<flow_dir>

        This dir path can then be used to find the next level of information
        in the directory by appending the appropriate next dir structures like:
        - <flow_name>.json, for the Flow object
        - /transitionRouteGroups, for the Route Groups dir
        - /pages, for the Pages dir
        """
        flows_path = agent_local_path + '/flows'

        flow_paths = []

        for flow_dir in os.listdir(flows_path):
            # start_page_flow_file = flow_dir + '.json'
            flow_dir_path = f'{flows_path}/{flow_dir}'
            flow_paths.append(flow_dir_path)

        return flow_paths

    @staticmethod
    def build_page_path_list(flow_path: str):
        """Builds a list of files, each representing a Page.

        Ex: /path/to/something/flows/<flow_dir>/pages/<page_name>.json
        """
        pages_path = f'{flow_path}/pages'

        page_paths = []

        for page in os.listdir(pages_path):
            page_file_path = f'{pages_path}/{page}'
            page_paths.append(page_file_path)

        return page_paths