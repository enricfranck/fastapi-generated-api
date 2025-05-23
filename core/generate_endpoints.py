import os
from typing import List

from schemas import ClassModel
from sqlalchemy.orm import DeclarativeMeta

from model_type import  snake_to_camel, camel_to_snake

OUTPUT_DIR = "/app/api/api_v1/endpoints"


def generate_router_file(table_name):
    """Generate a FastAPI router file for CRUD operations."""
    schema_name = snake_to_camel(table_name)
    router_name = table_name
    crud_name = table_name
    response_model_name = f"Response{schema_name}"

    router_lines = [
        "from typing import Any",
        "from fastapi import APIRouter, Depends, HTTPException",
        "from fastapi.encoders import jsonable_encoder",
        "from sqlalchemy.orm import Session",
        "",
        "from app import crud, models, schemas",
        "from app.api import deps",
        "",
        f"router = APIRouter()",
        "",
        "",
        f"@router.get('/', response_model=schemas.{response_model_name})",
        f"def read_{router_name}s(",
        "        db: Session = Depends(deps.get_db),",
        "        current_user: models.User = Depends(deps.get_current_active_user),",
        ") -> Any:",
        f"    \"\"\"",
        f"    Retrieve {router_name}s.",
        f"    \"\"\"",
        f"    {router_name}s = crud.{crud_name}.get_multi_where_array(db=db)",
        f"    count = crud.{crud_name}.get_count_where_array(db=db)",
        f"    response = schemas.{response_model_name}(**{{'count': count, 'data': jsonable_encoder({router_name}s)}})",
        "    return response",
        "",
        "",
        f"@router.post('/', response_model=schemas.{schema_name})",
        f"def create_{router_name}(",
        "        *,",
        "        db: Session = Depends(deps.get_db),",
        f"        {router_name}_in: schemas.{schema_name}Create,",
        "        current_user: models.User = Depends(deps.get_current_active_user),",
        ") -> Any:",
        f"    \"\"\"",
        f"    Create new {router_name}.",
        f"    \"\"\"",
        "    if crud.user.is_superuser(current_user):",
        f"        {router_name} = crud.{crud_name}.create(db=db, obj_in={router_name}_in)",
        "    else:",
        "        raise HTTPException(status_code=400, detail='Not enough permissions')",
        f"    return {router_name}",
        "",
        "",
        f"@router.put('/', response_model=schemas.{schema_name})",
        f"def update_{router_name}(",
        "        *,",
        "        db: Session = Depends(deps.get_db),",
        f"        {router_name}_id: int,",
        f"        {router_name}_in: schemas.{schema_name}Update,",
        "        current_user: models.User = Depends(deps.get_current_active_user),",
        ") -> Any:",
        f"    \"\"\"",
        f"    Update an {router_name}.",
        f"    \"\"\"",
        f"    {router_name} = crud.{crud_name}.get(db=db, id={router_name}_id)",
        f"    if not {router_name}:",
        f"        raise HTTPException(status_code=404, detail='{schema_name} not found')",
        f"    {router_name} = crud.{crud_name}.update(db=db, db_obj={router_name}, obj_in={router_name}_in)",
        f"    return {router_name}",
        "",
        "",
        f"@router.get('/by_id/', response_model=schemas.{schema_name})",
        f"def read_{router_name}(",
        "        *,",
        "        db: Session = Depends(deps.get_db),",
        f"        {router_name}_id: int,",
        "        current_user: models.User = Depends(deps.get_current_active_user),",
        ") -> Any:",
        f"    \"\"\"",
        f"    Get {router_name} by ID.",
        f"    \"\"\"",
        f"    {router_name} = crud.{crud_name}.get(db=db, id={router_name}_id)",
        f"    if not {router_name}:",
        f"        raise HTTPException(status_code=404, detail='{schema_name} not found')",
        f"    return {router_name}",
        "",
        "",
        f"@router.delete('/', response_model=schemas.{schema_name})",
        f"def delete_{router_name}(",
        "        *,",
        "        db: Session = Depends(deps.get_db),",
        f"        {router_name}_id: int,",
        "        current_user: models.User = Depends(deps.get_current_active_user),",
        ") -> Any:",
        f"    \"\"\"",
        f"    Delete an {router_name}.",
        f"    \"\"\"",
        f"    {router_name} = crud.{crud_name}.get(db=db, id={router_name}_id)",
        f"    if not {router_name}:",
        f"        raise HTTPException(status_code=404, detail='{schema_name} not found')",
        f"    {router_name} = crud.{crud_name}.remove(db=db, id={router_name}_id)",
        f"    return {router_name}",
        "",
    ]

    return "\n".join(router_lines)


def write_endpoints(models: List[ClassModel], output_dir):
    """Write the generated schemas to files."""
    endpoints_directory = output_dir + OUTPUT_DIR
    os.makedirs(endpoints_directory, exist_ok=True)
    for model in models:
        model = ClassModel(**model)
        table_name = camel_to_snake(model.name)
        endpoints = generate_router_file(table_name)
        file_name = f"{table_name}s.py"
        with open(os.path.join(endpoints_directory, file_name), "w") as f:
            f.write(endpoints)
        print(f"Generated endpoints for: {table_name}")

    apis_directory = output_dir + "/app/api/api_v1"  # Path to endpoints directory
    output_file_path = os.path.join(apis_directory, "api.py")  # Output file path

    print(endpoints_directory)
    generate_endpoints_file(endpoints_directory, output_file_path)


def generate_endpoints_file(endpoints_dir, output_file):
    """
    Generate an `endpoints.py` file that includes all FastAPI routers from the endpoints directory.

    Args:
        endpoints_dir (str): Path to the directory containing the endpoint files.
        output_file (str): Path to the output `endpoints.py` file.
    """
    # List all Python files in the endpoints directory
    endpoint_files = [
        f[:-3] for f in os.listdir(endpoints_dir)
        if f.endswith(".py") and f != "__init__.py"
    ]

    # Generate import statements
    import_lines = [
        f"from app.api.api_v1.endpoints import {endpoint}"
        for endpoint in endpoint_files
    ]

    # Generate include_router lines
    include_router_lines = [
        f'api_router.include_router({endpoint}.router, prefix="/{endpoint}", tags=["{endpoint}"])'
        for endpoint in endpoint_files
    ]

    # Combine everything into the final script
    lines = [
        "from fastapi import APIRouter",
        "",
        *import_lines,
        "",
        "api_router = APIRouter()",
        *include_router_lines,
        "",
    ]

    # Write to the output file
    with open(output_file, "w") as f:
        f.write("\n".join(lines))

    print(f"Generated {output_file} successfully!")
