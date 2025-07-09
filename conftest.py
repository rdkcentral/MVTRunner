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

pytest_plugins = [
    "fixtures.common",
    "fixtures.mvt_remote_runner",
    "fixtures.stb",
    "fixtures.mvtdriver",
    "fixtures.websocket",
]


def pytest_addoption(parser):
    parser.addoption("--ip", action="store", required=True)
    parser.addoption("--profile", action="store", required=True)
    parser.addoption("--result_dir", action="store")
    parser.addoption("--pack_result", action="store_true")
    parser.addoption("--mvt_url", action="store", default="")
    parser.addoption("--ws_nw_interface", action="store", default="eth0")
    parser.addoption("--device_type", action="store", default="LGI")
