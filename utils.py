import platform
import logging
from time import sleep

HTTP_CONTENT_TYPE_JSON = {"content-type": "application/json"}


def wait_for(pred, wait_time=10, step=1):
    while wait_time:
        if pred():
            return True
        wait_time -= step
        sleep(step)
    return False


def is_linux():
    return platform.system() == "Linux"


def retry_on_failure(times, step=10):
    def _decorator(f):
        def wrapper(*args, **kwargs):
            for _ in range(times):
                try:
                    return f(*args, **kwargs)
                except Exception as exc:
                    logger = logging.getLogger("mvt_runner")
                    logger.debug(f"ERROR in function '{f.__name__}': {exc}")
                    sleep(step)
            return f(*args, **kwargs)
        return wrapper
    return _decorator
