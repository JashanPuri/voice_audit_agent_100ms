def get_human_transfer_detection_audit_prompt():
    return """
You are an auditing assistant that analyzes call transcripts to find when a new human agent (on the pharmacy/insurance side) first comes on the line.
The transcript is formatted as a list of <message> blocks in XML. 
Each <message> has:
- <index>: a unique integer identifier for this message (incremented sequentially).
- <id>: the raw message id from the transcript (not relevant for your task).
- <role>: "agent" for our voice agent, or "user" for the pharmacy/insurance side (either IVR or human).
- <content>: the actual text spoken.

Your task:
1. Identify the exact <index> values where a NEW human agent first comes on the line.
   - This includes the very first time a human answers after the IVR.
   - Also includes when the call is transferred and another human agent joins.
2. Ignore IVR prompts (e.g., "Press 1 for …", "Please enter your …").
3. Human agent entries usually look like: "Hello, this is …", "Hi, you’ve reached …", "How may I help you?", etc.
Human agent cues include greetings and agent identification such as:
    - “Hello/Hi, this is …”, “My name is …”, “You’ve reached …”
    - “How may I help you?”, “Who am I speaking with?”
    - Free-form conversational replies that are clearly not IVR.
4. You only need to return the <index> values of the messages where a new human agent speaks for the first time.

Output format:
- Return a JSON array of integers representing the <index> values.
- Example: [5, 27, 43]
- Do not include explanations, only output the JSON.

Few shot examples:
Example 1:
<messages>
  <message>
    <index>0</index>
    <role>user</role>
    <content>Thank you for calling … Press 1 for claims.</content>
  </message>
  <message>
    <index>1</index>
    <role>assistant</role>
    <content>Representative</content>
  </message>
  <message>
    <index>2</index>
    <role>user</role>
    <content>Please hold while I connect you.</content>
  </message>
  <message>
    <index>3</index>
    <role>user</role>
    <content>Hi, this is Sarah with Member Services. How can I help?</content>
  </message>
</messages>
Output: [3]

Example 2:
<messages>
  <message>
    <index>0</index>
    <role>user</role>
    <content>Press 1 for …</content>
  </message>
  <message>
    <index>1</index>
    <role>user</role>
    <content>Please hold while I connect you.</content>
  </message>
  <message>
    <index>2</index>
    <role>user</role>
    <content>Hello, you’ve reached John in Benefits.</content>
  </message>
  <message>
    <index>3</index>
    <role>assistant</role>
    <content>Hi John…</content>
  </message>
  <message>
    <index>4</index>
    <role>user</role>
    <content>I’ll transfer you to Pharmacy. One moment.</content>
  </message>
  <message>
    <index>5</index>
    <role>user</role>
    <content>Pharmacy Help Desk, this is Amy.</content>
  </message>
</messages>
Output: [2, 5]

Example 3:
<messages>
  <message>
    <index>0</index>
    <role>user</role>
    <content>Please hold while I connect you with someone who can help.</content>
  </message>
  <message>
    <index>1</index>
    <role>assistant</role>
    <content></content>
  </message>
  <message>
    <index>2</index>
    <role>user</role>
    <content>Thank you for calling. My name is Crystal. Who do I have the pleasure of speaking with?</content>
  </message>
</messages>
Output: [2]
"""


def get_recorded_line_phrase_audit_prompt(agent_name: str):
    return f"""
You are an auditing assistant that analyzes call transcripts to find whether the voice agent (on the USA side) explicitly stated that the call is on a recorded line when introducing itself to a human agent (on the pharmacy/insurance side).
Note that the transcript is a chunk of the full transcript. Hence indexes will not start from 0 and will represent the index of the message as per the full transcript.
The transcript is formatted as <message> blocks in XML. Each block has:
- <index>: a unique integer identifier
- <role>: either "assistant" (our voice agent) or "user" (the pharmacy/insurance side, IVR or human)
- <content>: the spoken text

Your task:
1. Focus only on the "assistant" (our voice agent) messages in the provided chunk.
2. Determine if the assistant explicitly stated that the call is on a recorded line when introducing itself to a human agent.
   - Look for phrases like "we are on a recorded line", "this call is recorded", "you are on a recorded line", "this is a recorded line", "this is a recorded call", "this is a recorded conversation", "this is a recorded line call", "this is a recorded line conversation".
   - Variations in wording are acceptable as long as the meaning is clearly that the call is recorded.
3. Ignore cases where the assistant is just responding normally without an introduction.

Agent name: {agent_name}

Output format:
- Always return a JSON object with two fields:
  {{
    "recorded_line_said": true/false,
    "index": <index> of the message where the voice agent explicitly stated that the call is on a recorded line. Do not include if the voice agent did not explicitly state that the call is on a recorded line.
  }}

Notes:
- If multiple assistant messages appear, choose the one that seems to be the introduction (usually the first message after the human agent's greeting).
- If the assistant failed to include the recorded line phrase, return false but still include the <index> of the introduction message.
"""
