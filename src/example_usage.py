"""
Example usage of the OpenAI client using the Responses API.

Before running this example:
1. Create a .env file in the project root
2. Add your OpenAI API key: OPENAI_API_KEY=your_key_here
3. Run: python -m src.example_usage
"""

from dotenv import load_dotenv
from src.openai_client import OpenAIClient

# Load environment variables from .env file
load_dotenv()


def example_simple_chat():
    """Example: Simple chat with system prompt"""
    print("=" * 60)
    print("Example 1: Simple Chat")
    print("=" * 60)
    
    # Initialize the client
    client = OpenAIClient(model="gpt-4o-mini")
    
    # Define system prompt (instructions)
    system_prompt = "You are a helpful voice audit assistant that analyzes conversations."
    
    # Define conversation messages
    messages = [
        {"role": "user", "content": "Hello! Can you help me audit a conversation?"}
    ]
    
    # Get response using Responses API
    response = client.chat(
        system_prompt=system_prompt,
        messages=messages
    )
    
    print(f"\nUser: {messages[0]['content']}")
    print(f"Assistant: {response}\n")


def example_conversation():
    """Example: Multi-turn conversation"""
    print("=" * 60)
    print("Example 2: Multi-turn Conversation")
    print("=" * 60)
    
    client = OpenAIClient(model="gpt-4o-mini")
    
    system_prompt = "You are a professional customer service auditor."
    
    messages = [
        {"role": "user", "content": "What should I look for in a good customer service call?"},
        {"role": "assistant", "content": "In a good customer service call, you should look for: 1) Clear communication, 2) Empathy and active listening, 3) Problem resolution, 4) Professional tone, and 5) Customer satisfaction."},
        {"role": "user", "content": "How do I rate the empathy of an agent?"}
    ]
    
    response = client.chat(
        system_prompt=system_prompt,
        messages=messages,
        temperature=0.7
    )
    
    print(f"\nFinal User Question: {messages[-1]['content']}")
    print(f"Assistant: {response}\n")


def example_different_temperatures():
    """Example: Different temperature settings"""
    print("=" * 60)
    print("Example 3: Temperature Comparison")
    print("=" * 60)
    
    client = OpenAIClient(model="gpt-4o-mini")
    
    system_prompt = "You are a creative writer."
    messages = [{"role": "user", "content": "Describe a sunset in one sentence."}]
    
    # Low temperature (more deterministic)
    response_low = client.chat(
        system_prompt=system_prompt,
        messages=messages,
        temperature=0.2
    )
    
    # High temperature (more creative)
    response_high = client.chat(
        system_prompt=system_prompt,
        messages=messages,
        temperature=1.5
    )
    
    print(f"\nPrompt: {messages[0]['content']}")
    print(f"\nLow Temperature (0.2): {response_low}")
    print(f"\nHigh Temperature (1.5): {response_high}\n")


if __name__ == "__main__":
    try:
        example_simple_chat()
        example_conversation()
        example_different_temperatures()
        
        print("=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except ValueError as e:
        print(f"\nError: {e}")
        print("\nMake sure to:")
        print("1. Create a .env file in the project root")
        print("2. Add your OpenAI API key: OPENAI_API_KEY=your_key_here")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

