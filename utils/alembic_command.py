import json
import os
import sys
from alembic import command
from alembic.config import Config

from utils.move_migrations_versions import move_migration_files

DEFAULT_PATH = "alembic/versions/"


def run_migrations(message: str):
    try:
        # Read the configuration file
        with open("config.json") as f:
            config_data = json.load(f)

        # Set the PYTHONPATH environment variable
        os.environ["PYTHONPATH"] = config_data["new_project_path"]

        # Paths for directories
        local_directory = DEFAULT_PATH
        remote_directory = os.path.join(config_data["new_project_path"], DEFAULT_PATH)
        print(f"Remote directory: {remote_directory}")

        # Move migration files to the local directory before running Alembic commands
        print("Moving migration files to local directory...")
        move_migration_files(remote_directory, local_directory)

        # Load Alembic configuration
        alembic_cfg = Config("alembic.ini")

        # Create a new migration with autogenerate
        print("Creating migration...")
        command.revision(alembic_cfg, autogenerate=True, message=message)

        # Apply migrations
        print("Applying migrations...")
        command.upgrade(alembic_cfg, "head")

        print("Migrations completed successfully!")

        # Move migration files back to the remote directory after Alembic commands
        print("Moving migration files back to remote directory...")
        move_migration_files(local_directory, remote_directory)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)  # Exit with a non-zero status code to indicate failure

    # Déplacer les fichiers
    # move_migration_files(local_directory, remote_directory)
