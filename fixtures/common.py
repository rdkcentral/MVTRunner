import logging
import pytest
from os import makedirs, path
from gather_results import gather_results


@pytest.fixture(scope="session")
def stb_ip(pytestconfig):
    return pytestconfig.getoption("ip")


@pytest.fixture(scope="session")
def mvt_profile(pytestconfig):
    return pytestconfig.getoption("profile")


@pytest.fixture(scope="session")
def mvt_url(pytestconfig):
    return pytestconfig.getoption("mvt_url")

@pytest.fixture(scope="session")
def ws_nw_interface(pytestconfig):
    return pytestconfig.getoption("ws_nw_interface")

@pytest.fixture(scope="session")
def device_type(pytestconfig):
    return pytestconfig.getoption("device_type")

def _assertion(self, condition, message):
    if not condition:
        self.error(message)
        assert condition, message


logging.Logger.assertion = _assertion


@pytest.fixture(scope="session")
def test_logger(pytestconfig):
    logger = logging.getLogger("mvt_runner")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    logger.result_dir = pytestconfig.getoption("result_dir")
    if logger.result_dir:
        makedirs(logger.result_dir, exist_ok=True)
        fh = logging.FileHandler(path.join(logger.result_dir, "summary.log"))
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    yield logger
    logging.shutdown()
    if pytestconfig.getoption("pack_result"):
        gather_results(logger.result_dir)
