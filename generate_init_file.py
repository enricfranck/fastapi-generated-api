import os


def snake_to_camel(snake_str):
    """Convert snake_case string to CamelCase."""
    return ''.join(word.capitalize() for word in snake_str.split('_'))


def generate_init_file(folder, folder_type: str = "schemas"):
    """Generate an __init__.py file to import schema classes from each file."""
    lines = []
    for file_name in os.listdir(folder):
        if file_name.endswith(".py") and file_name != "__init__.py" and file_name != "base.py":
            module_name = file_name.replace(".py", "")
            class_name = snake_to_camel(module_name)
            if folder_type == "schemas":
                lines.append(
                    f"from .{module_name} import ( \n  {class_name},  \n  {class_name}Create,  \n  {class_name}Update,  \n  Response{class_name}\n)")
            elif folder_type == "models":
                lines.append(
                    f"from .{module_name} import {class_name}")
            else:
                module_name = file_name.replace(".py", "").replace("crud_", '')
                lines.append(
                    f"from .crud_{module_name} import {module_name}")


    # Join all import statements with a newline and add a final newline
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    schema_folder = "app/schemas"
    models_folder = "app/models"
    crud_folder = "app/crud"

    # Generate __init__.py content
    init_content_schemas = generate_init_file(schema_folder, "schemas")

    # Write the content to __init__.py
    with open(os.path.join(schema_folder, "__init__.py"), "w") as init_file_schemas:
        init_file_schemas.write(init_content_schemas)

    init_content_models = generate_init_file(models_folder, "models")

    # Write the content to __init__.py
    with open(os.path.join(models_folder, "__init__.py"), "w") as init_file_models:
        init_file_models.write(init_content_models)

    init_content_crud = generate_init_file(crud_folder, "crud")

    # Write the content to __init__.py
    with open(os.path.join(crud_folder, "__init__.py"), "w") as init_file_crud:
        init_file_crud.write(init_content_crud)

    print("Successfully generated __init__.py!")
