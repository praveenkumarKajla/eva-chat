from openai import AsyncOpenAI
from app.config import OPENAI_API_KEY
from typing import List, Dict

aclient = AsyncOpenAI(api_key=OPENAI_API_KEY)

class Chatbot:
    def __init__(self):
        self.conversation_history: List[Dict[str, str]] = []

    async def get_response(self, message: str):
        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": message})

        try:
            # Call OpenAI API with streaming
            stream = await aclient.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.conversation_history,
                stream=True,
                n=1,
                temperature=0.7
            )

            full_response = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content

            # Add bot response to conversation history
            self.conversation_history.append({"role": "assistant", "content": full_response})

        except Exception as e:
            print(f"Error in OpenAI API call: {str(e)}")
            yield "I'm sorry, but I encountered an error. Please try again later."

# Create a global instance of the Chatbot
chatbot = Chatbot()

async def get_chatbot_response(message: str):
    async for token in chatbot.get_response(message):
        yield token