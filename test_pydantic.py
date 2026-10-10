from pydantic import BaseModel, Field, EmailStr, field_validator, ValidationError
import re


class UserProfile(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    age: int = Field(ge=18, le=100)
    email: EmailStr
    pan: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if not value.replace(" ", "").isalpha():
            raise ValueError("Name must contain only letters and spaces")
        return value.strip()

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, value):
        value = value.strip().upper()

        # Indian PAN format: 5 letters, 4 digits, 1 letter
        if not re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", value):
            raise ValueError("Invalid PAN format. Example: ABCDE1234F")

        return value


# Test 1: Valid user profile
valid_data = {
    "name": "Divya Sri",
    "age": 22,
    "email": "divya@example.com",
    "pan": "ABCDE1234F",
}

try:
    user = UserProfile(**valid_data)
    print("VALID PROFILE")
    print(user.model_dump())
    print()

except ValidationError as error:
    print("Validation failed:")
    print(error)


# Test 2: Invalid user profile
invalid_data = {
    "name": "Divya123",
    "age": 15,
    "email": "invalid-email",
    "pan": "ABC123",
}

try:
    user = UserProfile(**invalid_data)
    print(user.model_dump())

except ValidationError as error:
    print("INVALID PROFILE — errors detected:")
    for issue in error.errors():
        field = ".".join(str(part) for part in issue["loc"])
        print(f"{field}: {issue['msg']}")
