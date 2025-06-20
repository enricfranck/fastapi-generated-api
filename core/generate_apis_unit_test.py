import os
import logging
from typing import List, Dict, Any

import schemas
from schemas import ClassModel, AttributesModel

from model_type import preserve_custom_sections, camel_to_snake
from utils.generate_data_test import generate_data

# Configuration
OUTPUT_DIR = "/tests"
TEST_LIST = ["create", "update", "get", "get_by_id", "delete"]

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_import(other_config: schemas.OtherConfigSchema) -> str:
    """Generate the necessary imports for the schema."""
    imports = [
        "from app import crud, schemas",
    ]
    if other_config.use_authentication:
        imports.append("from app.core import security")
    return "\n".join(imports)


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


def generate_data_to_access():
    return "{'email': 'test@example.com', 'password': 'testpassword'}"


def generate_access_token(other_config: schemas.OtherConfigSchema) -> List[str]:
    if not other_config.use_authentication:
        return []
    return [
        f"    # Prepare User for connection",
        f"    user_data = {generate_data_to_access()}",
        f"    user = schemas.User(**user_data)",
        f"    db.add(user)",
        f"    db.commit()",
        f"",
        f"    token = security.create_access_token({generate_create_access()})",
    ]


def generate_bearer(other_config: schemas.OtherConfigSchema) -> List[str]:
    if not other_config.use_authentication:
        return []
    return [
        f"        headers={generate_headers()},",
    ]


def generate_test_api(model: ClassModel, table_name: str, other_config: schemas.OtherConfigSchema) -> str:
    """Generate test functions for API operations (create, update, delete, get, get_by_id)."""
    test_name = camel_to_snake(model.name)
    class_lines = []

    for test_key in TEST_LIST:
        test_lines = [f"\n\ndef test_{test_key}_{table_name}_api(client, db):"]

        # Generate access token setup if authentication is enabled
        if other_config.use_authentication:
            test_lines.extend(generate_access_token(other_config))

        if test_key == "create":
            # Test for creating a new record via API
            data = [
                f"    {test_name}_data = {generate_column(model.attributes)}",
                f"    response = client.post(",
                f"        '/api/v1/{table_name}/',",
                f"        json={test_name}_data,",
                *generate_bearer(other_config),
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
                f"    # Create a record first",
                f"    {test_name}_data = {generate_column(model.attributes)}",
                f"    create_response = client.post(",
                f"        '/api/v1/{table_name}/',",
                f"        json={test_name}_data,",
                *generate_bearer(other_config),
                f"    )",
                f"    assert create_response.status_code == 200, create_response.text",
                f"    created_{test_name} = create_response.json()",
                f"",
                f"    # Update the record",
                f"    update_data = {generate_column(model.attributes)}",
                f"    update_response = client.put(",
                f"        '/api/v1/{table_name}/',",
                f"        params={{'{table_name}_id': created_{test_name}['id']}},",
                f"        json=update_data,",
                *generate_bearer(other_config),
                f"    )",
                f"    assert update_response.status_code == 200, update_response.text",
                f"    updated_{test_name} = update_response.json()",
                f"    assert updated_{test_name}['id'] == created_{test_name}['id']",
                f"    assert updated_{test_name} != created_{test_name}  # Ensure the record was updated"
            ]
            test_lines.extend(data)

        elif test_key == "get":
            # Test for retrieving all records via API
            data = [
                f"    # Create a record first",
                f"    {test_name}_data = {generate_column(model.attributes)}",
                f"    create_response = client.post(",
                f"        '/api/v1/{table_name}/',",
                f"        json={test_name}_data,",
                *generate_bearer(other_config),
                f"    )",
                f"    assert create_response.status_code == 200, create_response.text",
                f"    created_{test_name} = create_response.json()",
                f"",
                f"    # Retrieve all records",
                f"    get_response = client.get(",
                f"        '/api/v1/{table_name}/',",
                *generate_bearer(other_config),
                f"    )",
                f"    assert get_response.status_code == 200, get_response.text",
                f"    records = get_response.json()",
                f"    assert len(records['data']) > 0",
                f"    assert any(record['id'] == created_{test_name}['id'] for record in records['data'])"
            ]
            test_lines.extend(data)

        elif test_key == "get_by_id":
            # Test for retrieving a record by its ID via API
            data = [
                f"    # Create a record first",
                f"    {test_name}_data = {generate_column(model.attributes)}",
                f"    create_response = client.post(",
                f"        '/api/v1/{table_name}/',",
                f"        json={test_name}_data,",
                *generate_bearer(other_config),
                f"    )",
                f"    assert create_response.status_code == 200, create_response.text",
                f"    created_{test_name} = create_response.json()",
                f"",
                f"    # Retrieve the record by ID",
                f"    get_response = client.get(",
                f"        f'/api/v1/{table_name}/by_id/?{table_name}_id={{created_{test_name}['id']}}',",
                *generate_bearer(other_config),
                f"    )",
                f"    assert get_response.status_code == 200, get_response.text",
                f"    retrieved_{test_name} = get_response.json()",
                f"    assert retrieved_{test_name}['id'] == created_{test_name}['id']",
                f"    assert retrieved_{test_name} == created_{test_name}"
            ]
            test_lines.extend(data)

        elif test_key == "delete":
            # Test for deleting a record via API
            data = [
                f"    # Create a record first",
                f"    {test_name}_data = {generate_column(model.attributes)}",
                f"    create_response = client.post(",
                f"        '/api/v1/{table_name}/',",
                f"        json={test_name}_data,",
                *generate_bearer(other_config),
                f"    )",
                f"    assert create_response.status_code == 200, create_response.text",
                f"    created_{test_name} = create_response.json()",
                f"",
                f"    # Delete the record",
                f"    delete_response = client.delete(",
                f"        f'/api/v1/{table_name}/?{table_name}_id={{created_{test_name}['id']}}',",
                *generate_bearer(other_config),
                f"    )",
                f"    assert delete_response.status_code == 200, delete_response.text",
                f"    deleted_{test_name} = delete_response.json()",
                f"    assert deleted_{test_name}['id'] == created_{test_name}['id']",
                f"",
                f"    # Ensure the record is no longer retrievable",
                f"    get_response = client.get(",
                f"        f'/api/v1/{table_name}/by_id/?{table_name}_id={{created_{test_name}['id']}}',",
                *generate_bearer(other_config),
                f"    )",
                f"    assert get_response.status_code == 404, get_response.text"
            ]
            test_lines.extend(data)

        class_lines.extend(test_lines)

    return "\n".join(class_lines)


def generate_full_schema(model: ClassModel, table_name: str, other_config: schemas.OtherConfigSchema) -> str:
    """Generate the full schema for a model, including imports and test functions."""
    return "\n".join([
        generate_import(other_config),
        generate_test_api(model, table_name, other_config),
    ])


def write_test_apis(models: List[ClassModel], output_dir: str, other_config: schemas.OtherConfigSchema) -> None:
    """Write the generated schemas to files, preserving custom sections."""
    output_dir = output_dir + OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    for model in models:
        try:
            model = ClassModel(**model)
            table_name = camel_to_snake(model.name)
            schemas = generate_full_schema(model, table_name, other_config)
            file_name = f"test_{table_name}_api.py"
            file_path = os.path.join(output_dir, file_name)

            # Preserve custom sections in the file
            final_content = preserve_custom_sections(file_path, schemas)

            with open(file_path, "w") as f:
                f.write(final_content)
            logger.info(f"Generated test API for: {table_name}")
        except Exception as e:
            logger.error(f"Failed to generate test API for {model.name}: {e}")


def main(models: List[ClassModel], other_config: schemas.OtherConfigSchema, output_dir: str = None) -> None:
    """Main function to generate and write test APIs for all models."""
    if output_dir is None:
        output_dir = os.getcwd()
    write_test_apis(models, output_dir, other_config)