# pylint: skip-file

"""Testing"""

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

if __name__ == "__main__":
    agent_local_path = 'local_path/to/your/agent_files'
    agent_id = '<AGENT_ID' # optional AGENT_ID used for deep-linked logs

    naming_conventions = {
        "flow_name": "^[A-Z][a-z]*( [A-Z][a-z]*)*$",
        "intent_head_name": "head_intent.*",
        "intent_confirmation_name": "confirmation.*",
        "intent_escalation_name": "escalate.*",
        "intent_generic_name": "^\w+(-?\w+)*(\s+\w+(-?\w+)*)*$",
        "entity_type_name": "^\w+(-?\w+)*(\s+\w+(-?\w+)*)*$",
        "page_generic_name": "^\w+(-?\w+)*(\s+\w+(-?\w+)*)*$",
        "page_with_form_name": "^> collect.*",
        "page_with_webhook_name": "^> webhook.*",
        "test_case_name": "^\w+(-?\w+)*(\s+\w+(-?\w+)*)*$",
        "webhook_name": "^\w+(-?\w+)*(\s+\w+(-?\w+)*)*$"
        }


    cxlint = CxLint(
        agent_id=agent_id,
        naming_conventions=naming_conventions,
        load_gcs=False,
        # agent_type='chat',
        # language_code=['en'],
        # resource_filter=["flows", "entity_types", "webhooks", "intents"],
        # flow_include_list=['Steering'],
        # intent_include_pattern='sup'
        output_file="/Users/pmarlow/eng/cxlint/data/logs.txt",
    )

    cxlint.lint_agent(agent_local_path)
