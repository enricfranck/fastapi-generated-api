import datetime
import uuid
from typing import Any
import random
import string


def generate_random_text(length):
    # Generate a random string of letters and digits
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))


def generate_random_integer(max_value):
    # Generate a random integer between 0 and max_value (exclusive)
    return random.randint(0, max_value)


def generate_random_float():
    a = 1.5
    b = 5.5
    # Generate a random float between a and b
    return random.uniform(a, b)


def generate_random_boolean():
    return random.choice([True, False])


def generate_random_json():
    # Generate a random JSON object
    return {
        "id": random.randint(1, 100),  # Random integer
        "is_active": random.choice([True, False]),  # Random boolean
        "score": round(random.uniform(0, 100), 2),  # Random float
        "metadata": {  # Nested JSON object
            "created_at": f"2023-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",  # Random date
            "updated_at": f"2023-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",  # Random date
        }
    }


def generate_data(type_: Any, length: int = 0):
    type_ = type_.upper()
    limit = 10 if length and length >= 10 else length
    if type_ == "STRING":
        return generate_random_text(generate_random_integer(limit))
    elif type_ == "INTEGER":
        return generate_random_integer(20)
    elif type_ == "TEXT":
        return generate_random_text(generate_random_integer(100))
    elif type_ == "BOOLEAN":
        return generate_random_boolean()
    elif type_ == "FLOAT":
        return generate_random_float()
    elif type_ == "DATETIME":
        return datetime.datetime.now()
    elif type_ == "DATE":
        return datetime.date.today()
    elif type_ == "TIME":
        return datetime.time(
            hour=generate_random_integer(23),
            minute=generate_random_integer(59),
            second=generate_random_integer(59)
        )
    elif type_ == "JSON":
        return generate_random_json()
    elif type_ == "UUID":
        return uuid.uuid4()
    else:
        return ""


def get_column_type(column_type: str) -> str:
    """Map SQLAlchemy column type strings to Pydantic types."""
    column_type = column_type.lower()  # Normalize the type string

    if column_type == "integer":
        return "int"
    elif column_type == "string" or column_type == "text":
        return "str"
    elif column_type == "boolean":
        return "bool"
    elif column_type == "float":
        return "float"
    elif column_type == "datetime":
        return "datetime"
    elif column_type == "date":
        return "date"
    elif column_type == "uuid":
        return "UUID"
    elif column_type == "json":
        return "dict"
    else:
        return "Any"


def generate_comumn_name(column_name, optional: bool = False):
    if column_name == "hashed_password":
        return {"name": "password", "optional": True}
    return {"name": column_name, "optional": optional}
