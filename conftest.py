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
    parser.addoption("--mvt_url", action="store", default="https://mvt.onemw.net")
    parser.addoption("--ws_nw_interface", action="store", default="eth0")
    parser.addoption("--device_type", action="store", default="LGI")
