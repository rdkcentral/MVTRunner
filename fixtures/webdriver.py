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
try:
    import signal
    from signal import SIGALRM
    HAS_SIGNAL = True
except ImportError:
    HAS_SIGNAL = False
from time import sleep
from selenium.common.exceptions import WebDriverException, JavascriptException
from selenium.webdriver import Remote
from selenium.webdriver.common.by import By
from utils import HTTP_CONTENT_TYPE_JSON, wait_for, retry_on_failure


class WebDriver:
    def __init__(self, logger, stb):
        self.logger = logger
        self.stb = stb
        self._enable_automation()
        self._start_webdriver()
        self._connect_webdriver()
        self.logger.debug(f"Webdriver connection established: {self.stb.ip}")
        self._load_mvt()

    @staticmethod
    def signal_handler(signum, frame):
        raise Exception("Webdriver Remote end of timeout!")

    @retry_on_failure(3)
    def _connect_webdriver(self, timeout=60):
        if HAS_SIGNAL:  # "signal.SIGALRM" is not available for Windows...
            signal.signal(SIGALRM, self.signal_handler)
            signal.alarm(timeout)
        self.driver = Remote(
            desired_capabilities={
                "version": "",
                "platformName": "ANY",
                "javascriptEnabled": True,
            },
            command_executor=f"http://{self.stb.ip}:9517",
        )
        if HAS_SIGNAL:
            signal.alarm(0)

    def wait_until_element_visible(self, element_id, wait_time=15):
        while wait_time:
            try:
                self.driver.find_element(By.ID, element_id)
                return True
            except Exception as err:
                self.logger.debug(err)
            sleep(1)
            wait_time -= 1
        return False

    @retry_on_failure(3)
    def _start_webdriver(self):
        self.logger.debug("Starting webdriver on STB...")
        self.stb.shell("systemctl restart webdriver.service")
        sleep(15)
        if(False == self._is_daemon_active()):
            self.logger.debug("Webdriver is not active, retrying...")
            self.stb.shell("systemctl restart webdriver.service")
            sleep(15)
        self.logger.debug(f"Webdriver Active status = {self._is_daemon_active()}")

    def _is_daemon_active(self):
        response = self.stb.shell("systemctl status webdriver.service")
        return "Active: active" in response

    # TODO Fix race on updating config (caused by WebKit autostart)
    @retry_on_failure(10)
    def _enable_automation(self):
        self._change_webkit_config()
        config = self._fetch_webkit_config()
        assert config["automation"], "Failed to enable WebKit automation"
        if "2.22" in config["browserversion"]:
            assert config["inspector"] == "0.0.0.0:9226", "Failed to enable WebKit automation"
        self.logger.debug("Automation enabled in WebKitBrowser.json")
        sleep(5)

    @retry_on_failure(2)
    def _fetch_webkit_config(self):
        response = self.stb.http_request(9998, "Service/Controller/Configuration/WebKitBrowser").content
        return json.loads(response)

    def _change_webkit_config(self):
        config = self._fetch_webkit_config()
        if "2.22" in config["browserversion"]:
            config["inspector"] = "0.0.0.0:9226"
        config["automation"] = True
        config_json = json.dumps(config)
        self.stb.stop_webkit(clear_cache=True)
        self.stb.http_request(
            9998,
            "Service/Controller/Configuration/WebKitBrowser",
            method="PUT",
            headers=HTTP_CONTENT_TYPE_JSON,
            data=config_json,
        )
        self.logger.debug("Uploaded WebKitBrowser.json configuration")
        self.stb.start_webkit()

    @retry_on_failure(3)
    def is_js_loaded(self):
        try:
            result = self.driver.execute_script("return globalRunner.testList.length")
            self.logger.debug(f"Test suite loaded with {result} test cases")
        except (WebDriverException, JavascriptException):
            raise WebDriverException("JS not fully loaded on MVT test suite")

    @retry_on_failure(3, 30)
    def _load_mvt(self):
        self.stb.key_input(95)  # Press BACK in case of CS2400
        self.stb.start_mvt_app()
        assert self.wait_until_element_visible("testlist"), "Failed to load MVT application"
        self.logger.debug("Started MVT application")


@pytest.fixture(scope="session")
def webdriver(test_logger, stb):
    driver = WebDriver(test_logger, stb)
    yield driver
    # TODO: quit() is disabled, because it is failing in WPE 2.38 [ONEM-33283]
    # if driver.driver:
    #     driver.driver.quit()
