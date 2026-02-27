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

import json
import pytest
from time import sleep, time
from utils import HTTP_CONTENT_TYPE_JSON, wait_for, retry_on_failure


class MvtDriver:
    def __init__(self, logger, stb, websocket):
        self.logger = logger
        self.stb = stb
        self.websocket = websocket
        self._load_mvt()

    def wait_until_testlist_visible(self, timeout=60):
        start = time()
        while time() - start < timeout:
            num_test = self.websocket.send_message("getNumberOfTests")
            if num_test not in ("", None):
                self.logger.debug(f"Test suite loaded with {num_test} test cases")
                return True
            sleep(1)
        raise TimeoutError("MVT test list did not become visible in time")

    @retry_on_failure(3)
    def is_js_loaded(self):
        result = self.websocket.send_message("getNumberOfTests")
        if '' == result:
            self.logger.debug(f"Test suite loaded info not available")
        else:
            self.logger.debug(f"Test suite loaded with {result} test cases")

    @retry_on_failure(3, 30)
    def _load_mvt(self):
        self.stb.key_input(95)  # Press BACK in case of CS2400
        self.stb.start_mvt_app()
        self.wait_until_testlist_visible()
        self.logger.debug("Started MVT application")


@pytest.fixture(scope="session")
def mvtdriver(test_logger, stb, websocket):
    driver = MvtDriver(test_logger, stb, websocket)
    yield driver
