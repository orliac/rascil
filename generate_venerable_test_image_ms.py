# This script makes a fake data set and then deconvolves it.

import logging
import sys
import os

import numpy
from astropy import units as u
from astropy.coordinates import SkyCoord
from ska_sdp_datamodels.configuration.config_create import create_named_configuration
from ska_sdp_datamodels.science_data_model.polarisation_model import PolarisationFrame
from ska_sdp_datamodels.visibility import create_visibility
from ska_sdp_func_python.image import (
    deconvolve_cube,
    restore_cube,
)
from ska_sdp_func_python.imaging import (
    predict_visibility,
    invert_visibility,
    create_image_from_visibility,
    advise_wide_field,
    predict_ng
)
from rascil.processing_components import (
    create_test_image,
    create_visibility_from_ms
)
from rascil.processing_components.visibility.base import export_visibility_to_ms

import argparse
parser = argparse.ArgumentParser(description='Run RASCIL to generate MS dataset from venerable test image')
parser.add_argument('--ms_file',  help='path to MS dataset to process', required=True)
args = parser.parse_args()
results_dir = os.path.dirname(args.ms_file)


log = logging.getLogger("rascil-logger")
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler(sys.stdout))


# Construct LOW core configuration
lowr3 = create_named_configuration("LOWBD2-CORE", rmax=2000.0)

# We create the visibility. This just makes the uvw, time, antenna1, antenna2,
# weight columns in a table. We subsequently fill the visibility value in by
# a predict step.
polarization="linear"
times = numpy.zeros([1])
frequency = numpy.array([1e8])
channel_bandwidth = numpy.array([1e6])
phasecentre = SkyCoord(
    ra=+15.0 * u.deg, dec=-45.0 * u.deg, frame="icrs", equinox="J2000"
)
vt = create_visibility(
    lowr3,
    times,
    frequency,
    phasecentre=phasecentre,
    weight=1.0,
    polarisation_frame=PolarisationFrame(polarization),
    channel_bandwidth=channel_bandwidth
)

# Find the recommended imaging parameters
advice = advise_wide_field(
    vt,
    guard_band_image=3.0,
    delA=0.1,
    oversampling_synthesised_beam=4.0
)
rad2asec = 3600 * 180 / numpy.pi
advice_cellsize = advice["cellsize"]  # [rad]

if 1 == 1:
    cellsize = advice_cellsize
    cellsize_asec = cellsize * rad2asec
else:
    cellsize_asec = 50
    cellsize = cellsize_asec / rad2asec

print("advised cellsize =", advice_cellsize, "[rad], cellsize =", cellsize, "[rad] ==", cellsize_asec, "[asec]")



# Read the venerable test image, constructing a RASCIL Image
m31image = create_test_image(cellsize=cellsize,
                             frequency=frequency,
                             phasecentre=vt.phasecentre,
                             polarisation_frame=PolarisationFrame(polarization)
)
nchan, npol, ny, nx = m31image["pixels"].data.shape
print(f"nchan = {nchan}, npol = {npol}, nx = {nx}, ny = {ny}")
print("m31image.data.shape", m31image["pixels"].data.shape)
print("m31image.data.max =", numpy.max(m31image["pixels"].data))

if 1 == 1:
    vt = predict_ng(vt, m31image, context='2d')

    # Temporarily flag autocorrelations until MS writer is fixed
    #uvdist_lambda = numpy.hypot(vt.visibility_acc.uvw_lambda[..., 0],
    #                            vt.visibility_acc.uvw_lambda[..., 1])
    #vt["flags"].data[numpy.where(uvdist_lambda <= 0.0)] = 1
    
    dirty, sumwt = invert_visibility(vt, m31image, context="2d")
    assert(numpy.all(sumwt == sumwt[0,:]))
    psf, sumwt = invert_visibility(vt, m31image, context="2d", dopsf=True)
    assert(numpy.all(sumwt == sumwt[0,:]))
    print("dirty =", dirty)
    print("dirty[pixels] =", dirty["pixels"])
    print(
        "Min, max in dirty image = %.6f, %.6f, sumwt = %f"
        % (dirty["pixels"].data.min(), dirty["pixels"].data.max(), sumwt[0][0])
    )
else:
    model = create_image_from_visibility(vt, cellsize=cellsize, npixel=nx)
    #vt = predict_visibility(vt, model, context="2d")
    vt = predict_ng(vt, model, context="2d")
    dirty, sumwt = invert_visibility(vt, model, context="2d")
    psf, sumwt = invert_visibility(vt, model, context="2d", dopsf=True)
    print(
        "Max, min in dirty image = %.6f, %.6f, sumwt = %f"
        % (dirty["pixels"].data.max(), dirty["pixels"].data.min(), sumwt)
    )
    print(
        "Max, min in PSF         = %.6f, %.6f, sumwt = %f"
        % (psf["pixels"].data.max(), psf["pixels"].data.min(), sumwt)
    )


export_visibility_to_ms(args.ms_file, [vt])

dirty.image_acc.export_to_fits("%s/imaging_dirty_corrupted.fits" % (results_dir))
psf.image_acc.export_to_fits("%s/imaging_psf_corrupted.fits" % (results_dir))

if 1 == 1:
    vt_after = create_visibility_from_ms(args.ms_file)[0]

    # Temporarily flag autocorrelations until MS writer is fixed
    uvdist_lambda = numpy.hypot(
        vt_after.visibility_acc.uvw_lambda[..., 0],
        vt_after.visibility_acc.uvw_lambda[..., 1],
    )
    vt_after["flags"].data[numpy.where(uvdist_lambda <= 0.0)] = 1

    # Make the dirty image and point spread function
    model = create_image_from_visibility(vt_after, cellsize=cellsize, npixel=nx)
    dirty, sumwt = invert_visibility(vt_after, model, context="2d")
    psf,   sumwt = invert_visibility(vt_after, model, context="2d", dopsf=True)
    #dirty, sumwt = invert_visibility(vt_after, m31image, context="2d")
    print("Min, max in dirty image = %.6f, %.6f, sumwt = %f" % (dirty["pixels"].data.min(), dirty["pixels"].data.max(), sumwt[0][0]))
    dirty.image_acc.export_to_fits("%s/imaging_dirty.fits" % (results_dir))
    psf.image_acc.export_to_fits("%s/imaging_psf.fits" % (results_dir))

    export_visibility_to_ms(args.ms_file, [vt_after])
    
    
"""
# Deconvolve using clean
comp, residual = deconvolve_cube(
    dirty,
    psf,
    niter=10000,
    threshold=0.001,
    fractional_threshold=0.001,
    window_shape="quarter",
    gain=0.7,
    scales=[0, 3, 10, 30],
)

restored = restore_cube(comp, psf, residual)
print(
    "Max, min in restored image = %.6f, %.6f, sumwt = %f"
    % (restored["pixels"].data.max(), restored["pixels"].data.min(), sumwt)
)
restored.image_acc.export_to_fits("%s/imaging_restored.fits" % (results_dir))
"""
