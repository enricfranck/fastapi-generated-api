import os
import logging
from typing import List, Dict, Any

from schemas import ClassModel, AttributesModel

from model_type import preserve_custom_sections, camel_to_snake
from utils.generate_data_test import generate_data

# Configuration
OUTPUT_DIR = "/tests"
# OUTPUT_DIR = "/Users/macbookpro/Desktop/projet/fastapi-generated-api/core"
TEST_LIST = ["create", "update", "get", "get_by_id", "delete"]

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_import() -> str:
    """Generate the necessary imports for the schema."""
    return "\n".join([
        "from app import crud, schemas",
        "from app.core import security",
    ])


def generate_column(data: List[AttributesModel]) -> Dict[str, Any]:
    """Generate column data based on model attributes."""
    result = {}
    for attr in data:
        if attr.is_required:
            result[attr.name] = generate_data(attr.type, attr.length)
    return result


def generate_headers():
    return '{"Authorization": f\'Bearer {token}\'}'


def generate_create_access():
    return "data={'id': str(user.id), 'email': user.email}"


def generate_():
    return "data={'id': str(user.id), 'email': user.email}"


def generate_data_to_access():
    return "{'email': 'test@example.com', 'password': 'testpassword'}"


def generate_access_token():
    return [
        f"    # Prepare User for connection",
        f"    user_data = {generate_data_to_access()}",
        f"    user = schemas.User(**user_data)",
        f"    db.add(user)",
        f"    db.commit()",
        f"\n"
        f"    token = security.create_access_token({generate_create_access()})",
    ]


def generate_bearer():
    return [
        f"        headers={generate_headers()}",
    ]


generate_access_token_str = "\n".join(generate_access_token())
generate_bearer_str = "\n".join(generate_bearer())


def generate_test_api(model: ClassModel, table_name: str) -> str:
    """Generate test functions for API operations (create, update, delete, get, get_by_id)."""
    test_name = camel_to_snake(model.name)
    class_lines = []

    for test_key in TEST_LIST:
        test_lines = [f"\n\ndef test_{test_key}_{table_name}_api(client, db):"]

        if test_key == "create":
            # Test for creating a new record via API
            data = [
                generate_access_token_str,
                f"    {test_name}_data = {generate_column(model.attributes)}",
                f"    response = client.post(",
                f"        '/api/v1/{table_name}/',",
                f"        {table_name}_in={test_name}_data,",
                generate_bearer_str,
                f"    )",
                f"    assert response.status_code == 200, response.text",
                f"    created_{test_name} = response.json()",
                f"    assert created_{test_name}['id'] is not None",
                f"    assert created_{test_name}['{list(generate_column(model.attributes).keys())[0]}'] == {test_name}_data['{list(generate_column(model.attributes).keys())[0]}']"
            ]
            test_lines.extend(data)

        elif test_key == "update":
            # Test for updating an existing record via API
            data = [
                generate_access_token_str,
                f"    # Create a record first",
                f"    {test_name}_data = {generate_column(model.attributes)}",
                f"    create_response = client.post(",
                f"        '/api/v1/{table_name}/',",
                f"        {table_name}_in={test_name}_data",
                f"    )",
                f"    assert create_response.status_code == 200, create_response.text",
                f"    created_{test_name} = create_response",
                f"",
                f"    # Update the record",
                f"    update_data = {generate_column(model.attributes)}",
                f"    update_response = client.put(",
                f"        '/api/v1/{table_name}/',",
                f"        {table_name}_in=update_data,",
                f"        {table_name}_id=created_{test_name}.id,",
                generate_bearer_str,
                f"    )",
                f"    assert update_response.status_code == 200, update_response.text",
                f"    updated_{test_name} = update_response",
                f"    assert updated_{test_name}.id == created_{test_name}.id",
                f"    assert updated_{test_name} != created_{test_name}  # Ensure the record was updated"
            ]
            test_lines.extend(data)

        elif test_key == "get":
            # Test for retrieving all records via API
            data = [
                generate_access_token_str,
                f"    # Create a record first",
                f"    {test_name}_data = {generate_column(model.attributes)}",
                f"    create_response = client.post(",
                f"        '/api/v1/{table_name}/',",
                f"        {table_name}_in={test_name}_data,",
                generate_bearer_str,
                f"    )",
                f"    assert create_response.status_code == 200, create_response.text",
                f"    created_{test_name} = create_response.json()",
                f"",
                f"    # Retrieve all records",
                f"    get_response = client.get(",
                f"        '/api/v1/{table_name}/',",
                generate_bearer_str,
                f"    )",
                f"    assert get_response.status_code == 200, get_response.text",
                f"    records = get_response.json()",
                f"    assert len(records) > 0",
                f"    assert any(record['id'] == created_{test_name}['id'] for record in records)"
            ]
            test_lines.extend(data)

        elif test_key == "get_by_id":
            # Test for retrieving a record by its ID via API
            data = [
                generate_access_token_str,
                f"    # Create a record first",
                f"    {test_name}_data = {generate_column(model.attributes)}",
                f"    create_response = client.post(",
                f"        '/api/v1/{table_name}/',",
                f"        {table_name}_in={test_name}_data,",
                generate_bearer_str,
                f"    )",
                f"    assert create_response.status_code == 200, create_response.text",
                f"    created_{test_name} = create_response",
                f"",
                f"    # Retrieve the record by ID",
                f"    get_response = client.get(",
                f"         '/api/v1/{table_name}/by_id/',",
                f"          {table_name}_id=created_{test_name}.id,",
                generate_bearer_str,
                f"    )",
                f"    assert get_response.status_code == 200, get_response.text",
                f"    retrieved_{test_name} = get_response",
                f"    assert retrieved_{test_name}.id == created_{test_name}.id",
                f"    assert retrieved_{test_name} == created_{test_name}"
            ]
            test_lines.extend(data)

        elif test_key == "delete":
            # Test for deleting a record via API
            data = [
                generate_access_token_str,
                f"    # Create a record first",
                f"    {test_name}_data = {generate_column(model.attributes)}",
                f"    create_response = client.post(",
                f"        '/api/v1/{table_name}/',",
                f"        {table_name}_in={test_name}_data,",
                generate_bearer_str,
                f"    )",
                f"    assert create_response.status_code == 200, create_response.text",
                f"    created_{test_name} = create_response",
                f"",
                f"    # Delete the record",
                f"    delete_response = client.delete(",
                f"        '/api/v1/{table_name}/',",
                f"        {table_name}_id=created_{test_name}.id,",
                generate_bearer_str,
                f"    )",
                f"    assert delete_response.status_code == 200, delete_response.text",
                f"    deleted_{test_name} = delete_response.json()",
                f"    assert deleted_{test_name}.id == created_{test_name}.id",
                f"",
                f"    # Ensure the record is no longer retrievable",
                f"    get_response = client.get(",
                f"        '/api/v1/{table_name}/by_id/',",
                f"        {table_name}_id=created_{test_name}.id,",
                generate_bearer_str,
                f"    )",
                f"    assert get_response.status_code == 404, get_response.text"
            ]
            test_lines.extend(data)

        class_lines.extend(test_lines)

    return "\n".join(class_lines)


def generate_full_schema(model: ClassModel, table_name: str) -> str:
    """Generate the full schema for a model, including imports and test functions."""
    return "\n".join([
        generate_import(),
        generate_test_api(model, table_name),
    ])


def write_test_apis(models: List[ClassModel], output_dir: str) -> None:
    """Write the generated schemas to files, preserving custom sections."""
    output_dir = output_dir + OUTPUT_DIR

    for model in models:
        # try:
        model = ClassModel(**model)
        table_name = camel_to_snake(model.name)
        schemas = generate_full_schema(model, table_name)
        file_name = f"test_apis_{table_name}.py"
        file_path = os.path.join(output_dir, file_name)

        # Preserve custom sections in the file
        final_content = preserve_custom_sections(file_path, schemas)

        with open(file_path, "w") as f:
            f.write(final_content)
        logger.info(f"Generated schemas for: {table_name}")
    # except Exception as e:
    #     logger.error(f"Failed to generate schema for {model.name}: {e}")


def main(models: List[ClassModel], output_dir: str = OUTPUT_DIR) -> None:
    """Main function to generate and write schemas for all models."""
    write_test_apis(models, output_dir)


if __name__ == "__main__":
    # Example usage
    models = [
        {
            "name": "User",
            "attributes": [
                {
                    "name": "first_name",
                    "type": "String",
                    "length": 100,
                    "is_primary": False,
                    "is_indexed": False,
                    "is_auto_increment": False,
                    "is_required": False,
                    "is_unique": False,
                    "is_foreign": False,
                    "foreign_key_class": "string",
                    "foreign_key": "string"
                },
                {
                    "name": "last_name",
                    "type": "String",
                    "length": 20,
                    "is_primary": False,
                    "is_indexed": False,
                    "is_auto_increment": False,
                    "is_required": True,
                    "is_unique": False,
                    "is_foreign": False,
                    "foreign_key_class": "string",
                    "foreign_key": "string"
                },
                {
                    "name": "age",
                    "type": "Integer",
                    "length": 0,
                    "is_primary": False,
                    "is_indexed": False,
                    "is_auto_increment": False,
                    "is_required": True,
                    "is_unique": False,
                    "is_foreign": False,
                    "foreign_key_class": "string",
                    "foreign_key": "string"
                }
            ]
        },

        {
            "name": "Role",
            "attributes": [
                {
                    "name": "name",
                    "type": "String",
                    "length": 100,
                    "is_primary": False,
                    "is_indexed": False,
                    "is_auto_increment": False,
                    "is_required": True,
                    "is_unique": False,
                    "is_foreign": False,
                    "foreign_key_class": "string",
                    "foreign_key": "string"
                },

            ]
        }
    ]
    main(models)
