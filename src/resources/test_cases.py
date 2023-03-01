"""Test Case linter methods and functions."""

# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os

from configparser import ConfigParser
from typing import Dict, List, Any

from common import Common
from rules import RulesDefinitions
from resources.types import TestCase, LintStats

class TestCases:
    """Test Case linter methods and functions."""
    def __init__(self, verbose: bool, config: ConfigParser, console):
        self.verbose = verbose
        self.console = console
        self.disable_map = Common.load_message_controls(config)
        self.agent_id = Common.load_agent_id(config)
        self.rules = RulesDefinitions(self.console)
        self.tag_filter = self.load_tag_filter(config)
        self.display_name_filter = self.load_display_name_filter(config)
        # self.intent_map_for_tcs = None

    @staticmethod
    def load_tag_filter(config: ConfigParser) -> Dict[str,str]:
        """Loads the config file for test cases into a map."""
        tag_list = config['TEST CASE TAGS']['include'].replace(
            '\n', '').split(',')

        # Check for empty tag_list from file and set to None
        if len(tag_list) == 1 and tag_list[0] == '':
            tag_list = None

        else:
            for i, tag in enumerate(tag_list):
                if tag[0] != '#':
                    tag = f'#{tag}'
                    tag_list[i] = tag
                
        return tag_list

    @staticmethod
    def load_display_name_filter(config: ConfigParser) -> str:
        """Loads the matching pattern for test case display names."""
        pattern = config['TEST CASE DISPLAY NAME PATTERN']['pattern']

        return pattern

    @staticmethod
    def build_test_case_path_list(agent_local_path: str):
        """Builds a list of files, each representing a test case."""
        root_dir = agent_local_path + '/testCases'

        test_case_paths = []

        for test_case in os.listdir(root_dir):
            end = test_case.split('.')[-1]
            if end == 'json':
                test_case_path = f'{root_dir}/{test_case}'
                test_case_paths.append(test_case_path)

        return test_case_paths

    @staticmethod
    def get_test_case_intent_phrase_pair(tc: TestCase) -> List[Dict[str,str]]:
        """Parse Test Case and return a list of intents in use.
        
        This method will produce a List of Dicts where the contents of each
        dict is the Training Phrase and associated Triggered Intent as listed
        in the Test Case Conversation Turn. This information is used to compare
        the User Input training phrase with the actual training phrases that
        exist in the Intent resource. 
        
        The dict format is as follows:
            {
                training_phrase: <training_phrase>,
                intent: <intent_display_name>
            }
        """
        intent_data = []

        if tc.conversation_turns:
            for turn in tc.conversation_turns:
                user = turn['userInput']
                agent = turn['virtualAgentOutput']
                intent = agent.get('triggeredIntent', None)
                phrase = user.get('input', None)

                text = phrase.get('text', None)
                # TODO pmarlow: Add DTMF user inputs

                if text:
                    text = text['text']

                if intent and text:
                    intent_data.append(
                        {'user_utterance': text,
                        'intent': intent['name'],
                        'status': 'valid',
                        'training_phrases': []}
                        )

        return intent_data

    @staticmethod
    def get_test_case_intent_data(agent_local_path: str):
        """Collect all Intent Files and Training Phrases for Test Case."""
        # TODO (pmarlow) consolidate into build_intent_paths

        intents_path = agent_local_path + '/intents'

        intent_paths = []

        for intent_dir in os.listdir(intents_path):
            intent_dir_path = f'{intents_path}/{intent_dir}'
            intent_paths.append(
                {'intent': intent_dir,
                'file_path': intent_dir_path})

        return intent_paths

    @staticmethod
    def flatten_tp_data(tp_data: List[Any]):
        """Flatten the Training Phrase proto to a list of strings."""
        cleaned_tps = []

        for tp in tp_data['trainingPhrases']:
            parts_list = [part['text'].lower() for part in tp['parts']]
            cleaned_tps.append("".join(parts_list))

        return cleaned_tps 

    def check_invalid_intent_test_case(self, tc: TestCase):
        """Check to see if the Test Case contains an invalid intent."""
        return None

    def gather_intent_tps(self, tc: TestCase):
        # TODO Refactor
        """Collect all TPs associated with Intent data in Test Case."""
        tc.associated_intent_data = {}

        for i, pair in enumerate(tc.intent_data):
            intent_dir = tc.agent_path + '/intents/' + pair['intent']

            try:
                if 'trainingPhrases' in os.listdir(intent_dir):

                    training_phrases_path = intent_dir + '/trainingPhrases'

                    for lang_file in os.listdir(training_phrases_path):
                        lang_code = lang_file.split('.')[0]
                        lang_code_path = f'{training_phrases_path}/{lang_file}'

                        with open(lang_code_path, 'r', encoding='UTF-8') as tp_file:
                            tp_data = json.load(tp_file)
                            cleaned_tps = self.flatten_tp_data(tp_data)

                            tp_file.close()

                        # TODO pmarlow: refactor to use tc.intent_data instead
                        # Need to create another level inside the Intent Dict that contains
                        # the language files as well.
                        tc.intent_data[i]['training_phrases'].extend(cleaned_tps)
                        tc.associated_intent_data[pair['intent']] = cleaned_tps

            except Exception as err:
                tc.intent_data[i]['status'] = 'invalid_intent'
                tc.has_invalid_intent = True
                continue

        return tc

    def qualify_test_case(self, tc: TestCase):
        """Ensure Test Case meets all required filters and prerequisites."""
        tag_match = True
        display_name_match = False

        # Check to see if TC tags match the provided filter tags. If we fail a
        # match we can return early. If no tag_filter is provided we can skip.
        if tc.tags and self.tag_filter:
            tag_match = bool(set(tc.tags).intersection(set(self.tag_filter)))


        # Check to see if TC display name matches provided display name filter.
        # If the filter is not in the display name, we can return early. If no
        # display_name_filter is provided, we can skip.
        if self.display_name_filter in tc.display_name:
            display_name_match = True

        if all([tag_match, display_name_match]):
            tc.intent_data = self.get_test_case_intent_phrase_pair(tc)
            tc = self.gather_intent_tps(tc)

            if not tc.has_invalid_intent:
                tc.qualified = True

        return tc


    def lint_test_case(self, tc: TestCase, stats: LintStats):
        """Lint a single Test Case file."""
        
        with open(tc.dir_path, 'r', encoding='UTF-8') as tc_file:
            tc.data = json.load(tc_file)
            tc.resource_id = tc.data.get('name', None)
            tc.display_name = tc.data.get('displayName', None)
            tc.tags = tc.data.get('tags', None)
            tc.conversation_turns = tc.data.get(
                'testCaseConversationTurns', None)
            tc.test_config = tc.data.get('testConfig', None)

            tc = self.qualify_test_case(tc)

            tc_file.close()

        if tc.qualified:
            # R007 explicit-tps-in-test-cases
            if self.disable_map.get('explicit-tps-in-test-cases', True):
                stats.total_test_cases += 1
                stats = self.rules.explicit_tps_in_tcs(tc, stats)

        if tc.has_invalid_intent:
            # R008 invalid-intent-in-test-cases
            if self.disable_map.get('invalid-intent-in-test-cases', True):
                stats.total_test_cases += 1
                stats = self.rules.invalid_intent_in_tcs(tc, stats)

        return stats

    def lint_test_cases_directory(self, agent_local_path: str):
        """Linting the test cases dir in the JSON package structure."""
        start_message = f'{"#" * 10} Begin Test Cases Directory Linter'
        self.console.log(start_message)

        stats = LintStats()

        test_case_paths = self.build_test_case_path_list(agent_local_path)
        # stats.total_test_cases = len(test_case_paths)

        # self.intent_map_for_tcs = self.get_test_case_intent_data(agent_local_path)

        # Linting Starts Here
        for test_case in test_case_paths:
            tc = TestCase()
            tc.verbose = self.verbose
            tc.agent_id = self.agent_id
            tc.dir_path = test_case
            tc.agent_path = agent_local_path
            stats = self.lint_test_case(tc, stats)

        header = "-" * 20
        rating = Common.calculate_rating(
            stats.total_issues, stats.total_inspected)

        end_message = f'\n{header}\n{stats.total_test_cases} Test Cases linted.'\
            f'\n{stats.total_issues} issues found out of '\
            f'{stats.total_inspected} inspected.'\
            f'\nYour Agent Test Cases rated at {rating:.2f}/10\n\n'
        self.console.log(end_message)
