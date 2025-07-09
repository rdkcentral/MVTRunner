##
# If not stated otherwise in this file or this component's LICENSE file the
# following copyright and licenses apply:
#
# Copyright 2025 Liberty Global B.V.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##

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
