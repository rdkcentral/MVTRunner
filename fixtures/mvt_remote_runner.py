import json
import os
import pytest
from time import sleep, time
from utils import retry_on_failure

SCREENSHOTS_DIR = "screenshots"
MVT_RESULTS_DIR = "results"


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
        self.started = True
        self._t0 = time()
        self.logger.info(f" {self.get_test_name()} ".center(80, "-"))

        self._load_suite(suite)
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

    def collect_screenshot(self):
        screenshot_path = os.path.join(self._result_dir, SCREENSHOTS_DIR, f"{self.get_test_name()}.png")
        self.mvtdriver.stb.take_screenshot(screenshot_path)

    def save_result(self):
        if self._result_dir:
            file_name = f"{self.get_test_name()}_{self.mvtdriver.stb.profile}_result.json"
            json_result = os.path.join(self._result_dir, MVT_RESULTS_DIR, file_name)
            with open(json_result, "w", encoding="utf-8") as f:
                json.dump(self._results, f, indent=4)

    @retry_on_failure(3)
    def _load_suite(self, suite):
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
