import json
import pytest
from time import sleep
from utils import HTTP_CONTENT_TYPE_JSON, wait_for, retry_on_failure


class MvtDriver:
    def __init__(self, logger, stb, websocket):
        self.logger = logger
        self.stb = stb
        self.websocket = websocket
        self._load_mvt()

    def wait_until_testlist_visible(self):
        num_test = self.websocket.send_message("getNumberOfTests")
        if(num_test != ''):
            return True
        return False

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
