import os
import shutil
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware

from core.generate_base_file import write_base_files
from core.generate_crud import write_crud
from core.generate_endpoints import write_endpoints
from core.generate_env import generate_env
from core.generate_init_file import write_init_files
from core.generate_models import write_models
from core.generate_schema import write_schemas
from schemas import ClassModel, ProjectUpdate
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends

import models, schemas, crud
from core.database import engine, get_db, Base

# Create DB tables
# Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (you can specify specific origins instead of "*")
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)


def set_full_permissions(directory: str):
    """Set full permissions (rwx) for all users (owner, group, others)."""
    try:
        os.chmod(directory, 0o777)  # 0o777 = rwx for owner, group, and others
        print(f"Set full permissions for directory: {directory}")
    except Exception as e:
        print(f"Failed to set permissions for directory {directory}: {e}")


@app.post("/project/config", response_model=schemas.ProjectResponse)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    return crud.create_project(db=db, project=project)


@app.put("/project/config", response_model=schemas.ProjectResponse)
def update_project(project_id: int, project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    project = crud.update_config(db=db, project_data=project, project_id=project_id)

    destination_dir = os.path.join(project.path, project.name)
    generate_env(project.config, output_file=destination_dir + "/.env")
    return project


@app.get("/project/", response_model=list[schemas.ProjectResponse])
def read_project(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_project(db, skip, limit)


@app.post("/project")
async def create_project(
        project_id: int,
        body: ProjectUpdate,
        db: Session = Depends(get_db),
):
    project = crud.get_project_by_id(db=db, id=project_id)
    if not project:
        return
    path = project.path
    template_dir = os.path.join(os.path.dirname(__file__), "fastapi_template")
    destination_dir = os.path.join(path, body.name)

    try:
        if os.path.exists(destination_dir):
            # If the directory already exists, set full permissions
            set_full_permissions(destination_dir)

            # Generate files in the existing directory
            write_models(body.class_model, destination_dir)
            write_schemas(body.class_model, destination_dir)
            write_crud(body.class_model, destination_dir)
            write_endpoints(body.class_model, destination_dir)
            write_init_files(destination_dir)
            write_base_files(body.class_model, destination_dir)

            if not os.path.exists(destination_dir + "/.env"):
                # Generate the .env file
                generate_env(project.config, output_file=destination_dir + "/.env")

            return destination_dir

        # Copy the template directory to the destination
        shutil.copytree(template_dir, destination_dir)

        # Set full permissions for the new directory
        set_full_permissions(destination_dir)

        # Generate files in the new directory
        write_models(body.class_model, destination_dir)
        write_schemas(body.class_model, destination_dir)
        write_crud(body.class_model, destination_dir)
        write_endpoints(body.class_model, destination_dir)
        write_init_files(destination_dir)
        write_base_files(body.class_model, destination_dir)

        # Generate the .env file
        generate_env(project.config, output_file=destination_dir + "/.env")

    except FileExistsError:
        print("Error: Directory already exists.")
    except Exception as e:
        print(f"An error occurred: {e}")
    data = crud.update_project(db=db, project_data=body, project_id=project_id)
    return data
