#!/bin/bash

set -

CASA=~/SKA/casa-6.5.3-28-py3.8/bin/casa
[ -f $CASA ] || (echo "Fatal. Could not find $CASA" && exit 1)
which $CASA

#CASAVIEWER=~/SKA/casa-6.5.3-28-py3.8/bin/casaviewer
#[ -f $CASAVIEWER ] || (echo "Fatal. Could not find $CASAVIEWER" && exit 1)

#$CASA --help

$CASA \
    --nogui \
    --norc \
    --notelemetry \
    --logfile casa_flagdata.log \
    -c casa_flagdata.py \
    --ms_file /work/ska/orliac/rascil/rascil_skalow_venerable_test_image.ms

#    --ms_file /work/ska/orliac/rascil/rascil-main/test_results/test_roundtrip.ms

#$CASAVIEWER casa_dirty.image
