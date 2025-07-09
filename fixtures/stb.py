import json
import subprocess
import pytest
import os
from time import sleep, time
from requests import request, exceptions as requests_exceptions
from websocket import create_connection
from utils import HTTP_CONTENT_TYPE_JSON, is_linux, retry_on_failure


class STB:
    def __init__(self, logger, ip, profile, mvt_url, device_type):
        self.logger = logger
        self.ip = ip
        self.profile = profile
        self.mvt_url = mvt_url
        self.device_type = device_type
        self.logger.debug(f"Connecting to STB with IP {ip}")
        self.logger.debug(f"Device type is {device_type}")

        # first make sure Thunder is running
        # this will also make sure we can connect to the box - e.g. boot process finished and the network is up
        if not self._wait_for_thunder_ready(120):
            raise Exception("Couldn't contact Thunder")
        else:
            self.logger.debug('Thunder running')

        self._disable_busybox_warning()
        self._clear_ip_tables()
        self.wake_up_box()
        if 'LGI' in self.device_type:
            self.build_variant = self._get_stb_build_variant()
            if self.build_variant == "flt":
                sleep(60)
            else:
                self._wait_for_ui_tools()
            self._dismiss_screensaver()
            try:
                # This step is needed only after a factory reset, sometimes
                # function is failing even if 'app terms of use' are already
                # accepted, that is why we have 'pass' after an exception.
                self._accept_app_terms_of_use()
            except Exception:
                pass

    def _wait_for_thunder_ready(self, max_time):
        self.logger.debug('waiting for Thunder ...')
        start_time = time()
        thunder_started = False
        last_errlog_time = 0
        while time() - start_time < max_time and not thunder_started:
            try:
                response = request('GET', f'http://{self.ip}:9998/Service')
                thunder_started = response.status_code == 200
            except requests_exceptions.RequestException as e:
                t = int(time())
                if t > last_errlog_time:
                    self.logger.debug(f"{int(time() - start_time)}/{max_time} sec: Exception waiting for Thunder: {e}")
                    last_errlog_time = t
        return thunder_started

    def shell(self, command, ignore_stderr=True, decode_output=True):
        password = os.getenv("STB_PASSWORD")
        if is_linux():
            command_to_send = [
                "sshpass",
                "-p",
                password,
                "ssh",
                "root@" + self.ip,
                "-o",
                "HostKeyAlgorithms=+ssh-rsa",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "LogLevel=ERROR",
            ] + command.split()
            if ignore_stderr:
                command_to_send += ["2>/dev/null"]
            reading_process = subprocess.Popen(command_to_send, stdout=subprocess.PIPE)
        else:
            setup_plink = subprocess.Popen(
                ["echo", "y", "|", "plink", "-ssh", "root@" + self.ip, "-pw", password, "exit"],
                stdout=subprocess.PIPE,
                shell=True,
            )
            setup_plink.stdout.read()
            command_to_send = [
                "plink",
                "-batch",
                "-ssh",
                "root@" + self.ip,
                "-pw",
                password,
                command,
            ]
            reading_process = subprocess.Popen(command_to_send, stdout=subprocess.PIPE, shell=True)
        response = reading_process.stdout.read()
        reading_process.wait()
        reading_process.stdout.close()
        return str(response) if decode_output else response

    def rest_api(self, path, method="GET", headers=None, data=None):
        return self.http_request(10014, path, method, headers, data)

    @retry_on_failure(2)
    def http_request(self, port, path, method="GET", headers=dict(), data=None):
        response = request(method, f"http://{self.ip}:{port}/{path}", headers=headers, data=data)
        response.raise_for_status()
        return response

    def ws_api(self, command):
        ws = create_connection(f"ws://{self.ip}:10016", timeout=30)
        sleep(1)
        ws.send(command)
        sleep(1)
        ws.close()

    def wake_up_box(self):
        if 'LGI' in self.device_type:
            response = json.loads(self.rest_api("power-manager/getPowerState").content)
            self.logger.debug(response)
            if response["currentState"] != "Operational":
                self.logger.debug(f"Power state is {response["currentState"]} - waking up")
                #self.set_power_state("Operational")
                self.rest_api(
                    "power-manager/setPowerState",
                    method="POST",
                    headers=HTTP_CONTENT_TYPE_JSON,
                    data=json.dumps({"state": "Operational"})
                )
        else:
            self.shell(f"curl -d \'{{\"method\": \"org.rdk.System.1.setPowerState\", \"params\": {{\"powerState\": \"ON\"}}}}\' http://127.0.0.1:9998/jsonrpc")

    def start_webkit(self):
        self.shell(
            "dbus-send --system --print-reply --dest=com.lgi.rdk.utils.awc.server "
            "/com/lgi/rdk/utils/awc/awc com.lgi.rdk.utils.awc.awc.Start string:'thunderwpe' "
            "array:string:'https://widgets.metrological.com/lightning/liberty/2e3c4fc22f0d35e3eb7fdb47eb7d4658#boot'"
        )
        self.logger.debug("WebKit started")

    def stop_webkit(self, clear_cache=False):
        self.shell(
            "dbus-send --system --print-reply --dest=com.lgi.rdk.utils.awc.server "
            "/com/lgi/rdk/utils/awc/awc com.lgi.rdk.utils.awc.awc.Stop uint32:`pidof WPEWebProcess` int32:0"
        )
        self.logger.debug("WebKit stopped")
        if clear_cache:
            self.shell("rm -rf /mnt/wpe_cache/*")

    def start_mvt_app(self):
        self.logger.debug("Start MVT application")
        if 'LGI' in self.device_type:
            if self.build_variant == "flt":
                self._start_mvt_app_flt()
                return
            navigate_args = {
                "path": "/App/com.libertyglobal.app.mvt",
                "params": {
                "hardware": self.profile,
                },
            }
            self.ws_api(f"navigateTo: {json.dumps(navigate_args)}")
            self.logger.debug("ws request to open /App/com.libertyglobal.app.mvt sent")
        else:
            self.shell(f"curl -d \'{{\"method\": \"Controller.1.activate\", \"params\": {{\"callsign\": \"WebKitBrowser\"}}}}\' http://127.0.0.1:9998/jsonrpc")
        sleep(5)

    def take_screenshot(self, filename):
        if 'LGI' in self.device_type:
            device_image_path = "/tmp/mvt_runner_screenshot.png"
            self.shell(f"rm -f {device_image_path}")
            self.shell(f"/usr/bin/do_screenshot.sh {device_image_path}")
            image_data = self.shell(f"cat {device_image_path}", decode_output=False)
            with open(filename, "wb") as f:
                f.write(image_data)

    def key_input(self, keycode):
        if 'LGI' in self.device_type:
            self.rest_api(f"keyinjector/emulateuserevent/{keycode}/8300")
        else:
            self.shell(f"curl -d \'{{\"method\": \"org.rdk.RDKShell.1.generateKey\", \"params\": {{\"keys\": [{{\"keyCode\": {keycode}, \"modifiers\": [],  \"delay\": 0.3}}] }}}}\' http://127.0.0.1:9998/jsonrpc")
        sleep(2)

    def start_mvt_suite(self, url):
        self.logger.debug("Starting MVT suite for url " + url)
        self.shell(f'curl -d \'{{"url": "{url}"}}\' http://localhost:9998/Service/WebKitBrowser/URL')
        sleep(5)

    def _start_mvt_app_flt(self):
        self.logger.debug(
            self.shell(f'curl -d \'{"url": "{self.mvt_url}"}\' http://localhost:9998/Service/WebKitBrowser/URL')
        )
        sleep(10)

    def _disable_busybox_warning(self):
        self.shell("touch /mnt/nand/mw/i-know-im-using-devel-busybox")

    def _clear_ip_tables(self):
        self.logger.debug("Clearing iptables...")
        self.shell("/usr/sbin/iptables -P INPUT ACCEPT")
        self.shell("/usr/sbin/iptables -P OUTPUT ACCEPT")
        self.shell("/usr/sbin/iptables -F")
        self.logger.debug("iptables cleared")

    def _get_stb_build_variant(self):
        box_build = self.shell("cat /etc/version")
        stb_build_variant = box_build.split("-")[1]
        return stb_build_variant

    def _wait_for_ui_tools(self):
        RETRY_LIMIT = 20
        i = 0
        while self.rest_api("settings/getSetting/cpe.uiTestTools").text != "true":
            self.logger.debug("Starting uiTestTools...")
            self.rest_api("settings/setSetting/cpe.uiTestTools",
                          method="PUT",
                          headers=HTTP_CONTENT_TYPE_JSON,
                          data="true")
            i += 1
            self.logger.assertion(i < RETRY_LIMIT, "Failed to start uiTestTools")
            sleep(1)
        self.logger.debug("Started uiTestTools")

    def _dismiss_screensaver(self):
        response = self.http_request(8125, "v2/state").text
        ARROW_UP_KEYCODE = 81
        if "ApolloCPEPairingAnimation" in response:
            self.logger.debug("Sending key ARROW_UP to dismiss pairing hint animation")
            self.key_input(ARROW_UP_KEYCODE)
        if "ScreenSaver.View" in response:
            self.logger.debug("Sending key ARROW_UP to dismiss screensaver")
            self.key_input(ARROW_UP_KEYCODE)

    @retry_on_failure(1)
    def _accept_app_terms_of_use(self):
        self.logger.debug("Accepting apps terms of use")
        self.rest_api("settings/setSetting/customer.appsOptIn", method="PUT",
                      headers=HTTP_CONTENT_TYPE_JSON, data="true")


@pytest.fixture(scope="session")
def stb(test_logger, stb_ip, mvt_profile, mvt_url, device_type):
    return STB(test_logger, stb_ip, mvt_profile, mvt_url, device_type)
