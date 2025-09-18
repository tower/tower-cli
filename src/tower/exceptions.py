class NotFoundException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class UnauthorizedException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class UnknownException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class UnhandledRunStateException(Exception):
    def __init__(self, state: str):
        message = f"Run state '{state}' was unexpected. Maybe you need to upgrade to the latest Tower SDK."
        super().__init__(message)


class TimeoutException(Exception):
    def __init__(self, time: float):
        super().__init__(f"A timeout occurred after {time} seconds.")


class RunFailedError(RuntimeError):
    def __init__(self, app_name: str, number: int, state: str):
        super().__init__(f"Run {app_name}#{number} failed with status '{state}'")


class AppNotFoundError(RuntimeError):
    def __init__(self, app_name: str):
        super().__init__(f"App '{app_name}' not found in the Tower.")
