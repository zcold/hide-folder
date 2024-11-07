#!/usr/bin/env bash
function install_python_venv {
    local py_ver=${1:-"3.12"}
    local my_python="python${py_ver}"

    if ! which "${my_python}" &> /dev/null; then
        echo "${my_python} is not installed. Please install it first."
        exit 1
    fi

    if ! "${my_python}" -m venv -h &> /dev/null; then
        echo "${my_python} venv module is not installed. Please install it first."
        exit 1
    fi

    repo_root=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
    "${my_python}" -m venv "${repo_root}/venv"

    # shellcheck source=/dev/null
    source "${repo_root}/venv/bin/activate"

    if ! python -m pip install --upgrade pip; then
        echo "Failed to upgrade pip."
        exit 1
    fi

    python -m pip install -r "${repo_root}/requirements.txt"
}

install_python_venv 3.12
python extension.py
