import os
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import inspect

OUTPUT_DIR = "fastapi_template/app/schemas"


def snake_to_camel(name):
    """Convert snake_case to CamelCase."""
    return "".join(word.capitalize() for word in name.split("_"))


def get_column_type(column):
    """Map SQLAlchemy column types to Pydantic types."""
    python_type = column.type.python_type
    if python_type == int:
        return "int"
    elif python_type == str:
        return "str"
    elif python_type == bool:
        return "bool"
    elif python_type == float:
        return "float"
    elif "datetime" in str(python_type):
        return "datetime"
    else:
        return "Any"


def generate_import(model):
    """Generate the User schema class with all relationships."""
    schema_lines = [f"from datetime import time \nfrom datetime import date \nfrom datetime import datetime \nfrom typing import List, Optional \nfrom pydantic import "
                    f"BaseModel, EmailStr"]

    # Inspect relationships in the model
    for relationship in inspect(model).relationships:
        related_model = relationship.mapper.class_.__name__
        relationship_name = relationship.key
        schema_lines.append(f"from .{relationship_name} import {related_model}")

    schema_lines.append("")  # Add a blank line at the end
    return "\n".join(schema_lines)


def generate_base_schema(model, table_name):
    """Generate the base schema class."""
    schema_name = f"{snake_to_camel(table_name)}Base"
    schema_lines = [f"\nclass {schema_name}(BaseModel):"]
    for column in inspect(model).columns.values():
        column_type = get_column_type(column)
        is_optional = column.nullable or column.default is not None
        default_value = " = None" if is_optional else ""
        schema_lines.append(f"    {column.name}: Optional[{column_type}]{default_value}")
    schema_lines.append("")
    return "\n".join(schema_lines)


def generate_create_schema(model, base_schema, table_name):
    """Generate the create schema class."""
    schema_name = f"{snake_to_camel(table_name)}Create"
    schema_lines = [f"\nclass {schema_name}({base_schema}):"]

    # Add required fields (nullable=False and no default value)
    for column in inspect(model).columns.values():
        if not column.nullable and column.default is None and not column.primary_key:
            column_type = get_column_type(column)
            schema_lines.append(f"    {column.name}: {column_type}")
    if len(schema_lines) == 1:
        schema_lines.append(f"    pass")

    schema_lines.append("")  # Add a blank line at the end
    return "\n".join(schema_lines)


def generate_update_schema(base_schema, table_name):
    """Generate the update schema class."""
    schema_name = f"{snake_to_camel(table_name)}Update"
    schema_lines = [
        f"\nclass {schema_name}({base_schema}):",
        "    pass",
        "",
    ]
    return "\n".join(schema_lines)


def generate_in_db_base_schema(model, base_schema, table_name):
    """Generate the InDBBase schema class with all foreign keys."""
    schema_name = f"{snake_to_camel(table_name)}InDBBase"
    schema_lines = [f"\nclass {schema_name}({base_schema}):"]

    # Add primary key field
    schema_lines.append("    id: Optional[int]")

    # Inspect columns for foreign keys
    for column in inspect(model).columns.values():
        if column.foreign_keys:  # Check if the column has foreign key constraints
            column_type = get_column_type(column)
            schema_lines.append(f"    {column.name}: Optional[{column_type}]")

    schema_lines.append("")
    schema_lines.append("    class Config:")
    schema_lines.append("        orm_mode = True")
    schema_lines.append("")

    return "\n".join(schema_lines)


def generate_model_class(model, in_db_base_schema, table_name):
    """Generate the User schema class with all relationships."""
    schema_name = snake_to_camel(table_name)
    schema_lines = [f"\nclass {schema_name}({in_db_base_schema}):"]

    # Inspect relationships in the model
    for relationship in inspect(model).relationships:
        related_model = relationship.mapper.class_.__name__
        relationship_name = relationship.key
        is_list = relationship.uselist  # Check if it's a one-to-many/many-to-many relationship

        if is_list:
            schema_lines.append(f"    {relationship_name}: Optional[List[{related_model}]] = None")
        else:
            schema_lines.append(f"    {relationship_name}: Optional[{related_model}] = None")

    schema_lines.append("")  # Add a blank line at the end
    return "\n".join(schema_lines)


def generate_in_db_class(in_db_base_schema, table_name):
    """Generate the UserInDB schema class."""
    schema_name = f"{snake_to_camel(table_name)}InDB"
    schema_lines = [
        f"\nclass {schema_name}({in_db_base_schema}):",
        "    pass",
        "",
    ]
    return "\n".join(schema_lines)


def generate_response_class(class_name, table_name):
    schema_name = f"Response{snake_to_camel(table_name)}"
    """Generate the Response schema class."""
    schema_lines = [
        f"\nclass {schema_name}(BaseModel):",
        "    count: int",
        f"    data: Optional[List[{class_name}]]",
        "",
    ]
    return "\n".join(schema_lines)


def generate_full_schema(model, table_name):
    """Generate the full schema for a model."""
    base_schema = f"{snake_to_camel(table_name)}Base"
    in_db_base_schema = f"{snake_to_camel(table_name)}InDBBase"
    class_name = f"{snake_to_camel(table_name)}"

    schema_lines = [
        generate_import(model),
        generate_base_schema(model, table_name),
        generate_create_schema(model, base_schema, table_name),
        generate_update_schema(base_schema, table_name),
        generate_in_db_base_schema(model, base_schema, table_name),
        generate_model_class(model, in_db_base_schema, table_name),
        generate_in_db_class(in_db_base_schema, table_name),
        generate_response_class(class_name, table_name),
    ]
    return "\n".join(schema_lines)


def write_schemas(models, output_dir=OUTPUT_DIR):
    """Write the generated schemas to files."""
    os.makedirs(output_dir, exist_ok=True)
    for model in models:
        table_name = model.__tablename__
        schemas = generate_full_schema(model, table_name)
        file_name = f"{table_name}.py"
        with open(os.path.join(output_dir, file_name), "w") as f:
            f.write(schemas)
        print(f"Generated schemas for: {table_name}")


if __name__ == "__main__":
    # Import your models
    from app.db.base import Base, User, Role  # Update this path to your models

    # Get all SQLAlchemy models from the Base metadata
    models = [
        obj
        for obj in Base.registry._class_registry.values()
        if isinstance(obj, DeclarativeMeta) and hasattr(obj, "__tablename__")
    ]

    write_schemas(models)
