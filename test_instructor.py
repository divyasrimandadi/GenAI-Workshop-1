
import os
import instructor
from groq import Groq
from pydantic import BaseModel, Field, EmailStr


class UserProfile(BaseModel):
    name: str = Field(description="Full name")
    age: int = Field(ge=18, le=100)
    email: EmailStr
    pan: str = Field(
        pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]$",
        description="Indian PAN format"
    )


client = instructor.from_groq(
    Groq(api_key=os.environ["GROQ_API_KEY"]),
    mode=instructor.Mode.JSON,
)

try:
    profile = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        response_model=UserProfile,
        messages=[
            {
                "role": "user",
                "content": (
                    "Create a fictional example user profile. "
                    "Use the name Rahul Sharma, age 25, "
                    "email rahul@example.com, and PAN ABCDE1234F. "
                    "Return data matching the requested schema."
                ),
            }
        ],
        max_tokens=200,
    )

    print("STRUCTURED OUTPUT SUCCESSFUL")
    print(profile.model_dump_json(indent=2))

except Exception as error:
    print("Request failed:", error)
