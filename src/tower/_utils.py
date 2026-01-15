def secret(name: str, default: str = ""):
    """
    Retrieve a secret value from environment variables.

    Args:
        name (str): The name of the secret (environment variable).
        default (str, optional): The default value to return if the secret is not found. Defaults to "".

    Returns:
        str: The value of the secret or the default value.
    """
    import os

    return os.getenv(name, default)


def param(name: str, default: str = ""):
    """
    Retrieve a parameter value from this invocation. In this implementation,
    it fetches the value from environment variables.

    Args:
        name (str): The name of the parameter (environment variable).
        default (str, optional): The default value to return if the parameter is not found. Defaults to "".

    Returns:
        str: The value of the parameter or the default value.
    """
    import os

    return os.getenv(name, default)


def parameter(name: str, default: str = ""):
    """
    Alias for param function to retrieve a parameter value from environment variables.

    Args:
        name (str): The name of the parameter (environment variable).
        default (str, optional): The default value to return if the parameter is not found. Defaults to "".

    Returns:
        str: The value of the parameter or the default value.
    """
    return param(name, default)
