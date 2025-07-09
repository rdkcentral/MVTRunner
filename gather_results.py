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
