SHELL := /bin/bash

PIP_ARGS := --disable-pip-version-check --no-cache-dir
SYSTEM_PYTHON_PATH := /usr/local/bin/python3
SYSTEM_PIP_INSTALL_COMMAND := $(SYSTEM_PYTHON_PATH) -m pip install $(PIP_ARGS)

.PHONY: all bootstrap-pip-invoke bootstrap-pip-pipx-invoke pip-install-system pipx-install invoke-install-pipx invoke-install-system

all:
	# intentionally left empty to prevent accidental run of first recipe

bootstrap-pip-invoke: pip-install-system invoke-install-system

bootstrap-pip-pipx-invoke: pip-install-system pipx-install invoke-install-pipx

pip-install-system:
	curl -sS -L https://bootstrap.pypa.io/get-pip.py | $(SYSTEM_PYTHON_PATH) -


pipx-install:
	$(SYSTEM_PIP_INSTALL_COMMAND) --upgrade --user "pipx~=1.0"

# intended for local env
invoke-install-pipx:
	pipx install --pip-args "$(PIP_ARGS)" "invoke~=1.0"
	pipx inject --pip-args "$(PIP_ARGS)" "invoke" --include-apps "python-dotenv[cli]~=0.20"

# intended for server or container env
invoke-install-system:
	echo $(SYSTEM_PIP_INSTALL_COMMAND) --upgrade --user "invoke~=1.0" "python-dotenv~=0.20"
