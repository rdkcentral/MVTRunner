# List all tests
    python -m pytest --ip $STB_IP --profile default --collect-only .
# Run all tests and gather results
    python -m pytest -s --ip $STB_IP --profile default --result_dir results test_wpe_video.py
# Run MVT test suites separately and combine results
    python -m pytest -s --ip $STB_IP --profile default --result_dir results/mvt_220322 "test_wpe_video.py::test_mvt_suite[codec-support-test]"
    python -m pytest -s --ip $STB_IP --profile default --result_dir results/mvt_220322 --pack_result "test_wpe_video.py::test_mvt_suite[dash-shaka-test]"
# Input arguments
    --ip STB_IP // required
    --profile PROFILE // required, MVT profile e.g. default
    --result_dir // directory to store result files
    --pack_result // pack result directory into .tar.gz
    --mvt_url // MVT application address
    --ws_nw_interface // Network interface used for websocket creation, default value is eth0
    --device_type //Device type used. Some functionalities are device specific. Use 'RDK' for RDK VA. For LGI devices, use 'LGI'. Default is 'LGI'

# Docker setup and run

```bash
# Build mvt-runner docker image
docker build --build-arg UID=$(id -u) --build-arg GID=$(id -g) -t mvt-runner .

# Set your STB's IP here, eg. 10.42.0.234
MVT_RUNNER_STB_IP=
# Directory where results will be stored
MVT_RUNNER_RESULTS_DIR=$(pwd)/mvt-results

# Ensure the result dir is created
mkdir -p $MVT_RUNNER_RESULTS_DIR

# Run mvt-runner container, execute all tests and store results
docker run --rm --net=host --user=mvt-runner --env SSHPASS=$MVT_RUNNER_SSH_PASS --env STB_PASSWORD=$MVT_RUNNER_SSH_PASS -v $MVT_RUNNER_RESULTS_DIR:/mvt-results mvt-runner -s --ip $MVT_RUNNER_STB_IP --profile default --result_dir /mvt-results
```
# Note
    Since secure websocket is used for communication with MVT executing on the STB, a self signed SSL certifcate with Common Name (CN) set to the IP or Fully Qualified Domain Name (FQDN) of the machine where MVT Runner is hosted, will be used. This should be whitelisted in the STB where MVT will be loaded. Also, the corresponding private key used should be encrypted with key: b'Ki2SJWIXhuLG-4KrNhEdj3AFt_v72tmvgOH1_ExD16A='
    During runtime, based on the device type (read from --device_type parameter) the certificate and encrypted key will be taken from fixtures/certs/LGI path for 'LGI' devices and fixtures/certs/RDK path for 'RDK' devices
