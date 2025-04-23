import os
import logging
from typing import List, Dict, Any

from schemas import ClassModel, AttributesModel
from model_type import preserve_custom_sections, camel_to_snake
from utils.generate_data_test import  generate_data

# Configuration
OUTPUT_DIR = "/tests"
# OUTPUT_DIR = "/tests"
TEST_LIST = ["create", "update", "get", "get_by_id", "delete"]

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_import() -> str:
    """Generate the necessary imports for the test."""
    return "\n".join([
        "from app import crud, schemas",
        "from app.utils import pick_random_key_value",
        "from fastapi.encoders import jsonable_encoder",
    ])


def generate_column(data: List[AttributesModel]) -> Dict[str, Any]:
    """Generate column data based on model attributes."""
    result = {}
    for attr in data:
        if attr.is_required:
            result[attr.name] = generate_data(attr.type, attr.length)
    return result


def generate_test_crud(model: ClassModel, table_name: str) -> str:
    """Generate test functions for CRUD operations."""
    test_name = camel_to_snake(model.name)
    class_lines = []

    for test_key in TEST_LIST:
        test_lines = [f"\n\ndef test_{test_key}_{table_name}(db):"]

        if test_key == "create":
            # Test for creating a new record
            data = [
                f"    {test_name}_data = schemas.{model.name}Create(**{generate_column(model.attributes)})",
                f"    {test_name} = crud.{table_name}.create(db=db, obj_in={test_name}_data)",
                f"    data_json = pick_random_key_value(jsonable_encoder({test_name}_data))",
                f"    test_json = jsonable_encoder({test_name})",
                f"    assert {test_name}.id is not None",
                f"    assert test_json[data_json[0]] == data_json[1]"
            ]
            test_lines.extend(data)

        elif test_key == "update":
            # Test for updating an existing record
            data = [
                f"    # Create a record first",
                f"    {test_name}_data = schemas.{model.name}Create(**{generate_column(model.attributes)})",
                f"    {test_name} = crud.{table_name}.create(db=db, obj_in={test_name}_data)",
                f"    assert {test_name}.id is not None",
                f"",
                f"    # Update the record",
                f"    update_data = schemas.{model.name}Update(**{generate_column(model.attributes)})",
                f"    updated_{test_name} = crud.{table_name}.update(db=db, db_obj={test_name}, obj_in=update_data)",
                f"    assert updated_{test_name}.id == {test_name}.id",
                f"    assert updated_{test_name} != {test_name}  # Ensure the record was actually updated"
            ]
            test_lines.extend(data)

        elif test_key == "get":
            # Test for retrieving all records
            data = [
                f"    # Create a record first",
                f"    {test_name}_data = schemas.{model.name}Create(**{generate_column(model.attributes)})",
                f"    {test_name} = crud.{table_name}.create(db=db, obj_in={test_name}_data)",
                f"    assert {test_name}.id is not None",
                f"",
                f"    # Retrieve all records",
                f"    records = crud.{table_name}.get_multi(db=db)",
                f"    assert len(records) > 0",
                f"    assert any(record.id == {test_name}.id for record in records)"
            ]
            test_lines.extend(data)

        elif test_key == "get_by_id":
            # Test for retrieving a record by its ID
            data = [
                f"    # Create a record first",
                f"    {test_name}_data = schemas.{model.name}Create(**{generate_column(model.attributes)})",
                f"    {test_name} = crud.{table_name}.create(db=db, obj_in={test_name}_data)",
                f"    assert {test_name}.id is not None",
                f"",
                f"    # Retrieve the record by ID",
                f"    retrieved_{test_name} = crud.{table_name}.get(db=db, id={test_name}.id)",
                f"    assert retrieved_{test_name} is not None",
                f"    assert retrieved_{test_name}.id == {test_name}.id",
                f"    assert retrieved_{test_name} == {test_name}"
            ]
            test_lines.extend(data)

        elif test_key == "delete":
            # Test for deleting a record
            data = [
                f"    # Create a record first",
                f"    {test_name}_data = schemas.{model.name}Create(**{generate_column(model.attributes)})",
                f"    {test_name} = crud.{table_name}.create(db=db, obj_in={test_name}_data)",
                f"    assert {test_name}.id is not None",
                f"",
                f"    # Delete the record",
                f"    deleted_{test_name} = crud.{table_name}.remove(db=db, id={test_name}.id)",
                f"    assert deleted_{test_name} is not None",
                f"    assert deleted_{test_name}.id == {test_name}.id",
                f"",
                f"    # Ensure the record is no longer retrievable",
                f"    retrieved_{test_name} = crud.{table_name}.get(db=db, id={test_name}.id)",
                f"    assert retrieved_{test_name} is None"
            ]
            test_lines.extend(data)

        class_lines.extend(test_lines)

    return "\n".join(class_lines)


def generate_full_schema(model: ClassModel, table_name: str) -> str:
    """Generate the full test for a model, including imports and test functions."""
    return "\n".join([
        generate_import(),
        generate_test_crud(model, table_name),
    ])


def write_test_crud(models: List[ClassModel], output_dir: str) -> None:
    """Write the generated test to files, preserving custom sections."""
    output_dir = output_dir + OUTPUT_DIR

    for model in models:
        # try:
            model = ClassModel(**model)
            table_name = camel_to_snake(model.name)
            schemas = generate_full_schema(model, table_name)
            file_name = f"test_crud_{table_name}.py"
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
    write_test_crud(models, output_dir)


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