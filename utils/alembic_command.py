import json
import os
import sys
from alembic import command
from alembic.config import Config

from utils.move_migrations_versions import move_migration_files

DEFAULT_PATH = "alembic/versions/"


def run_migrations(message: str):
    # Lire le fichier de configuration
    with open("config.json") as f:
        config_data = json.load(f)

    # Set the PYTHONPATH environment variable
    os.environ["PYTHONPATH"] = config_data["new_project_path"]

    # Chemins des répertoires
    local_directory = DEFAULT_PATH
    remote_directory = config_data["new_project_path"] + "/" + DEFAULT_PATH
    print(remote_directory)
    # Déplacer les fichiers
    move_migration_files(remote_directory, local_directory)

    # Charger la configuration Alembic
    alembic_cfg = Config("alembic.ini")

    # Créer une nouvelle migration avec autogenerate
    print("Création de la migration...")
    command.revision(alembic_cfg, autogenerate=True, message=message)

    # Appliquer les migrations
    print("Application des migrations...")
    command.upgrade(alembic_cfg, "head")

    print("Migrations terminées avec succès !")

    # Déplacer les fichiers
    move_migration_files(local_directory, remote_directory)
