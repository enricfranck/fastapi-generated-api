import json
import os
import re

import pymysql
from pymysql import Error

from schemas import ClassModel
from schemas.project import ProjectBase


def preserve_custom_sections(file_path: str, new_content: str) -> str:
    """Preserve custom sections (e.g., # begin # .... # end #) in the file."""

    top_section_default = f"# begin #\n# ---write your code here--- #\n# end #"
    if not os.path.exists(file_path):
        return top_section_default + "\n\n" + new_content + "\n\n" + top_section_default + "\n"

    with open(file_path, "r") as f:
        existing_content = f.read()

    # Use regex to find and preserve custom sections
    section_pattern = r"#\s+begin\s+#.*?#\s+end\s+#"
    sections = re.findall(section_pattern, existing_content, re.DOTALL)

    # Ensure we have exactly two sections (top and bottom)
    if len(sections) != 2:
        return top_section_default + "\n\n" + new_content + "\n\n" + top_section_default + "\n"  # If sections are not found or
        # invalid, return new content

    top_section = sections[0]  # First section is the top
    bottom_section = sections[1]  # Second section is the bottom

    # Combine new content with preserved sections
    final_content = top_section + "\n\n" + new_content + "\n\n" + bottom_section + "\n"

    return final_content


def snake_to_camel(snake_str):
    """Convert snake_case string to CamelCase."""
    return ''.join(word.capitalize() for word in snake_str.split('_'))


def camel_to_snake(name):
    """Convert CamelCase to snake_case."""
    snake_case = ""
    for i, char in enumerate(name):
        if char.isupper() and i != 0:
            snake_case += "_"
        snake_case += char.lower()
    return snake_case


def create_or_update_mysql_user(new_user, new_password, database):
    connection = None
    try:
        # Connect to the MySQL server
        connection = pymysql.connect(
            host='localhost',
            user='fastapi',
            password="password",
            cursorclass=pymysql.cursors.DictCursor
        )

        with connection.cursor() as cursor:
            # Create the database if it does not exist
            create_database_query = f"CREATE DATABASE IF NOT EXISTS {database};"
            cursor.execute(create_database_query)
            print(f"Database '{database}' created (if it did not exist).")

            # Check if the user already exists
            check_user_query = f"SELECT User FROM mysql.user WHERE User = '{new_user}';"
            cursor.execute(check_user_query)
            result = cursor.fetchone()

            if result:
                # If the user exists, drop the user
                drop_user_query = f"DROP USER '{new_user}'@'%';"
                cursor.execute(drop_user_query)
                print(f"User '{new_user}' already exists. Dropping the user to recreate.")

            # Create the new user
            create_user_query = f"CREATE USER '{new_user}'@'%' IDENTIFIED BY '{new_password}';"
            cursor.execute(create_user_query)

            # Grant all privileges on the specified database to the new user
            grant_query = f"GRANT ALL PRIVILEGES ON {database}.* TO '{new_user}'@'%' WITH GRANT OPTION;"
            cursor.execute(grant_query)

            # Flush privileges to apply changes
            flush_query = "FLUSH PRIVILEGES;"
            cursor.execute(flush_query)

            print(f"User '{new_user}' created/updated successfully with GRANT OPTION.")

        # Commit the changes
        connection.commit()

    except Error as e:
        print(f"Error: {e}")

    finally:
        if connection:
            connection.close()
            print("MySQL connection is closed.")


def write_config(config: ProjectBase):
    config = {
        "new_project_path": config.path + "/" + config.name,
        "db": config.config['mysql_database'],
        "user": config.config['mysql_user'],
        "host": config.config['mysql_host'],
        "password": config.config['mysql_password'],
        "port": config.config['mysql_port']
    }

    # Write the configuration to a JSON file
    with open("config.json", "w") as json_file:
        json.dump(config, json_file, indent=4)
