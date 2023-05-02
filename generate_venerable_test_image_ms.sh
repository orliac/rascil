#!/bin/shell

set -e

source ~/SKA/ska-spack-env/bipp-izar-gcc/activate.sh
source RASCIL100/bin/activate

export RASCIL=/work/ska/orliac/rascil/rascil-main
[ -d $RASCIL ] || (echo "Fatal: $RASCIL not a directory" && exit 1)

export SKA_SDP_FUNC_PYTHON=/work/ska/orliac/rascil/ska-sdp-func-python
[ -d $SKA_SDP_FUNC_PYTHON ] || (echo "Fatal: $SKA_SDP_FUNC_PYTHON not a directory" && exit 1)

export PYTHONPATH=$SKA_SDP_FUNC_PYTHON:$RASCIL:$PYTHONPATH
#echo $PYTHONPATH | grep ska-sdp

#python -V
#python -m pip list | grep sdp

MS=/work/ska/orliac/rascil/rascil_skalow_venerable_test_image.ms
[ -d ${MS} ] && echo "-I- Deleting ${MS}*" && rm -r ${MS}*


echo "-I- Running RASCIL 1.1.0 example imaging.py"
python generate_venerable_test_image_ms.py --ms_file ${MS}


# EO: deactivate environments before running CASA
deactivate
source ~/SKA/ska-spack-env/bipp-izar-gcc/deactivate.sh


#python rascil-main/tests/processing_components/test_export_ms_roundtrip.py
#python test_export_ms_roundtrip.py

if [ 1 == 0 ]; then
    echo "- !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo "-W- Running CASA to flag autocorrelations, otherwise WSClean scale does not match RASCIL/Bluebild"
    echo "-W- (WSClean intensity range is half (almost exactly) the one from RASCIL)"
    
    CASA=~/SKA/casa-6.5.3-28-py3.8/bin/casa
    [ -f $CASA ] || (echo "Fatal. Could not find $CASA" && exit 1)
    echo "-I Running " $(which $CASA)
    
    $CASA \
        --nogui \
        --norc \
        --notelemetry \
        --logfile casa_flagdata.log \
        -c casa_flagdata.py \
        --ms_file $MS
    echo "- !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
fi
