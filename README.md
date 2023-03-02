# Dialogflow CX Linter
<a href="https://github.com/googleapis/google-cloud-python/blob/main/README.rst#stability-levels" alt="preview">
<img src="https://img.shields.io/badge/support-preview-gold" /></a>
<a href="https://pypi.org/project/cxlint/" alt="preview">
<img src="https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10-blue" /></a>

\
Similar to [code linting](https://en.wikipedia.org/wiki/Lint_(software)), Dialogflow CX Agents can benefit from an automated linter to catch various common design defects when developing Agents.  
The primary goal is to minimize common defects shipped to production by proactively catching and fixing them.  


# Quick Start

In order to use this library, you first need to go through the following steps:

1. Select or create a [Cloud Platform](https://console.cloud.google.com/project) project.
2. [Enable billing](https://cloud.google.com/billing/docs/how-to/modify-project#enable_billing_for_a_project) for your project.
3. [Setup Authentication.](https://googleapis.dev/python/google-api-core/latest/auth.html)

## Mac/Linux
``` bash
pip install virtualenv
virtualenv <your-env>
source <your-env>/bin/activate
<your-env>/bin/pip install google-cloud-dialogflow-cx
```

## Windows
-------

```bash
pip install virtualenv
virtualenv <your-env>
<your-env>\Scripts\activate
<your-env>\Scripts\pip.exe install google-cloud-dialogflow-cx
```

# Authentication  
Authentication can vary depending on how and where you are interacting with SCRAPI.

## Google Colab
If you're using cxlint with a [Google Colab](https://colab.research.google.com/) notebook, you can add the following to the top of your notebook for easy authentication

``` python
project_id = '<YOUR_GCP_PROJECT_ID>'

# this will launch an interactive prompt that allows you to auth with GCP in a browser
!gcloud auth application-default login --no-launch-browser

# this will set your active project to the `project_id` above
!gcloud auth application-default set-quota-project $project_id
```

After running the above, Colab will pick up your credentials from the environment. No need to use Service Account keys!

# Examples

Code samples and snippets live in the [examples/](examples) folder.

# Supported Python Versions
Python >= 3.8

# Contributing
We welcome any contributions or feature requests you would like to submit!

1. Fork the Project
2. Create your Feature Branch (git checkout -b feature/AmazingFeature)
3. Commit your Changes (git commit -m 'Add some AmazingFeature')
4. Push to the Branch (git push origin feature/AmazingFeature)
5. Open a Pull Request

License
=======
Distributed under the Apache 2.0 License. See [LICENSE](../LICENSE.txt) for more information.

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->