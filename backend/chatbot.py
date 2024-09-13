from openai import AsyncOpenAI
import os
import asyncio
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

aclient = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Chatbot:
    def __init__(self):
        self.conversation_history: List[Dict[str, str]] = []

    async def get_response(self, message: str):
        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": message})

        try:
            # Call OpenAI API without streaming
            response = await aclient.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.conversation_history,
                max_tokens=150,
                n=1,
                temperature=0.7
            )

            full_response = response.choices[0].message.content

            # Add bot response to conversation history
            self.conversation_history.append({"role": "assistant", "content": full_response})

            return full_response

        except Exception as e:
            print(f"Error in OpenAI API call: {str(e)}")
            return "I'm sorry, but I encountered an error. Please try again later."

# Create a global instance of the Chatbot
chatbot = Chatbot()

async def get_chatbot_response(message: str):
    return await chatbot.get_response(message)