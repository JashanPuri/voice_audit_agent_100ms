"""
Simple OpenAI Async Script
---------------------------
A minimal script to call OpenAI API with a prompt and get a response.

Setup:
1. Create a .env file in the project root
2. Add: OPENAI_API_KEY=your_api_key_here
3. Run: python personal_openai_script.py
"""

import os
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def get_openai_response(
    prompt: str,
    model: str = "gpt-5",
    temperature: float = 0.7,
    system_message: str = "You are a helpful assistant."
) -> str:
    """
    Send a prompt to OpenAI and get a response.
    
    Args:
        prompt: Your question or message
        model: The model to use (default: gpt-4o-mini)
        temperature: 0-2, lower = more focused, higher = more creative
        system_message: Instructions for the AI's behavior
    
    Returns:
        The AI's response as a string
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    client = AsyncOpenAI(api_key=api_key)
    
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature
    )
    
    return response.choices[0].message.content


system_prompt = """
Lets say I have a voice agent that makes calls to USA pharmacies and insurance providers for doing insurance verifications. 
The voice agent goes through the IVR and whenever a human agent comes in and speaks my agent is prompted to introduce itself and say something on the lines of .... we are on a recorded line. Now there can be multiple transfers where multiple human agents come in. My agent should always say the recorded line phrase. I have the transcripts of the call where the agent and the user (IVR Agent and/or human agent of the other side) go back and forth. Using this transcript (which is large) I just want to audit that whenever a human agent introduced and asked for the name of the agent. My agent introduced itself and said the we are on a recorded line phrase.

I have a prompt which takes in the conversation history and returns the indices of the messages where a new human agent speaks for the first time. which I would like to improve:
```
You are an auditing assistant that analyzes call transcripts. 
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
4. You only need to return the <index> values of the messages where a new human agent speaks for the first time.

Output format:
- Return a JSON array of integers representing the <index> values.
- Example: [5, 27, 43]
- Do not include explanations, only output the JSON.
```

Given a sample transcript in <transcript> tags, please improve the prompt.
Include some few shot examples and improve the overall context a bit
Do not create a very big prompt. Keep it concise.

"""

prompt = """
<transcript>
[
            {
              "role": "assistant",
              "content": "",
              "_id": "2198e11e-31d5-42f9-9e30-f56f2c06d0f7"
            },
            {
              "role": "assistant",
              "content": "",
              "_id": "7b5b335c-b3d4-4281-8182-d185c6eb7d76"
            },
            {
              "role": "user",
              "content": "Thank you for calling the Optum Rx pharmacy help desk.",
              "_id": "bff24e12-9a43-482e-b2d0-0d4bff160d0e"
            },
            {
              "role": "assistant",
              "content": "Representative",
              "_id": "c659686f-4154-49bb-9156-333fe6147b85"
            },
            {
              "role": "user",
              "content": "Your call may be monitored or recorded for quality purposes. Alright. Are you calling as a health care professional? Yes or no?",
              "_id": "7ef17f8a-ff0f-4c1d-9848-1e1875e81b13"
            },
            {
              "role": "assistant",
              "content": "Yes",
              "_id": "76938a7d-5dbc-4f9f-aeeb-c24e1d444f2b"
            },
            {
              "role": "user",
              "content": "I didn't hear anything. If you're calling as a health care professional, say yes or press one. Otherwise, say no or press two.",
              "_id": "3ffb8873-2afb-4056-a8bc-203df0503a0f"
            },
            {
              "role": "assistant",
              "content": "Yes",
              "_id": "0f40a0b2-c211-4006-8a4e-7ad2dce73642"
            },
            {
              "role": "user",
              "content": "Please say or enter your NPI number.",
              "_id": "4d84096d-2a55-4f35-bccf-41a858a19243"
            },
            {
              "role": "assistant",
              "content": "<dtmf>1588648570</dtmf>",
              "_id": "45c382be-24e1-4d89-89c6-f5db529d23db"
            },
            {
              "role": "user",
              "content": "Got it.",
              "_id": "46566e47-202a-426b-bae0-0a30356fe355"
            },
            {
              "role": "assistant",
              "content": "",
              "_id": "484a3b3f-6160-4d22-9df1-f3fba618785e"
            },
            {
              "role": "user",
              "content": "Are you calling about prior authorizations today?",
              "_id": "8571a0e1-2d9f-43e4-8d1d-d0828bc912ce"
            },
            {
              "role": "assistant",
              "content": "Benefits",
              "_id": "b408d926-57f3-42d9-a5bb-fbe4ba55d260"
            },
            {
              "role": "user",
              "content": "I'm sorry.",
              "_id": "30d62faa-3281-4e53-a110-5afe9f6270fd"
            },
            {
              "role": "assistant",
              "content": "Eligibility",
              "_id": "460a8da1-0ba5-4ea5-af00-6191744857a4"
            },
            {
              "role": "user",
              "content": "What's the member ID you're calling about?",
              "_id": "b3d9037c-d3ca-478d-a46f-f22667f6a146"
            },
            {
              "role": "assistant",
              "content": "<dtmf>91363884900</dtmf>",
              "_id": "5d1f2311-1474-4203-bc5b-7bb6d58e8cf4"
            },
            {
              "role": "user",
              "content": "Got it. What's the member's date of birth?",
              "_id": "ad3f98be-a640-4520-9df8-12afa3b62aa1"
            },
            {
              "role": "assistant",
              "content": "<dtmf>05221946</dtmf>",
              "_id": "2de186c9-8588-4f64-9a7b-87b6d0454ea6"
            },
            {
              "role": "user",
              "content": "Got it.",
              "_id": "5ef1f848-e251-4082-b8f8-4f21eee31888"
            },
            {
              "role": "assistant",
              "content": "",
              "_id": "197f7b66-72b8-4776-a828-d3387ad5d2dc"
            },
            {
              "role": "user",
              "content": "That's for Paul. Correct?",
              "_id": "1e6ec902-f185-44f8-a3be-633ad05b4b3b"
            },
            {
              "role": "assistant",
              "content": "Yes",
              "_id": "30fc6696-f273-4d60-a4a3-f3ffaeed6f27"
            },
            {
              "role": "user",
              "content": "Sorry. Let's try again. Is that for Paul? Did I get that right? Just say yes or no. Sorry. Since I'm having trouble, let's move on. What can I help? I'm sorry. I didn't understand that. For prior authorizations, press or say one. For patient benefits, press or say two. For mail order, press or say three. For technical support, press or say four. Or to speak with an advocate, press or say five.",
              "_id": "6d08f86a-1a82-425c-8954-682288ba3013"
            },
            {
              "role": "assistant",
              "content": "Two",
              "_id": "667a9a1b-982a-44c9-b4f0-df21de0c30e8"
            },
            {
              "role": "user",
              "content": "For your convenience, we also provide the ability to submit your prior authorization request online. Visit professionals dot OptumRx dot com and select prior authorizations to electronically submit your request.",
              "_id": "d137c44a-2704-4b58-8073-c61dec29e426"
            },
            {
              "role": "assistant",
              "content": "Representative",
              "_id": "3e86d497-8bed-48a9-968d-127fa58891e3"
            },
            {
              "role": "user",
              "content": "Please hold while I connect you with someone who can help.",
              "_id": "7d097c5f-3c7c-4ef5-95da-8c8ce9fbbbc1"
            },
            {
              "role": "assistant",
              "content": "",
              "_id": "8669b428-aac4-4aa9-89e9-2c5c1802c38b"
            },
            {
              "role": "user",
              "content": "Would you be willing to take a brief survey at the end of this call?",
              "_id": "af2ce1a1-e050-408d-a413-7b83612bb144"
            },
            {
              "role": "assistant",
              "content": "No",
              "_id": "c69167b7-aad1-41fb-ab3a-4f19ad89bf0e"
            },
            {
              "role": "user",
              "content": "If you have an online account, you may be able to sign in to chat with an agent, find answers to your most frequently asked questions, check medication pricing, and much more. Save time by going online today.",
              "_id": "4532bc7e-7bff-4454-9f91-ed2dd0c67222"
            },
            {
              "role": "assistant",
              "content": "",
              "_id": "76d7b788-dd71-4555-9318-3b7ce059cc89"
            },
            {
              "role": "user",
              "content": "Thank you for calling. My name is Crystal. Who do I have the pleasure of speaking with?",
              "_id": "97c8035a-29ec-47bf-a044-04056dd75c5f"
            },
            {
              "role": "assistant",
              "content": "Hi Crystal, this is Richard, from the Orgovyx support team, on a recorded line.",
              "_id": "944341a3-1859-463e-8e0a-90edfd3e40ee"
            },
            {
              "role": "user",
              "content": "Alright. Thank you. And how can I help you today?",
              "_id": "1325a40f-5051-444e-b388-b852500e7388"
            },
            {
              "role": "assistant",
              "content": "I'm calling about a patient's medication coverage.",
              "_id": "5e7ca921-9e8f-4169-88e7-db81a8dcfac7"
            },
            {
              "role": "user",
              "content": "Absolutely. What's the patient's name?",
              "_id": "1d082eb1-4599-4f74-a10f-e8fb724efbef"
            },
            {
              "role": "assistant",
              "content": "The patient's name is Paul Foote.",
              "_id": "bfb16d1a-03d7-455d-a145-87d464ce3559"
            },
            {
              "role": "user",
              "content": "And the patient's date of birth, please?",
              "_id": "5135e1e9-e233-4a35-98be-54c34487317a"
            },
            {
              "role": "assistant",
              "content": "Sure, the date of birth is May twenty-second, nineteen forty-six.",
              "_id": "715b836c-e796-41bc-a137-700507b55838"
            },
            {
              "role": "user",
              "content": "And can I get an NPI number for you?",
              "_id": "8a6cbe12-a714-4b94-bd11-cf95d7dc40aa"
            },
            {
              "role": "assistant",
              "content": "Yes, the NPI is <sp>1 5 8</sp>, <sp>8 6 4</sp>, <sp>8 5 7 0</sp>.",
              "_id": "2b5a7521-6bf5-41f1-997a-93e56b0868a1"
            },
            {
              "role": "user",
              "content": "Thank you. And how can I help you today?",
              "_id": "c1760e45-db3a-4aeb-a4e2-a1a29c107b83"
            },
            {
              "role": "assistant",
              "content": "I'm looking to verify pharmacy benefits for Orgovyx, one-twenty milligrams, quantity thirty, for a thirty-day supply. Is this medication covered under the member's plan?",
              "_id": "ad9031b8-5111-47f9-af65-443348aeccbc"
            },
            {
              "role": "user",
              "content": "It is covered with an approved prior authorization.",
              "_id": "4fd370a7-f370-40da-88a2-7de14f00cdc8"
            },
            {
              "role": "assistant",
              "content": "Okay, thank you. Could I get the prior authorization reference number, and the effective and end dates for that approval?",
              "_id": "0a36f0c5-f250-4d4a-9fba-636a91dc8758"
            },
            {
              "role": "user",
              "content": "It's p a dash f as in Frank, five zero eight three seven five six.",
              "_id": "a32ce8da-6ab1-46db-970d-aeddf89a9bcb"
            },
            {
              "role": "assistant",
              "content": "Thank you, Crystal. And what are the effective and end dates for that prior authorization?",
              "_id": "38fb448a-7667-4963-bf4e-a7f66e261b0f"
            },
            {
              "role": "user",
              "content": "The effective date is nine twenty three of twenty twenty five to nine twenty three of twenty twenty six.",
              "_id": "dbeb84d3-6c76-4650-ac20-20df48f2186c"
            },
            {
              "role": "assistant",
              "content": "Perfect, thank you. What formulary tier is Orgovyx listed under for this member?",
              "_id": "783a7f42-c06c-47f8-9abb-700e2c57ec27"
            },
            {
              "role": "user",
              "content": "It is",
              "_id": "d34ba66e-0e8a-40d4-8aca-fed47bf2b33e"
            },
            {
              "role": "assistant",
              "content": "Sorry, I think you cut out for a second\u2014could you let me know what tier Orgovyx is on?",
              "_id": "ce4c9373-0d69-42a2-a1fc-77a73264b8ee"
            },
            {
              "role": "user",
              "content": "Yes. One moment.",
              "_id": "f7ab3fb4-62a8-4b3a-89f8-1b8105d7596a"
            },
            {
              "role": "assistant",
              "content": "",
              "_id": "892f60f4-b12a-4423-9d84-4ccba2ef7020"
            },
            {
              "role": "user",
              "content": "Tier three.",
              "_id": "afcb393a-44d6-458c-a738-87557f434ee0"
            },
            {
              "role": "assistant",
              "content": "Thank you. Which specialty pharmacies are in-network for Orgovyx for this member?",
              "_id": "b2ee65ba-245b-424e-8260-6459a964b31c"
            },
            {
              "role": "user",
              "content": "It doesn't look like there's any preferred or recommended pharmacy.",
              "_id": "f0e44b27-1c9a-40d5-b7b1-f87c2da3311b"
            },
            {
              "role": "assistant",
              "content": "Oh, actually, since I'm from the Orgovyx support team, I know it's usually distributed through Biologics or Onco360. Would you mind checking if either of those are in-network? I have their NPIs if that helps.",
              "_id": "039a203a-8677-4ae1-bfb4-e4fe5e38e96a"
            },
            {
              "role": "user",
              "content": "ONCO360 is in the network.",
              "_id": "5688b901-a58a-4ed0-95f1-45e476662cb2"
            },
            {
              "role": "assistant",
              "content": "Thank you, Crystal. Could you tell me what the estimated patient cost would be at Onco360 for this fill?",
              "_id": "9cba7fba-0b59-4f7e-b7fa-cefd83cfb3ac"
            },
            {
              "role": "user",
              "content": "Fifty dollars for a thirty day supply.",
              "_id": "7f1f2d76-6d88-456d-8458-1da4fe6c70a9"
            },
            {
              "role": "assistant",
              "content": "Thank you. And just to clarify, is this plan Medicare Part D or commercial coverage?",
              "_id": "ea00a3f5-d50b-42aa-9624-2bad0d208a39"
            },
            {
              "role": "user",
              "content": "Medicare.",
              "_id": "a6d92edd-0a4a-4846-b96e-18be5bf69b1a"
            },
            {
              "role": "assistant",
              "content": "Is that Medicare Part D, as in prescription drug coverage, or is it a different Medicare plan?",
              "_id": "1e0c1a2f-8256-4c77-91b1-d96cc2d82c1a"
            },
            {
              "role": "user",
              "content": "Medicare Part D.",
              "_id": "79484487-c076-4210-b50a-4bb205b33313"
            },
            {
              "role": "assistant",
              "content": "Thank you for clarifying. What is the deductible amount for this plan, and how much has been met so far?",
              "_id": "866c8219-4c0c-43e3-b64e-257ca21014c3"
            },
            {
              "role": "user",
              "content": "There is no deductible for the plan.",
              "_id": "16a41982-3cb0-4635-bc22-c0f0ad6e93ea"
            },
            {
              "role": "assistant",
              "content": "Okay, thanks. Could you tell me the member's TrOOP amount\u2014how much has been met so far this year?",
              "_id": "f5074e18-85bc-4371-b486-550e373ca1cb"
            },
            {
              "role": "user",
              "content": "The trip amount is two thousand and six hundred and seven dollars and twenty one cents has been met.",
              "_id": "56df2243-e3a6-4bc0-b9d8-88693f3e11be"
            },
            {
              "role": "assistant",
              "content": "Thank you. And is the member receiving any Low Income Subsidy, or LIS, on this plan?",
              "_id": "31028b4e-938f-439f-89ed-ab60f8c5f893"
            },
            {
              "role": "user",
              "content": "No.",
              "_id": "13ab7c8c-f060-4097-9fa3-b908d331c604"
            },
            {
              "role": "assistant",
              "content": "Okay, and just to confirm, what would the patient pay if they entered the catastrophic phase\u2014would it be zero dollars, or is there a percentage?",
              "_id": "33490aa9-42bc-47a4-b24c-eb50a6f1f3df"
            },
            {
              "role": "user",
              "content": "It would be zero dollar copay.",
              "_id": "68c33a4c-0db4-4e81-ac06-74e2ea04e9a5"
            },
            {
              "role": "assistant",
              "content": "Alright, let me just make sure I have everything noted here... Oh, could I also get a reference number for this call?",
              "_id": "85de6141-6b73-4f81-8c88-25f3b648bf3f"
            },
            {
              "role": "user",
              "content": "Absolutely. That reference number is seven five two eight zero eight zero zero zero one.",
              "_id": "b43996c8-9994-41e0-9af5-73d5ac7ab233"
            },
            {
              "role": "assistant",
              "content": "Got it, thank you, Crystal. I really appreciate your help today. Hope you have a great rest of your afternoon.",
              "_id": "a87fcf53-f19e-4871-826c-612207a45df3"
            }
          ]
</transcript>
"""

# Example usage
async def main():
    """Example of how to use the function"""
    
    # Example 2: Custom settings
    response = await get_openai_response(
        prompt=prompt,
        temperature=1,
        system_message=system_prompt
    )
    print(f"Response: {response}\n")


if __name__ == "__main__":
    asyncio.run(main())
