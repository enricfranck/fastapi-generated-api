import os
import shutil
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware

from generate_base_file import write_base_files
from generate_crud import write_crud
from generate_endpoints import write_endpoints
from generate_env import generate_env
from generate_init_file import write_init_files
from generate_models import write_models
from generate_schema import write_schemas
from model_type import ClassModel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (you can specify specific origins instead of "*")
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)


class Project(BaseModel):
    name: str
    class_model: List[ClassModel]


def set_full_permissions(directory: str):
    """Set full permissions (rwx) for all users (owner, group, others)."""
    try:
        os.chmod(directory, 0o777)  # 0o777 = rwx for owner, group, and others
        print(f"Set full permissions for directory: {directory}")
    except Exception as e:
        print(f"Failed to set permissions for directory {directory}: {e}")


@app.post("/project")
async def create_project(
        path: str,
        body: Project
):
    template_dir = os.path.join(os.path.dirname(__file__), "fastapi_template")
    destination_dir = os.path.join(path, body.name)

    config = {
        "DOMAIN": "localhost",
        "STACK_NAME": f"{body.name.lower()}-com",
        "SERVER_NAME": f"http://{body.name.lower()}-com",
        "SERVER_HOST": f"http://{body.name.lower()}-com",
        "DOCKER_IMAGE_BACKEND": "backend",
        "BACKEND_CORS_ORIGINS": '["http://localhost","http://localhost:8070", "http://localhost:4200","http://localhost:8080", "https://localhost:3000", "http://192.168.88.60:4200", "http://127.0.0.1:8080"]',
        "PROJECT_NAME": f"{body.name.title()}",
        "SECRET_KEY": "tzrctxhgdc876guyguv6v",
        "FIRST_SUPERUSER": f"admin@{body.name.lower()}.com",
        "FIRST_NAME_SUPERUSER": "",
        "LAST_NAME_SUPERUSER": "",
        "FIRST_SUPERUSER_PASSWORD": "aze135azq35sfsnf6353sfh3xb68yyp31gf68k5sf6h3s5d68jd5",
        "SMTP_TLS": "True",
        "SMTP_PORT": "",
        "SMTP_HOST": "",
        "SMTP_USER": "",
        "SMTP_PASSWORD": "",
        "SMTP_SERVER": "smtp.gmail.com",
        "EMAILS_FROM_EMAIL": "",
        "MYSQL_HOST": "localhost",
        "MYSQL_PORT": "",
        "MYSQL_USER": "",
        "MYSQL_ROOT_USER": "",
        "MYSQL_ROOT_PASSWORD": "",
        "MYSQL_PASSWORD": "",
        "MYSQL_DATABASE": "test",
        "MYSQL_ROOT_HOST": "%",
    }

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
                generate_env(config, output_file=destination_dir + "/.env")

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
        generate_env(config, output_file=destination_dir + "/.env")

    except FileExistsError:
        print("Error: Directory already exists.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return destination_dir
