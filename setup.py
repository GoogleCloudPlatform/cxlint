"""Setuptools for CXLINT."""

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

import pathlib
from setuptools import setup, find_packages

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='cxlint',
    version='1.0.4',
    description='A static code analyzer that provides automated quality \
      control for Dialogflow CX Agents',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/GoogleCloudPlatform/cxlint',
    author='Patrick Marlow',
    author_email='pmarlow@google.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Communications :: Chat',
        'Topic :: Software Development',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    keywords='dialogflow, cx, google, bot, chatbot, linter, dfcx',
    package_dir={'':'src'},
    packages=find_packages(where='src'),
    package_data={'': ['.cxlintrc']},
    python_requires='>=3.6, <4',
)
