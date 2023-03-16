# Rules Quick Reference Table

| Index | Rule  | Target Files / Resources  |
|---|---|---|
| R001 | [Closed-Choice Alternative Missing Question Mark](#closed-choice-alternative-missing-question-mark) | All Fulfillments |
| R002 | [“Wh-” questions](#wh--questions)  | All Fulfillments  |
| R003 | [Clarifying Questions Punctuation](#clarifying-questions-punctuation)  | Fulfillments in No-Match Handlers  |
| R004 | [Empty Training Phrases](#empty-training-phrases) | Intents |
| R005 | [Minimum Training Phrases for Head Intents](#minimum-training-phrases-for-head-intents) | Intents |
| R006 | [Minimum Training Phrases for General Intents](#minimum-training-phrases-for-general-intents) | Intents |
| R007 | [Explicit Training Phrase Not in Test Cases](#explicit-training-phrase-not-in-test-cases) | Test Cases, Intents |
| R008 | [Invalid Intent in Test Case](#invalid-intent-in-test-case) | Test Cases, Intents |
| R009 | [Yes / No Entities Present in Agent](#yes--no-entities-present-in-agent) | Entity Types |
| R010 | [Missing Metadata file for Intent](#missing-metadata-file-for-intent) | Intents |
| R011 | [Missing Webhook Error Handlers](#missing-webhook-error-handlers) | Pages, Route Groups, Start Page |
| R012 | [Unused Pages](#unused-pages) | Pages |
| R013 | [Dangling Pages](#dangling-pages) | Pages |
| R014 | [Unreachable Pages](#unreachable-pages) | Pages |

<br>
<br>

# Flow / Page Rules
### Closed-Choice Alternative Missing Question Mark
_**Rule: If Voice bot, check for trailing `?` immediately after each item in the list, except for the last item.**_   

Also known as _**Closed-Choice Alternative**_ questions.  

These questions have the form of “do you prefer A or B?” and they imply that the only choices are A or B and not C or D.  
This is, there is a finite number of choices. In this case, all items in the list have rising intonation except for the last one, which has falling intonation.  

When designing voice bots with “A or B” style questions, it is important to direct the STT using SSML “cues”.  
One such cue is to include a `?` immediately after the `A` portion of the “A or B” question. This forces the STT to use the proper intonation when synthesizing the text, leading the listener to appropriately understand this as a question that has 2 distinct choices.

Best practice is to write them like this:  
- Do you have problems with inbound `?` or outbound calls`.`
- Do you want to change it now `?` or later`.`
___

### Wh- Questions
_**Rule: If Voice bot, if an Agent Response question begins with “Wh-” (i.e. What, Who, Where, etc.) then the punctuation at the end should be .**_  
Verbiage in chatbots can follow normal punctuation rules of the target language in its written form. However, for voicebot, we should not treat punctuation markers as such but as intonation markers. This is:
- `.` = falling intonation
- `,` = continuing intonation
- `?` = raising intonation

In English, specifically, questions and statements follow very specific intonation rules depending on their syntax and speech acts. As such, we should adapt these punctuation markers to the appropriate intonation. While statements tend to have falling intonation, questions vary a bit more:   

**Wh- questions**. These are pronounced with falling intonation. So we’ll write them as:
- How can I help you`.`
- Which countries are you visiting`.`
- What’s the reason for your call today`.`
___

### Missing Webhook Error Handlers
_**Rule: If Page/Route contains Webhook, at least 1 Webhook Error Handler should also be present.**_  

There are various Webhook Error Handler events that can be applied.  
The primary purpose of this rule is to ensure that in the case of a failed Webhook, the user experience does not suffer from lack of conversation repair.
___

### Dangling Pages
_**Rule: If Page exists and has Incoming routes, it should have at least 1 Outgoing route, otherwise it represents a “dead-end” conversation path.**_   
These "dead end" or dangling pages can present a negative user experience if a user were to find there way to them with no way to exit the page.  
Although it's possible for a dangling page to have a webhook that returns it to another page in the graph, the lack of connectedness in the immediate graph and the use of a "black box routing" approach is not a best practice.
___

### Unreachable Pages
_**Rule: If Page exists and has Outgoing routes, it should have at least 1 Incoming route, otherwise it represents an unreachable conversation path in the graph.**_   
Unreachable Pages in the graph typically occur when an upstream route dependency is removed either on purpose or by accident.  This can cause one or more portions of the graph to become completely unreachable from the Start Page.  
Although it's possible to use webhooks to direct a user to a seemingly unreachable page in the graph, the "black box routing" approach is not a best practice and is generally discouraged.
___

### Unused Pages
_**Rule: If Page exists but is not used in the graph, raise a warning.**_   
In general, we find that users will create Page shells as placeholders which is typically fine for development work. However, by the time the bot reaches production, these should be built out and connected into the main graph for whatever feature they are to be used for.   

Any Page that exists but is not in use will be flagged for inspection and/or removal.
___

### Clarifying Questions Punctuation
_**Rule: If Voice bot, if No-Match Handler is present with follow up question, ensure punctuation is `?` for the follow up question.**_  
These questions don’t present new information to the customer as the previous types do. Instead, they repeat or rephrase a previous question to indicate that something is not clear and to give an opportunity to the other speaker to clarify.  
Normally, we’ll use these types of questions in no-matches (not in no-inputs.)  
These questions are pronounced with rising intonation regardless of their syntax.  
So, we’ll write them like this:
- Ex.1:	
  - Bot:	Which country are you visiting. _(first time asking this question)_
  - User:	`[noise/ambiguous/unclear]`
  - Bot:	Sorry, which country are you traveling to`?` _(clarifying question)_

- Ex.2:
  - Bot:	Do you know your travel dates? _(first time asking this question)_
  - User:	`[noise/ambiguous/unclear]`
  - Bot:	Sorry, do you know when you are traveling`?` _(clarifying question)_
___

<br>
<br>

# Entity Type Rules
### Yes / No Entities Present in Agent
_**Rule: Flag any Entity in the Agent that is focused on collecting yes/no responses.**_  

In general, capturing yes / no style responses from the user should be done via Intents and not Entities, because using Intents provides a more sophisticated capture method.  
In some special cases it may be desirable to use Entity Types for capturing yes / no responses, but this is typically an advanced design method and should be used only if the designer recognizes the inherent impact to the NLU model and possible conflict if this is used.
___

<br>
<br>

# Intent Rules
### Empty Training Phrases
**_Rule: If an Intent exists in the agent and has 0 Training Phrases, trigger a warning/error._**
While this is self-explanatory, there are some outliers for this behavior to consider.  
Some designers choose to “stage” Intents before they are released.  
While this may get caught in linting, it might not actually be an issue.  
Bot designers should have the ability to disable linting for this rule if needed.
___

### Minimum Training Phrases for Head Intents
_**Rule: If an Intent exists that contains a label “head intent”, “head”, OR if the Intent contains in its display name the word “head”, AND in either of these scenarios the Intent has < 50 Training Phrases, trigger a warning/error.**_  

Following the [Training Phrases Best Practices](https://cloud.google.com/dialogflow/cx/docs/concept/agent-design#phrase-minimum) for this rule.

Note that the definition of "head intent" is tunable by using the .cxlintrc file and adding your specific naming convention for what is considered a "head intent".
___


### Minimum Training Phrases for General Intents
_**Rule: If an Intent is not a Head Intent (as defined above) and has < 20 Training Phrases, trigger a warning/error.**_  

Following the [Training Phrases Best Practices](https://cloud.google.com/dialogflow/cx/docs/concept/agent-design#phrase-minimum) for this rule.

Note that the number of training phrases is tunable using the .cxlintrc file.
___

### Missing Metadata File for Intent
_**Rule: If the Intent metadata file is missing from the JSON Package, flag this as a potential corrupted file / issue.**_  

In some rare cases the Intent metadata file could be deleted during a merge (using Git Integration) or accidentally removed by a user.   
In these cases, it can cause the Intent file to become corrupted and may not import properly to an Agent.
___

<br>
<br>

# Test Case Rules
### Explicit Training Phrase Not in Test Cases
_**Rule: All Test Case User utterances should be explicitly present in the corresponding Intent that it triggers as part of the Test Case.**_  

In the User Input portion of the Test Case, the exact utterance that the user says should be explicitly present as a Training Phrase in the corresponding Intent that it will trigger in the Virtual Agent Output of the conversation turn.  

- Example:
  - User: I need to make a payment
  - TriggeredIntent: `head_intent.make_payment`

When we inspect the Training Phases that are in `head_intent.make_payment`, we should find that “I need to make a payment” is verbatim, explicitly present in the Intent Training Phrases.  
The implications of not having an `EXACT_MATCH` for training phrases in Test Cases is that it can cause flakiness of the Test Cases due to the way NLU models are retrained upon Agent import to a new environment.  
While testing NLU is equally important, we should separate “NLU Tests” from “Agent Logic” tests appropriately.
___

### Invalid Intent in Test Case
_**Rule: Any Triggered Intent that is used in the Virtual Agent Output of a Test Case should exist as a valid Intent in agent resources.**_  

When building a Test Case, it’s possible to define a triggered Intent manually through the Test Case UI or via the API that contains an Intent Display Name string that is invalid (i.e. doesn’t actually exist in the agent).   
This rule will check for the existence of these Test Cases and flag them.

___