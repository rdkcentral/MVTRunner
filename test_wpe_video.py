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

from time import sleep
import pytest


@pytest.mark.parametrize(
    "suite",
    [
        "codec-support-test",
        # "dash-shaka-test",
        # "dash-dashjs-test",
        # "hls-shaka-test",
        # "hls-hlsjs-test",
        # "hss-html5-test",
        # "hss-dashjs-test",
        # "progressive-html5-test",
        "html-test",
        "css-test",
        "js-test",
        "system-font-test",
        "gfx-test",
        "lightning-test",
        "application-memory-test"
    ],
)
def test_mvt_suite(suite, mvt_remote_runner):
    mvt_remote_runner.run(suite)
    mvt_remote_runner.verify_results()
    sleep(5)
