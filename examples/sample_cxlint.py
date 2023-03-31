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
    gcs_path = "gs://sample_bucket/agent.zip"
    agent_id = '<AGENT_ID' # optional AGENT_ID used for deep-linked logs

    naming_conventions = {
        "agent_name": ".*",
        "flow_name": ".*",
        "intent_head_name": "head_intent.*",
        "intent_confirmation_name": ".*",
        "intent_escalation_name": ".*",
        "intent_generic_name": ".*",
        "entity_type_name": ".*",
        "page_generic_name": ".*",
        "page_with_form_name": ".*",
        "page_with_webhook_name": ".*",
        "test_case_name": ".*",
        "webhook_name": ".*"
        }

    # Instantiating Linter Class and input args
    cxlint = CxLint(
        agent_id=agent_id,
        naming_conventions=naming_conventions,
        load_gcs=True,
        # agent_type='chat',
        # language_code=['en'],
        # resource_filter=["flows", "entity_types", "webhooks", "intents"],
        # flow_include_list=['Steering'],
        # intent_include_pattern='sup'
        output_file="logs.txt",
    )

    # Downloading GCS files and unzipping locally
    agent_file = cxlint.gcs.download_gcs(gcs_path, agent_local_path)
    cxlint.gcs.unzip(agent_file, agent_local_path)

    # Running Linter
    cxlint.lint_agent(agent_local_path)
