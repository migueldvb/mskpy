# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
irtf --- NASA IRTF instruments.
===============================

   Classes
   -------
   BASS
   MIRSI
   SpeX

"""

import numpy as np
import astropy.units as u

try:
    from ..ephem import Earth
except ImportError:
    Earth = None

from .instrument import Instrument, Camera
from .instrument import CircularApertureSpectrometer, LongSlitSpectrometer

__all__ = [
    'BASS',
    'MIRSI',
    'SpeX'
]

class BASS(CircularApertureSpectrometer):
    """Broadband Array Spectrograph System.
    """

    def __init__(self):
        waves = [
            3.02961,   3.13797,   3.24272,   3.34419,   3.63162,   3.7225 ,
            3.89791,   3.98272,   4.06576,   4.53217,   4.74822,   4.81809,
            4.88695,   4.95486,   5.02185,   5.28133,   5.34423,   7.27842,
            7.46219,   7.64154,   7.98818,   8.15597,   8.32038,   8.48161,
            8.63982,   8.79519,   8.94787,   9.09798,   9.24565,   9.39101,
            9.53414,   9.67516,   9.81416,   9.95121,  10.0864 ,  10.2198 ,
            10.4815 ,  10.6099 ,  10.7368 ,  10.8623 ,  10.9862 ,  11.1089 ,
            11.2301 ,  11.3501 ,  11.5863 ,  11.7026 ,  11.8178 ,  11.9318 ,
            12.0448 ,  12.1567 ,  12.2677 ,  12.3776 ,  12.4865 ,  12.5945 ,
            12.7016 ,  12.8078 ,  12.9131 ,  13.0176 ,  13.1212 ,  13.224  
        ] * u.um
        CircularApertureSpectrometer.__init__(
            self, waves, 2.0 * u.arcsec, Earth)

class MIRSI(Instrument):
    """Mid-Infrared Spectrometer and Imager.

    Attributes
    ----------
    imager : `Camera` for imaging mode.
    sp10r200 : `LongSlitSpectrometer` for 10-micron spectroscopy.
    sp20r100 : `LongSlitSpectrometer` for 20-micron spectroscopy.
    mode : The current MIRSI mode (see examples).

    Examples
    --------

    """

    shape = (240, 320)
    ps = 0.265 * u.arcsec
    location = Earth

    def __init__(self):
        w = [4.9, 7.7, 8.7, 9.8, 10.6, 11.6, 12.7, 20.6, 24.4] * u.um
        self.imager = Camera(w, self.shape, self.ps, location=self.location)

        self.sp10r200 = LongSlitSpectrometer(10.5 * u.um, self.shape, self.ps,
                                             2.25, 0.022 * u.um, R=200,
                                             location=self.location)

        self.sp20r100 = LongSlitSpectrometer(21.5 * u.um, self.shape, self.ps,
                                             4.5, 0.028 * u.um, R=100,
                                             location=self.location)

        self._mode = 'imager'

    @property
    def mode(self):
        if self._mode in ['imager', 'sp10r200', 'sp20r100']:
            return self.__dict__[self._mode]
        else:
            raise KeyError("Invalid mode: {:}".format(self._mode))

    def sed(self, *args, **kwargs):
        """Spectral energy distribution of a target.

        Parameters
        ----------
        *args
        **kwargs
          Arguments and keywords depend on the current MIRSI mode.

        Returns
        -------
        sed : ndarray

        """
        return self.mode.sed(*args, **kwargs)

    def lightcurve(self, *args, **kwargs):
        """Secular lightcurve of a target.

        Parameters
        ----------
        *args
        **kwargs
          Arguments and keywords depend on the current MIRSI mode.

        Returns
        -------
        lc : astropy Table

        """
        return self.mode.lightcurve(*args, **kwargs)

class SpeX(LongSlitSpectrometer):
    """SpeX.

    Attributes
    ----------
    guidedog : SpeX's guide `Camera`.
    prism : `LongSlitSpectrometer` for 1- to 2.5-micron spectroscopy.
    mode : The current SpeX mode (see examples).

    Examples
    --------

    """

    shape = dict(guidedog=(512, 512), bigdog=(1024, 1024))
    ps = dict(guidedog=0.12 * u.arcsec, bigdog=0.15 * u.arcsec)
    location = Earth

    def __init__(self):
        w = [1.25, 1.64, 2.12, 3.75, 4.70] * u.um
        self.imager = Camera(w, self.shape['guidedog'], self.ps['guidedog'],
                             location=self.location)

        self.prism = LongSlitSpectrometer(
            1.65 * u.um, self.shape['bigdog'], self.ps['bigdog'],
            2.0, 0.034 * u.um, R=250, location=self.location)

        self._mode = 'guidedog'

    @property
    def mode(self):
        if self._mode in ['guidedog', 'prism']:
            return self.__dict__[self._mode]
        else:
            raise KeyError("Invalid mode: {:}".format(self._mode))

    def sed(self, *args, **kwargs):
        """Spectral energy distribution of a target.

        Parameters
        ----------
        *args
        **kwargs
          Arguments and keywords depend on the current MIRSI mode.

        Returns
        -------
        sed : ndarray

        """
        return self.mode.sed(*args, **kwargs)

    def lightcurve(self, *args, **kwargs):
        """Secular lightcurve of a target.

        Parameters
        ----------
        *args
        **kwargs
          Arguments and keywords depend on the current MIRSI mode.

        Returns
        -------
        lc : astropy Table

        """
        return self.mode.lightcurve(*args, **kwargs)

    def spec_correct(self, ftarget, ftelluric, dtt=0.0, dat=0.0, ext=0.0):
        """Correct a spectrum processed with xspextool.

        Take the reduced and telluric spectra, and return a final
        calibrated spectrum.

        Parameters
        ----------
        ftarget : string
          The file name of the target spectrum (FITS format).
        ftelluric : string, optional
          The file name of the telluric spectrum (FITS format).
        dtt : float, optional
          The shift in wavelength to align the telluric spectrum with
          the target. [micron]
        dat : float, optional
          The shift in wavelength to align the ATRAN spectrum with the
          target. [micron]
        ext : float, optional
          Correct the final spectrum using this amount of extinction
          and an ATRAN model.

        Returns
        -------
        wave : ndarray
        flux : ndarray
        err : ndarray
          The final wavelength, flux, and uncertainty.

        """

        from os import path
        from astropy.io import fits
        from ..config import config

        raw_w, raw_f, raw_e = fits.getdata(ftarget)
        tel_w, tel_f, tel_e = fits.getdata(ftelluric)

        x = np.arange(len(tel_w))
        tc = np.interp(x, x + dtt, tel_f)
        tar_f = raw_f * tc
        tar_e = raw_e * tc
        tar_w = raw_w

        atf = path.sep.join([config.get('spex', 'spextool_path'), 'data',
                             'atrans.fits'])
        atran = fits.getdata(atf)
        bw =  np.diff(tar_w) / 2.0
        bins = np.r_[tar_w[0] - bw[0], tar_w[1:] - bw, tar_w[-1] + bw[-1]]
        n = np.histogram(atran[0] + dat, bins=bins)[0].astype(float)
        h = np.histogram(atran[0] + dat, bins=bins, weights=atran[1])
        at = h[0] / n
        try:
            atc = 1 + (1 - at) * ext
        except ZeroDivisionError:
            atc = np.ones_like(tar_w)
        atc[~np.isfinite(atc)] = 1.0

        tar_f /= atc
        tar_e /= atc
        return tar_w, tar_f, tar_e

# update module docstring
from ..util import autodoc
autodoc(globals())
del autodoc
