
import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

try:
    models = client.models.list()

    print("API key is authenticated!")
    print("\nAvailable models:")

    for model in models.data:
        print(model.id)

except Exception as error:
    print("Request failed:", error)
