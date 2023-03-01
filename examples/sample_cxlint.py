"""Example Python file to run as part of an External Pipeline."""

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

from cxlint import CxLint

if __name__ == '__main__':
    AGENT_LOCAL_PATH = 'local_path/to/your/agent_files'
    AGENT_ID = '<AGENT_ID' # optional AGENT_ID used for deep-linked logs

    # Each of the keyword args for CxLint can also be set using the .cxlintrc
    # config file keyword args provided at runtime will override config file
    # entries.

    cxlint = CxLint(
        agent_id=AGENT_ID,
        # agent_type='chat',
        # language_code=['en'],
        # resource_filter=["flows", "entity_types"],
        # flow_include_list=['Steering'],
        # intent_include_pattern='sup'
        output_file='logs.txt',
    )

    cxlint.lint_agent(AGENT_LOCAL_PATH)
