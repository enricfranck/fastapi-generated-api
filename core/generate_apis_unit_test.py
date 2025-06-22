import os
import logging
from typing import List, Dict, Any, Optional

import schemas
from schemas import ClassModel, AttributesModel

from model_type import preserve_custom_sections, camel_to_snake
from utils.generate_data_test import generate_data, generate_column

# Configuration
OUTPUT_DIR = "/tests"
TEST_LIST = ["create", "update", "get", "get_by_id", "delete"]

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_import(other_config: schemas.OtherConfigSchema) -> str:
    """Generate the necessary imports for the schema."""
    imports = [
        "from fastapi import status",
        "from app import crud, schemas",
        "import datetime",
    ]
    if other_config.use_authentication:
        imports.append("from app.core import security")
    return "\n".join(imports)


def generate_headers(other_config: schemas.OtherConfigSchema) -> str:
    """Generate headers string with authentication if needed."""
    if other_config.use_authentication:
        return 'headers={"Authorization": f"Bearer {token}"}'
    return ""


def generate_auth_setup(other_config: schemas.OtherConfigSchema) -> List[str]:
    """Generate authentication setup code if needed."""
    if not other_config.use_authentication:
        return []

    return [
        "    # Setup test user for authentication",
        "    user_data = {",
        "        'email': 'admin@example.com',",
        "        'password': 'securepassword',",
        "        'is_active': True,",
        "        'is_superuser': False",
        "    }",
        "    user = crud.user.create(db, obj_in=schemas.UserCreate(**user_data))",
        "    db.commit()",
        "",
        "    # Create access token",
        "    token = security.create_access_token(sub={'id': str(user.id), 'email': user.email})",
        ""
    ]


def generate_test_api(model: ClassModel, table_name: str, other_config: schemas.OtherConfigSchema) -> str:
    """Generate test functions for API operations."""
    test_name = camel_to_snake(model.name)
    base_endpoint = f"/api/v1/{table_name}s"
    class_lines = []

    for test_key in TEST_LIST:
        test_lines = [f"\n\ndef test_{test_key}_{table_name}_api(client, db):"]
        test_data = generate_column(model.attributes)

        # Add authentication setup if needed
        test_lines.extend(generate_auth_setup(other_config))

        if test_key == "create":
            test_lines.extend([
                f"    # Test data",
                f"    {test_name}_data = {test_data}",
                f"",
                f"    # Create request",
                f"    response = client.post(",
                f"        '{base_endpoint}/',",
                f"        json={test_name}_data,",
                f"        {generate_headers(other_config)}",
                f"    )",
                f"    assert response.status_code == status.HTTP_200_OK, response.text",
                f"    created_{test_name} = response.json()",
                f"    assert created_{test_name}['id'] is not None",
                *[f"    assert created_{test_name}['{k}'] == {test_name}_data['{k}']"
                  for k in test_data.keys() if k != 'password']
            ])

        elif test_key == "update":
            test_lines.extend([
                f"    # Create initial record",
                f"    create_data = {test_data}",
                f"    create_response = client.post(",
                f"        '{base_endpoint}/',",
                f"        json=create_data,",
                f"        {generate_headers(other_config)}",
                f"    )",
                f"    assert create_response.status_code == status.HTTP_200_OK",
                f"    created_{test_name} = create_response.json()",
                "",
                f"    # Update data",
                f"    update_data = {{k: (not v) if isinstance(v, bool) else (v + 1) if isinstance(v, (int, "
                f"    float)) else f'updated_{{v}}' for k, v in create_data.items()}}",
                f"    update_response = client.put(",
                f"        f'{base_endpoint}/{{created_{test_name}[\"id\"]}}',",
                f"        json=update_data,",
                f"        {generate_headers(other_config)}",
                f"    )",
                f"    assert update_response.status_code == status.HTTP_200_OK",
                f"    updated_{test_name} = update_response.json()",
                f"    assert updated_{test_name}['id'] == created_{test_name}['id']",
                *[f"    assert updated_{test_name}['{k}'] == update_data['{k}']"
                  for k in test_data.keys() if k != 'password']
            ])

        elif test_key == "get":
            test_lines.extend([
                f"    # Create test record",
                f"    {test_name}_data = {test_data}",
                f"    create_response = client.post(",
                f"        '{base_endpoint}/',",
                f"        json={test_name}_data,",
                f"        {generate_headers(other_config)}",
                f"    )",
                f"    assert create_response.status_code == status.HTTP_200_OK",
                f"    created_{test_name} = create_response.json()",
                f"",
                f"    # Get all records",
                f"    get_response = client.get(",
                f"        '{base_endpoint}/',",
                f"        {generate_headers(other_config)}",
                f"    )",
                f"    assert get_response.status_code == status.HTTP_200_OK",
                f"    records = get_response.json()",
                f"    assert isinstance(records, dict)",

                f"    items = records['data']",
                f"    assert isinstance(items, list)",

                f"    assert len(items) > 0",
                f"    assert any(r['id'] == created_{test_name}['id'] for r in items)"
            ])

        elif test_key == "get_by_id":
            test_lines.extend([
                f"    # Create test record",
                f"    {test_name}_data = {test_data}",
                f"    create_response = client.post(",
                f"        '{base_endpoint}/',",
                f"        json={test_name}_data,",
                f"        {generate_headers(other_config)}",
                f"    )",
                f"    assert create_response.status_code == status.HTTP_200_OK",
                f"    created_{test_name} = create_response.json()",
                f"",
                f"    # Get by ID",
                f"    get_response = client.get(",
                f"        f'{base_endpoint}/{{created_{test_name}[\"id\"]}}',",
                f"        {generate_headers(other_config)}",
                f"    )",
                f"    assert get_response.status_code == status.HTTP_200_OK",
                f"    retrieved_{test_name} = get_response.json()",
                f"    assert retrieved_{test_name}['id'] == created_{test_name}['id']",
                *[f"    assert retrieved_{test_name}['{k}'] == {test_name}_data['{k}']"
                  for k in test_data.keys() if k != 'password']
            ])

        elif test_key == "delete":
            test_lines.extend([
                f"    # Create test record",
                f"    {test_name}_data = {test_data}",
                f"    create_response = client.post(",
                f"        '{base_endpoint}/',",
                f"        json={test_name}_data,",
                f"        {generate_headers(other_config)}",
                f"    )",
                f"    assert create_response.status_code == status.HTTP_200_OK",
                f"    created_{test_name} = create_response.json()",
                f"",
                f"    # Delete record",
                f"    delete_response = client.delete(",
                f"        f'{base_endpoint}/{{created_{test_name}[\"id\"]}}',",
                f"        {generate_headers(other_config)}",
                f"    )",
                f"    assert delete_response.status_code == status.HTTP_200_OK",
                f"    deleted_{test_name} = delete_response.json()",
                f"    assert deleted_{test_name}['id'] == created_{test_name}['id']",
                f"",
                f"    # Verify deletion",
                f"    get_response = client.get(",
                f"        f'{base_endpoint}/{{created_{test_name}[\"id\"]}}',",
                f"        {generate_headers(other_config)}",
                f"    )",
                f"    assert get_response.status_code == status.HTTP_404_NOT_FOUND"
            ])

        class_lines.extend(test_lines)

    return "\n".join(class_lines)


def generate_full_schema(model: ClassModel, table_name: str, other_config: schemas.OtherConfigSchema) -> str:
    """Generate the full test file content."""
    content = [
        generate_import(other_config),
        generate_test_api(model, table_name, other_config),
    ]
    return "\n".join(content)


def write_test_apis(models: List[ClassModel], output_dir: str, other_config: schemas.OtherConfigSchema) -> None:
    """Write the generated test files."""
    full_output_dir = os.path.join(output_dir, OUTPUT_DIR.lstrip('/'))
    os.makedirs(full_output_dir, exist_ok=True)

    for model in models:
        try:
            model = ClassModel(**model)
            table_name = camel_to_snake(model.name)
            content = generate_full_schema(model, table_name, other_config)
            file_name = f"test_{table_name}_api.py"
            file_path = os.path.join(full_output_dir, file_name)

            # Preserve any custom sections in existing files
            final_content = preserve_custom_sections(file_path, content)

            with open(file_path, "w") as f:
                f.write(final_content)
            logger.info(f"Generated test API for: {table_name}")
        except Exception as e:
            logger.error(f"Failed to generate test API for {model.name}: {e}")
            raise


def main(models: List[ClassModel], other_config: schemas.OtherConfigSchema, output_dir: Optional[str] = None) -> None:
    """Main entry point for test generation."""
    if output_dir is None:
        output_dir = os.getcwd()
    write_test_apis(models, output_dir, other_config)