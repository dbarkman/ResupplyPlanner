import os
from dotenv import load_dotenv

# Load environment variables from a .env file at the root of the project
load_dotenv()

def get_config(key: str) -> str:
    """
    Retrieves a configuration value from the environment.

    This function fetches a value based on its key from the environment
    variables. It enforces a strict policy where the configuration key
    must be present. If the key is not found, it raises a ValueError,
    ensuring that the application does not run with missing configuration.

    Args:
        key: The string name of the configuration variable to retrieve.

    Returns:
        The configuration value as a string.

    Raises:
        ValueError: If the configuration key is not found in the environment.
    """
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Error: Configuration key '{key}' not found in .env file.")
    return value
