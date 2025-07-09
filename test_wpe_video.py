from time import sleep
import pytest


@pytest.mark.parametrize(
    "suite",
    [
        "codec-support-test",
        "dash-shaka-test",
        "dash-dashjs-test",
        "hls-shaka-test",
        "hls-hlsjs-test",
        "hss-html5-test",
        "hss-dashjs-test",
        "progressive-html5-test",
    ],
)
def test_mvt_suite(suite, mvt_remote_runner):
    mvt_remote_runner.run(suite)
    mvt_remote_runner.verify_results()
    sleep(5)
