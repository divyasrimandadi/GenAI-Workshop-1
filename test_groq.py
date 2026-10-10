
import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

try:
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": "Reply with: Groq API key is working!"
            }
        ],
        max_tokens=50,
    )

    print("SUCCESS: Groq API is working!")
    print("Response:", response.choices[0].message.content)

except Exception as error:
    print("API request failed:", error)
