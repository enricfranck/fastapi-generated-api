import os

from sqlalchemy.orm import DeclarativeMeta

OUTPUT_DIR = "fastapi_template/app/crud"


def snake_to_camel(name):
    """Convert snake_case to CamelCase."""
    return "".join(word.capitalize() for word in name.split("_"))


def generate_crud(model_name, table_name):
    """Generate a CRUD class for a given model."""
    schema_create = f"{snake_to_camel(table_name)}Create"
    schema_update = f"{snake_to_camel(table_name)}Update"
    crud_class_name = f"CRUD{snake_to_camel(table_name)}"

    crud_lines_import = [
        "from typing import Optional",
        "from sqlalchemy.orm import Session",
        "",
        f"from app.crud.base import CRUDBase",
        f"from app.models.{table_name} import {model_name}",
        f"from app.schemas.{table_name} import {schema_create}, {schema_update}",
        "",
    ]

    if table_name == "user":
        crud_lines_import.append(
            f"from app.core.security import get_password_hash, verify_password",
        )
        crud_lines_import.append(
            "from typing import Any, Dict, Union, List \n",
        )

    crud_lines_class = [
        f"\nclass {crud_class_name}(CRUDBase[{model_name}, {schema_create}, {schema_update}]):",
    ]

    crud_lines_function_user = [
        f"    def get_by_email(self, db: Session, *, email: str) -> Optional[{model_name}]:",
        f"        return db.query({model_name}).filter({model_name}.email == email).first()",
        "",
        f"    def create(self, db: Session, *, obj_in: {model_name}Create) -> {model_name}:",
        f"        db_obj = {model_name}(",
        "               email=obj_in.email,",
        "               hashed_password=get_password_hash(obj_in.password),",
        "               first_name=obj_in.first_name,",
        "               last_name=obj_in.last_name,",
        "               is_admin=obj_in.is_admin,",
        "               role_id=obj_in.role_id,",
        "               is_superuser=obj_in.is_superuser,",
        "               )",
        "        db.add(db_obj)",
        "        db.commit()",
        "        db.refresh(db_obj)",
        "        return db_obj",
        "",
        "    def update(",
        f"           self, db: Session, *, db_obj: User, obj_in: Union[{model_name}Update, Dict[str, Any]]",
        f"    ) -> {model_name}:",
        "        if isinstance(obj_in, dict):",
        "            update_data = obj_in",
        "        else:",
        "            update_data = obj_in.dict(exclude_unset=True)",
        "        if 'password' in update_data:",
        "            hashed_password = get_password_hash(update_data['password'])",
        "            del update_data['password']",
        "            update_data['hashed_password'] = hashed_password",
        "        return super().update(db, db_obj=db_obj, obj_in=update_data)",
        "",
        f"    def is_superuser(self, {table_name}_: {model_name}) -> bool:",
        f"        return {table_name}_.is_superuser",
        "",
        f"    def is_active(self, {table_name}_: {model_name}) -> bool:",
        f"        return {table_name}_.is_active",
        "",
        "",

    ]

    crud_lines_function = [
        f"    def get_by_id(self, db: Session, *, id: int) -> Optional[{model_name}]:",
        f"        return db.query({model_name}).filter({model_name}.id == id).first()",
        "",
        "",
    ] if table_name != "user" else crud_lines_function_user

    crud_line_return = [
        f"{table_name} = {crud_class_name}({model_name})",
        "",

    ]

    crud_lines = crud_lines_import + crud_lines_class + crud_lines_function + crud_line_return
    return "\n".join(crud_lines)


def generate_full_crud(table_name):
    """Generate the full schema for a model."""
    class_name = f"{snake_to_camel(table_name)}"

    schema_lines = [
        generate_crud(class_name, table_name)
    ]
    return "\n".join(schema_lines)


def write_crud(models, output_dir=OUTPUT_DIR):
    """Write the generated schemas to files."""
    os.makedirs(output_dir, exist_ok=True)
    for model in models:
        table_name = model.__tablename__
        schemas = generate_full_crud(table_name)
        file_name = f"crud_{table_name}.py"
        with open(os.path.join(output_dir, file_name), "w") as f:
            f.write(schemas)
        print(f"Generated schemas for: {table_name}")


if __name__ == "__main__":
    # Import your models
    from app.db.base import Base  # Update this path to your models

    # Get all SQLAlchemy models from the Base metadata
    models = [
        obj
        for obj in Base.registry._class_registry.values()
        if isinstance(obj, DeclarativeMeta) and hasattr(obj, "__tablename__")
    ]

    write_crud(models)
