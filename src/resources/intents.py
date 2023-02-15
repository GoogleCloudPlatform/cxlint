import json
import os

from configparser import ConfigParser

from common import Common
from rules import RulesDefinitions
from resources.types import Intent, LintStats

class Intents:
    """Intent linter methods and functions."""
    def __init__(self, verbose: bool, config: ConfigParser, console):
        self.verbose = verbose
        self.console = console
        self.disable_map = Common.load_message_controls(config)
        self.agent_id = Common.load_agent_id(config)
        self.rules = RulesDefinitions(self.console)
        self.include_filter = self.load_include_filter(config)
        self.exclude_filter = self.load_exclude_filter(config)

    @staticmethod
    def load_include_filter(config: ConfigParser) -> str:
        """Loads the include pattern for Intent display names."""
        pattern = config['INTENTS']['include']

        return pattern

    @staticmethod
    def load_exclude_filter(config: ConfigParser) -> str:
        """Loads the exclude pattern for Intent display names."""
        pattern = config['INTENTS']['exclude']

        if pattern == '':
            pattern = None

        return pattern

    @staticmethod
    def parse_lang_code(lang_code_path: str) -> str:
        """Extract the language_code from the given file path."""

        first_parse = lang_code_path.split('/')[-1]
        lang_code = first_parse.split('.')[0]

        return lang_code

    @staticmethod
    def build_lang_code_paths(intent: Intent):
        """Builds dict of lang codes and file locations.

        The language_codes and paths for each file are stored in a dictionary
        inside of the Intent dataclass. This dict is access later to lint each
        file and provide reporting based on each language code.
        """
        root_dir = intent.dir_path + '/trainingPhrases'

        for lang_file in os.listdir(root_dir):
            lang_code = lang_file.split('.')[0]
            lang_code_path = f'{root_dir}/{lang_file}'
            intent.training_phrases[lang_code] = {'file_path': lang_code_path}

    @staticmethod
    def build_intent_path_list(agent_local_path: str):
        """Builds a list of dirs, each representing an Intent directory.

        Ex: /path/to/agent/intents/<intent_dir>

        This dir path can be used to find the next level of information
        in the directory by appending the appropriate next dir structures like:
        - <intent_name>.json, for the Intent object metadata
        - /trainingPhrases, for the Training Phrases dir
        """
        root_dir = agent_local_path + '/intents'

        intent_paths = []

        for intent_dir in os.listdir(root_dir):
            intent_dir_path = f'{root_dir}/{intent_dir}'
            intent_paths.append(intent_dir_path)

        return intent_paths

    def check_intent_filters(self, intent: Intent) -> Intent:
        """Determines if the Intent should be filtered for linting."""
        if self.include_filter:
            if self.include_filter in intent.display_name:
                intent.filtered = False

            else:
                intent.filtered = True

        if self.exclude_filter:
            if self.exclude_filter in intent.display_name:
                intent.filtered = True

        return intent

    def lint_intent_metadata(self, intent: Intent, stats: LintStats):
        """Lint the metadata file for a single Intent."""
        intent.metadata_file = f'{intent.dir_path}/{intent.display_name}.json'

        try:
            with open(intent.metadata_file, 'r', encoding='UTF-8') as meta_file:
                intent.data = json.load(meta_file)
                intent.resource_id = intent.data.get('name', None)
                intent.labels = intent.data.get('labels', None)
                intent.description = intent.data.get('description', None)

                # TODO: Linting rules for Intent Metadata

                meta_file.close()

        except FileNotFoundError as err:
            stats = self.rules.intent_missing_metadata(intent, stats)

        return stats

    def lint_language_codes(self, intent: Intent, stats: LintStats):
        """Executes all Training Phrase based linter rules."""

        for lang_code in intent.training_phrases:
            tp_file = intent.training_phrases[lang_code]['file_path']

            with open(tp_file, 'r', encoding='UTF-8') as tps:
                data = json.load(tps)
                intent.training_phrases[lang_code]['tps'] = data['trainingPhrases']

                # intent-min-tps
                if self.disable_map.get('intent-min-tps', True):
                    stats = self.rules.min_tps_head_intent(
                        intent, lang_code, stats)

                tps.close()

        return stats

    def lint_training_phrases(self, intent: Intent, stats: LintStats):
        """Lint the Training Phrase dir for a single Intent."""
        if 'trainingPhrases' in os.listdir(intent.dir_path):
            self.build_lang_code_paths(intent)
            stats = self.lint_language_codes(intent, stats)

        # intent-missing-tps
        elif self.disable_map.get('intent-missing-tps', True):
            stats = self.rules.missing_training_phrases(intent, stats)

        return stats


    def lint_intent(self, intent: Intent, stats: LintStats):
        """Lint a single Intent directory and associated files."""
        intent.display_name = Common.parse_filepath(intent.dir_path, 'intent')
        intent = self.check_intent_filters(intent)

        if not intent.filtered:
            stats.total_intents += 1
            stats = self.lint_intent_metadata(intent, stats)
            stats = self.lint_training_phrases(intent, stats)

        return stats

    def lint_intents_directory(self, agent_local_path: str):
        """Linting the top level Intents Dir in the JSON Package structure.

        The following files/dirs exist under the `intents` dir:
        - <intent_display_name> Directory
          - trainingPhrases
            - <language-code>.json
          - <intent_display_name> Object

        In Dialogflow CX, the Training Phrases of each Intent are stored in
        individual .json files by language code under each Intent Display
        Name. In this method, we will lint all Intent dirs, including the
        training phrase files and metadata objects for each Intent.
        """
        start_message = f'{"#" * 10} Begin Intents Directory Linter'
        self.console.log(start_message)

        stats = LintStats()

        # Create a list of all Intent paths to iter through
        intent_paths = self.build_intent_path_list(agent_local_path)
        # stats.total_intents = len(intent_paths)

        # Linting Starts Here
        for intent_path in intent_paths:
            intent = Intent()
            intent.verbose = self.verbose
            intent.agent_id = self.agent_id
            intent.dir_path = intent_path
            stats = self.lint_intent(intent, stats)
            # stats.total_inspected += 1

        header = "-" * 20
        rating = Common.calculate_rating(
            stats.total_issues, stats.total_inspected)

        end_message = f'\n{header}\n{stats.total_intents} Intents linted.'\
            f'\n{stats.total_issues} issues found out of '\
            f'{stats.total_inspected} inspected.'\
            f'\nYour Agent Intents rated at {rating:.2f}/10\n\n'
        self.console.log(end_message)
