"""Example Python Executable for Running CX Lint as part of an External Pipeline."""
from cxlint import CxLint

if __name__ == '__main__':
    AGENT_LOCAL_PATH = 'local_path/to/your/agent_files'
    AGENT_ID = '<AGENT_ID' # optional AGENT_ID used for deep-linked logs

    # Each of the keyword args for CxLint can also be set using the .cxlintrc config file
    # keyword args provided at runtime will override config file entries.

    cxlint = CxLint(
        verbose=True,
        agent_id=AGENT_ID, # for deep link logs
        agent_type='voice', # voice | chat; some rules apply only to voice agents
        intent_pattern=None, # used to filter intents by sub-string provided
        load_gcs=False, # enable to utilize built-in GCS download function
        resource_filter=None, # Can be List of Str containing resource(s) to filter for linting
        test_case_pattern='NUS.SA', # Filter for test case display names
        test_case_tags='required' # Filter for test case tags
        )

    cxlint.lint_agent(AGENT_LOCAL_PATH)
