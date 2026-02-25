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
import os
import pytest
from time import sleep, time
from utils import retry_on_failure

SCREENSHOTS_DIR = "screenshots"
MVT_RESULTS_DIR = "results"
MVT_EXTENSION_TESTS = {
    "html-test",
    "css-test",
    "js-test",
    "system-font-test",
    "gfx-test",
    "lightning-test",
    "application-memory-test",
}


def _fix_test_results_ver_type(results):
    """Convert type of values under 'ver' key from str to float"""
    results["ver"] = float(results["ver"])
    for test in results["tests"]:
        test["ver"] = float(test["ver"])
    return results


class MVTRemoteRunner:
    def __init__(self, logger, mvtdriver):
        self.logger = logger
        self.mvtdriver = mvtdriver
        self.started = False
        self._result_dir = logger.result_dir
        self._current_test = 0
        self._num_of_tests = 0
        self._results = {}
        if self._result_dir:
            os.makedirs(os.path.join(self._result_dir, SCREENSHOTS_DIR), exist_ok=True)
            os.makedirs(os.path.join(self._result_dir, MVT_RESULTS_DIR), exist_ok=True)

    @staticmethod
    def get_test_name():
        return os.environ.get("PYTEST_CURRENT_TEST").split(":")[-1].split(" ")[0].replace("[", "_").replace("]", "")

    def run(self, suite, timeout=1800):
        self._last_suite = suite
        self.started = True
        self._t0 = time()
        self.logger.info(f" {self.get_test_name()} ".center(80, "-"))

        self._load_suite(suite)
        if suite in MVT_EXTENSION_TESTS:
            return
        self._num_of_tests = int(self.mvtdriver.websocket.send_message("getNumberOfTests"))
        self._get_results()

        while int(time() - self._t0) < timeout:
            sleep(5)
            if self._browser_has_crashed():
                self.logger.assertion(False, f"Browser has crashed. Finished {self._current_test}/{self._num_of_tests}")
            elif self.is_finished():
                self._get_results()
                for i, test_result in enumerate(self._results["tests"], 1):
                    if test_result["status"] == "failed":
                        self.logger.error(f'{i}. {test_result["name"]}... {test_result["status"]}')
                    else:
                        self.logger.info(f'{i}. {test_result["name"]}... {test_result["status"]}')
                self.logger.info(f" Test finished in: {int(time() - self._t0)}s ".center(80, "-"))
                return
            else:
                try:  # Cache partial results to simplify debugging in case of browser crash:
                    self._get_results()
                except Exception:
                    pass
        self.logger.assertion(
            False, f"Timeout on running sute '{suite}'. Finished {self._current_test}/{self._num_of_tests}"
        )

    def is_finished(self):
        return self._current_test == self._num_of_tests

    def verify_results(self):
        failed_tests = [test["name"] for test in self._results["tests"] if test["status"] == "failed"]
        self.logger.assertion(not failed_tests, f"{len(failed_tests)} test failed: {failed_tests}.")

    def collect_screenshot(self, suffix=None):
        base_name = self.get_test_name()
        if suffix:
            file_name = f"{base_name}_{suffix}.png"
        else:
            file_name = f"{base_name}.png"
        screenshot_path = os.path.join(self._result_dir, SCREENSHOTS_DIR, file_name)
        self.mvtdriver.stb.take_screenshot(screenshot_path)

    def save_result(self):
        if getattr(self, "_last_suite", None) in MVT_EXTENSION_TESTS:
            return
        if self._result_dir:
            file_name = f"{self.get_test_name()}_{self.mvtdriver.stb.profile}_result.json"
            json_result = os.path.join(self._result_dir, MVT_RESULTS_DIR, file_name)
            with open(json_result, "w", encoding="utf-8") as f:
                json.dump(self._results, f, indent=4)

    def _open_and_press(self, page, keys, sleep_time=20, screenshot_suffix=None, delay=None):
        suite_url = f"{self.mvtdriver.stb.mvt_url}/{page}"
        self.logger.debug(f"Loading page: {suite_url}")

        self.mvtdriver.stb.start_mvt_suite(suite_url)
        for key in keys:
            self.mvtdriver.stb.key_input(key)
            if delay:
                sleep(delay)
        sleep(sleep_time)
        self.collect_screenshot(screenshot_suffix)

    @retry_on_failure(3)
    def _load_suite(self, suite):
        if suite == "html-test":
            self._open_and_press("html-tests.html", [85])
            return

        if suite == "css-test":
            self._open_and_press("css-tests.html", [85])
            return

        if suite == "js-test":
            self._open_and_press("js-tests.html", [85])
            return

        if suite == "system-font-test":
            self._open_and_press("system-fonts.html", [85])
            return

        if suite == "gfx-test":
            self._open_and_press("gfx-test.html", [85], screenshot_suffix="1")
            self._open_and_press("gfx-test.html", [82, 85], screenshot_suffix="2")
            return

        if suite == "lightning-test":
            self._open_and_press("lightningjs_test.html", [85, 82, 84, 84, 85], screenshot_suffix="1", delay=5)
            self._open_and_press("lightningjs_test.html", [82, 85], screenshot_suffix="2")
            return

        if suite == "application-memory-test":
            suite_url = f"{self.mvtdriver.stb.mvt_url}/application_memory.html"
            self.logger.debug(f"Loading page: {suite_url}")
            self.mvtdriver.stb.start_mvt_suite(suite_url)
            for i in range(1, 25):
                self.logger.debug(f"key press : {i}")
                self.mvtdriver.stb.key_input(85)
                sleep(2)
                if self._browser_has_crashed():
                    if i > 19:
                        self.collect_screenshot()
                    return

            sleep(20)
            return

        suite_url = f"{self.mvtdriver.stb.mvt_url}/?test_type={suite}&profile={self.mvtdriver.stb.profile}&command=run"
        self.logger.debug(f"Load MVT test suite: {suite_url}")
        self.mvtdriver.stb.start_mvt_suite(suite_url)
        self.mvtdriver.wait_until_testlist_visible()
        self.mvtdriver.is_js_loaded()

    def _browser_has_crashed(self):
        try:
            resp = self.mvtdriver.stb.shell("ps aux | grep WPEWebProcess | grep -v grep")
            return "WPEWebProcess" not in resp
        except Exception:
            return False

    @retry_on_failure(3)
    def _get_results(self):
        self._current_test = int(self.mvtdriver.websocket.send_message("getCurrentTestIdx"))
        self._results = _fix_test_results_ver_type(json.loads(self.mvtdriver.websocket.send_message("getMvtTestResults")))
        if self._result_dir:
            self.collect_screenshot()
            self.save_result()


@pytest.fixture
def mvt_remote_runner(test_logger, websocket, mvtdriver):
    runner = MVTRemoteRunner(test_logger, mvtdriver)
    yield runner
    runner.save_result()
