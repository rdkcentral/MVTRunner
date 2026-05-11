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
