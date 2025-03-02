def replace_cote(value: str):
    if type(value) == type([]):
        return str(value).replace("'", '"')
    return value


def generate_env(config: dict, output_file: str = ".env"):
    """
    Generate a .env file with the provided configuration values.

    Args:
        config (dict): A dictionary containing key-value pairs for the .env file.
        output_file (str): The path to the output .env file (default: .env).
    """
    with open(output_file, "w") as f:
        for key, value in config.items():
            f.write(f"{key.upper()}='{replace_cote(value)}'\n")
    print(f"Generated .env file at: {output_file}")
