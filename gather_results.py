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

import argparse
import tarfile
from os import path, sep
from shutil import rmtree
from time import time


def make_tarfile(source_dir, output_filename):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=path.basename(source_dir))


def gather_results(pytest_result_dir):
    # TODO Gather journal from STB
    # TODO Gather core dumps from STB
    pytest_result_dir = pytest_result_dir.rstrip(sep)
    print(f"Compressing {pytest_result_dir}...")
    compressed_path = path.join(path.dirname(pytest_result_dir), f"mvt_{int(time())}.tar.gz")
    make_tarfile(pytest_result_dir, compressed_path)
    rmtree(pytest_result_dir)
    print(f"Results package: {compressed_path}")
    return compressed_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gather MVT tests results.")
    parser.add_argument("result_dir", action="store", help="Directory with MVT runner results")
    args = parser.parse_args()
    gather_results(args.result_dir)
