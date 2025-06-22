import os
import logging
from typing import List, Dict, Any

from schemas import ClassModel, AttributesModel
from model_type import preserve_custom_sections, camel_to_snake
from utils.generate_data_test import generate_data, generate_column

# Configuration
OUTPUT_DIR = "/tests"
TEST_LIST = ["create", "update", "get", "get_by_id", "delete"]

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_import(model: ClassModel) -> str:
    """Generate the necessary imports for the test."""
    imports = [
        "from fastapi import status",
        "from app import crud, schemas",
        "from sqlalchemy.orm import Session",
        "from typing import Any, Dict",
        "import pytest"
    ]
    return "\n".join(imports)



def generate_test_crud(model: ClassModel, table_name: str) -> str:
    """Generate test functions for CRUD operations."""
    test_name = camel_to_snake(model.name)
    class_lines = []

    # Add docstring
    class_lines.append(f'"""Tests for CRUD operations on {model.name} model."""')

    for test_key in TEST_LIST:
        test_lines = [f"\n\ndef test_{test_key}_{table_name}(db: Session):"]
        test_lines.append(f'    """Test {test_key} operation for {model.name}."""')

        test_data = generate_column(model.attributes)
        schema_create = f"schemas.{model.name}Create"
        schema_update = f"schemas.{model.name}Update"

        if test_key == "create":
            test_lines.extend([
                f"    # Test data",
                f"    {test_name}_data = {schema_create}(**{test_data})",
                f"",
                f"    # Create record",
                f"    {test_name} = crud.{table_name}.create(db=db, obj_in={test_name}_data)",
                f"",
                f"    # Assertions",
                f"    assert {test_name}.id is not None",
                *[f"    assert {test_name}.{attr.name} == {test_name}_data.{attr.name}"
                  for attr in model.attributes if attr.is_required and attr.name != "id"]
            ])

        elif test_key == "update":
            test_lines.extend([
                f"    # Create initial record",
                f"    create_data = {schema_create}(**{test_data})",
                f"    {test_name} = crud.{table_name}.create(db=db, obj_in=create_data)",
                f"    assert {test_name}.id is not None",
                f"",
                f"    # Update data",
                f"    update_data = {schema_update}(**{{",
                f"        k: (not v) if isinstance(v, bool) else",
                f"           (v + 1) if isinstance(v, (int, float)) else",
                f"           f'updated_{{v}}'",
                f"        for k, v in {test_data}.items()",
                f"    }})",
                f"    updated_{test_name} = crud.{table_name}.update(",
                f"        db=db, db_obj={test_name}, obj_in=update_data)",
                f"",
                f"    # Assertions",
                f"    assert updated_{test_name}.id == {test_name}.id",
                *[
                    f"    assert updated_{test_name}.{attr.name} != {test_name}.{attr.name}"
                    for attr in model.attributes
                    if attr.is_required and attr.name != "id"
                ]
            ])


        elif test_key == "get":
            test_lines.extend([
                f"    # Create test record",
                f"    {test_name}_data = {schema_create}(**{test_data})",
                f"    {test_name} = crud.{table_name}.create(db=db, obj_in={test_name}_data)",
                f"    assert {test_name}.id is not None",
                f"",
                f"    # Get all records",
                f"    records = crud.{table_name}.get_multi_where_array(db=db)",
                f"",
                f"    # Assertions",
                f"    assert len(records) > 0",
                f"    assert any(record.id == {test_name}.id for record in records)"
            ])

        elif test_key == "get_by_id":
            test_lines.extend([
                f"    # Create test record",
                f"    {test_name}_data = {schema_create}(**{test_data})",
                f"    {test_name} = crud.{table_name}.create(db=db, obj_in={test_name}_data)",
                f"    assert {test_name}.id is not None",
                f"",
                f"    # Get by ID",
                f"    retrieved_{test_name} = crud.{table_name}.get(db=db, id={test_name}.id)",
                f"",
                f"    # Assertions",
                f"    assert retrieved_{test_name} is not None",
                f"    assert retrieved_{test_name}.id == {test_name}.id",
                *[f"    assert retrieved_{test_name}.{attr.name} == {test_name}.{attr.name}"
                  for attr in model.attributes if attr.is_required and attr.name != "id"]
            ])

        elif test_key == "delete":
            test_lines.extend([
                f"    # Create test record",
                f"    {test_name}_data = {schema_create}(**{test_data})",
                f"    {test_name} = crud.{table_name}.create(db=db, obj_in={test_name}_data)",
                f"    assert {test_name}.id is not None",
                f"",
                f"    # Delete record",
                f"    deleted_{test_name} = crud.{table_name}.remove(db=db, id={test_name}.id)",
                f"",
                f"    # Assertions",
                f"    assert deleted_{test_name} is not None",
                f"    assert deleted_{test_name}.id == {test_name}.id",
                f"",
                f"    # Verify deletion",
                f"    retrieved_{test_name} = crud.{table_name}.get(db=db, id={test_name}.id)",
                f"    assert retrieved_{test_name} is None"
            ])

        class_lines.extend(test_lines)

    return "\n".join(class_lines)


def generate_full_schema(model: ClassModel, table_name: str) -> str:
    """Generate the full test file content."""
    content = [
        generate_import(model),
        generate_test_crud(model, table_name),
    ]
    return "\n".join(content)


def write_test_crud(models: List[ClassModel], output_dir: str) -> None:
    """Write the generated test files."""
    full_output_dir = os.path.join(output_dir, OUTPUT_DIR.lstrip('/'))
    os.makedirs(full_output_dir, exist_ok=True)

    for model in models:
        try:
            model = ClassModel(**model)
            table_name = camel_to_snake(model.name)
            content = generate_full_schema(model, table_name)
            file_name = f"test_crud_{table_name}.py"
            file_path = os.path.join(full_output_dir, file_name)

            # Preserve any custom sections in existing files
            final_content = preserve_custom_sections(file_path, content)

            with open(file_path, "w") as f:
                f.write(final_content)
            logger.info(f"Generated CRUD tests for: {table_name}")
        except Exception as e:
            logger.error(f"Failed to generate CRUD tests for {model.name}: {e}")
            raise


def main(models: List[ClassModel], output_dir: str = None) -> None:
    """Main entry point for test generation."""
    if output_dir is None:
        output_dir = os.getcwd()
    write_test_crud(models, output_dir)


if __name__ == "__main__":
    # Example usage
    pass