#/bin/bash

set -e

VENV=RASCIL100
source ~/SKA/ska-spack-env/bipp-izar-gcc/activate.sh
which python && python -V

python -m venv $VENV
source $VENV/bin/activate
#pip list -v
python -m pip install --upgrade pip

if [[ 1 == 0 ]]; then
    pip uninstall ska-sdp-datamodels
    pip uninstall ska-sdp-func
    pip uninstall ska-sdp-func-python
fi

[ ! -d rascil-main ]  && \
    git clone https://gitlab.com/ska-telescope/external/rascil-main.git
[ ! -d ska-sdp-func ] && \
    git clone https://gitlab.com/ska-telescope/sdp/ska-sdp-func.git
[ ! -d ska-sdp-datamodels ] && \
    git clone https://gitlab.com/ska-telescope/sdp/ska-sdp-datamodels.git
[ ! -d ska-sdp-func-python ] && \
    git clone https://gitlab.com/ska-telescope/sdp/ska-sdp-func-python.git

if [[ 1 == 0 ]]; then
    cd ska-sdp-datamodels
    python -m pip install --no-deps .
    cd -
fi

if [[ 1 == 0 ]]; then
    cd ska-sdp-func
    python -m pip install --no-deps .
    cd -
fi

cd ska-sdp-func-python
python -m pip install --no-deps .
cd -

cd rascil-main
make install_requirements
cd -

deactivate
source ~/SKA/ska-spack-env/bipp-izar-gcc/deactivate.sh
