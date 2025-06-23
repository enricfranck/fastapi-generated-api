import os
import logging
from typing import List, Dict, Any, Optional, Set, Tuple

from schemas import ClassModel, AttributesModel
from model_type import preserve_custom_sections, camel_to_snake
from utils.generate_data_test import generate_data  #  ← NEW import
import datetime, uuid

# ---------------------------------------------------------------------------
# Configuration & logging
# ---------------------------------------------------------------------------
OUTPUT_DIR = "/tests"
TEST_LIST = ["create", "update", "get", "get_by_id", "delete"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers for code generation
# ---------------------------------------------------------------------------


def _literal_value(attr: AttributesModel) -> str:
    """
    Return Python *code* for a realistic value of the given column.
    No more hard-coded None!
    """
    # Give special-case values you hard-coded earlier
    if attr.name == "email":
        return "'test@example.com'"
    if attr.name == "hashed_password":
        return "'securepassword123'"

    # Let your existing generator pick something appropriate
    value = generate_data(attr.type, attr.length or 5)

    # Turn the *runtime* value into source-code text
    if isinstance(value, str):
        return repr(value)          # adds quotes & escapes
    if isinstance(value, (bool, int, float)):
        return repr(value)
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return f"datetime.{value.__class__.__name__}({value.isoformat()!r})"
    if isinstance(value, uuid.UUID):
        return f"uuid.UUID('{value}')"

    # fallback – rarely needed
    return repr(value)


def _literal_name(name: str) -> str:
    if name == "hashed_password":
        return "password"
    return name



def _build_dependency_setup_lines(
    model: ClassModel,
    all_models: Dict[str, ClassModel],
    created: Set[str],
    indent: str = "    ",
) -> Tuple[List[str], str]:
    """
    Recursively create parent FK models and emit Python test code for the current model.
    Skips auto-increment `id` fields.
    """
    lines: List[str] = []
    model_var = camel_to_snake(model.name)
    data_var = f"{model_var}_data"

    # Recurse for foreign keys
    for attr in model.attributes:
        if attr.is_foreign and attr.foreign_key_class:
            fk_model = all_models[attr.foreign_key_class]
            if fk_model.name not in created:
                fk_lines, _ = _build_dependency_setup_lines(
                    fk_model, all_models, created, indent
                )
                lines.extend(fk_lines)

    # Build the test data
    lines.append(f"{indent}# Test data for {model.name}")
    lines.append(f"{indent}{data_var} = schemas.{model.name}Create(")
    for attr in model.attributes:
        if attr.name == "id" and attr.is_auto_increment:
            continue  # ⛔️ Skip auto-incrementing primary key
        if attr.is_foreign and attr.foreign_key_class:
            fk_var = camel_to_snake(attr.foreign_key_class)
            lines.append(f"{indent}    {attr.name}={fk_var}.id,")
        else:
            lines.append(f"{indent}    {_literal_name(attr.name)}={_literal_value(attr)},")
    lines.append(f"{indent})\n")

    # Create the object using CRUD
    table_name = camel_to_snake(model.name)
    lines.append(f"{indent}{model_var} = crud.{table_name}.create(db=db, obj_in={data_var})\n")

    created.add(model.name)
    return lines, model_var


# ---------------------------------------------------------------------------
# Code-gen building blocks
# ---------------------------------------------------------------------------


def generate_import(_: ClassModel) -> str:
    """Imports that every generated test file needs."""
    return "\n".join(
        [
            "from fastapi import status",
            "from app import crud, schemas",
            "from sqlalchemy.orm import Session",
            "from typing import Any, Dict",
            "import pytest",
        ]
    )


def generate_test_crud(
    model: ClassModel, table_name: str, all_models: Dict[str, ClassModel]
) -> str:
    """Emit the five CRUD test functions, with FK-aware setup."""
    test_name = camel_to_snake(model.name)
    out: List[str] = [f'"""Tests for CRUD operations on {model.name} model."""']

    for test_key in TEST_LIST:
        lines: List[str] = [f"\n\ndef test_{test_key}_{table_name}(db: Session):"]
        lines.append(f'    """Test {test_key} operation for {model.name}."""')

        # -------------------------------------------------------------------
        # Dependency chain (creates everything, *including* {model})
        # -------------------------------------------------------------------
        dep_lines, root_var = _build_dependency_setup_lines(model, all_models, set())
        lines.extend(dep_lines)
        data_var = f"{root_var}_data"          # created inside dependency builder
        schema_update = f"schemas.{model.name}Update"

        # -------------------------------------------------------------------
        # Specific CRUD scenarios
        # -------------------------------------------------------------------
        if test_key == "create":
            lines.extend(
                [
                    "    # Assertions",
                    f"    assert {root_var}.id is not None",
                    *[
                        f"    assert {root_var}.{a.name} == {data_var}.{a.name}"
                        for a in model.attributes
                        if a.is_required and a.name != "id"
                    ],
                ]
            )

        elif test_key == "update":
            lines.extend(
                [
                    "    # Update data",
                    f"    update_data = {schema_update}(**{{",
                    "        k: (not v) if isinstance(v, bool) else",
                    "           (v + 1) if isinstance(v, (int, float)) else",
                    "           f'updated_{v}'",
                    f"        for k, v in {data_var}.dict().items() if k != 'id'",
                    "    })",
                    f"    updated_{root_var} = crud.{table_name}.update("
                    f"      db=db, db_obj={root_var}, obj_in=update_data)",
                    "",
                    "    # Assertions",
                    f"    assert updated_{root_var}.id == {root_var}.id",
                    *[
                        f"    assert updated_{root_var}.{a.name} != {root_var}.{a.name}"
                        for a in model.attributes
                        if a.is_required and a.name != 'id' and not a.is_foreign
                    ],
                ]
            )

        elif test_key == "get":
            lines.extend(
                [
                    "    # Get all records",
                    f"    records = crud.{table_name}.get_multi_where_array(db=db)",
                    "",
                    "    # Assertions",
                    "    assert len(records) > 0",
                    f"    assert any(r.id == {root_var}.id for r in records)",
                ]
            )

        elif test_key == "get_by_id":
            lines.extend(
                [
                    "    # Get by ID",
                    f"    retrieved_{root_var} = crud.{table_name}.get(db=db, id={root_var}.id)",
                    "",
                    "    # Assertions",
                    f"    assert retrieved_{root_var} is not None",
                    f"    assert retrieved_{root_var}.id == {root_var}.id",
                    *[
                        f"    assert retrieved_{root_var}.{a.name} == {root_var}.{a.name}"
                        for a in model.attributes
                        if a.is_required and a.name != 'id'
                    ],
                ]
            )

        elif test_key == "delete":
            lines.extend(
                [
                    "    # Delete record",
                    f"    deleted_{root_var} = crud.{table_name}.remove(db=db, id={root_var}.id)",
                    "",
                    "    # Assertions",
                    f"    assert deleted_{root_var} is not None",
                    f"    assert deleted_{root_var}.id == {root_var}.id",
                    "",
                    "    # Verify deletion",
                    f"    assert crud.{table_name}.get(db=db, id={root_var}.id) is None",
                ]
            )

        out.extend(lines)

    return "\n".join(out)


def generate_full_schema(
    model: ClassModel, table_name: str, all_models: Dict[str, ClassModel]
) -> str:
    """Concatenate imports + helper tests for one model into a file."""
    return "\n".join(
        [generate_import(model), generate_test_crud(model, table_name, all_models)]
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def write_test_crud(models: List[ClassModel], output_dir: str) -> None:
    """
    For every ClassModel in *models* write `tests/test_crud_<table>.py`,
    preserving any custom sections.
    """
    full_output_dir = os.path.join(output_dir, OUTPUT_DIR.lstrip("/"))
    os.makedirs(full_output_dir, exist_ok=True)

    # FIX: Normalize all models to ClassModel objects first
    normalized_models = [
        m if isinstance(m, ClassModel) else ClassModel(**m) for m in models
    ]
    all_models: Dict[str, ClassModel] = {m.name: m for m in normalized_models}

    for model in normalized_models:
        table_name = camel_to_snake(model.name)
        content = generate_full_schema(model, table_name, all_models)
        fname = f"test_crud_{table_name}.py"
        fpath = os.path.join(full_output_dir, fname)

        # Preserve custom section markers
        final_content = preserve_custom_sections(fpath, content)

        with open(fpath, "w", encoding="utf-8") as fp:
            fp.write(final_content)

        logger.info("Generated CRUD tests for %s", table_name)



def main(models: List[ClassModel], output_dir: str | None = None) -> None:
    """CLI entry point."""
    if output_dir is None:
        output_dir = os.getcwd()
    write_test_crud(models, output_dir)


if __name__ == "__main__":
    # Example usage (expects `models` already loaded):
    # main(models)
    pass
