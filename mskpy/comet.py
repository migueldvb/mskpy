# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
comet --- Comets!
=================

.. autosummary::
   :toctree: generated/

   Classes
   -------
   Coma
   Comet

   Functions
   ---------
   flux2Q
   fluxd2afrho
   fluxd2efrho
   m2afrho1

"""

__all__ = [
    'Coma',
    'Comet',
    'flux2Q',
    'fluxd2afrho',
    'fluxd2efrho',
    'm2afrho1'
]

import numpy as np
import astropy.units as u
from astropy.time import Time

from .ephem import SolarSysObject, State
from .asteroid import Asteroid
from .models import AfrhoRadiation, AfrhoScattered, AfrhoThermal

class Coma(SolarSysObject):
    """A comet coma.

    Parameters
    ----------
    state : State
      The location of the coma.
    Afrho1 : Quantity
      Afrho of the coma at 1 AU.
    k : float, optional
      The logarithmic slope of the dust production rate's dependence
      on rh.
    reflected : AfrhoRadiation, optional
      A model for light scattered by dust or `None` to pass `kwargs`
      to `AfrhoScattered`.
    thermal : AfrhoRadiation, optional
      A model for thermal emission from dust or `None` to pass
      `kwargs` `AfrhoThermal`.
    name : string, optional
      A name for this coma.
    **kwargs
      Keywords for `AfrhoRadiation` and/or `AfrhoThermal`, when
      `reflected` and/or `thermal` are `None`, respectively.

    """
    _Afrho1 = None

    def __init__(self, state, Afrho1, k=-2, reflected=None, thermal=None,
                 name=None, **kwargs):
        assert u.cm.is_equivalent(Afrho1), "Afrho1 must have units of length"

        SolarSysObject.__init__(self, state, name=name)
        self.k = k

        if reflected is None:
            self.reflected = AfrhoScattered(1 * Afrho1.unit, **kwargs)
        else:
            self.reflected = reflected
        assert isinstance(self.reflected, AfrhoRadiation)

        if thermal is None:
            self.thermal = AfrhoThermal(1 * Afrho1.unit, **kwargs)
        else:
            self.thermal = thermal
        assert isinstance(self.thermal, AfrhoRadiation)

        # Afrho1 property will also update self.thermal, self.scattered
        self.Afrho1 = Afrho1

    @property
    def Afrho1(self):
        return self._Afrho1

    @Afrho1.setter
    def Afrho1(self, a):
        assert u.cm.is_equivalent(a), "Afrho1 must have units of length"
        self._Afrho1 = a
        self.thermal.Afrho = 1 * a.unit
        self.reflected.Afrho = 1 * a.unit

    def fluxd(self, observer, date, wave, rap=1.0 * u.arcsec,
              reflected=True, thermal=True, ltt=False,
              unit=u.Unit('W / (m2 um)'), **kwargs):
        """Total flux density as seen by an observer.

        Parameters
        ----------
        observer : SolarSysObject
          The observer.
        date : string, float, astropy Time, datetime
          The time of the observation in any format acceptable to
          `observer`.
        wave : Quantity
          The wavelengths to compute `fluxd`.
        rap : Quantity, optional
          The aperture radius, angular or projected distance at the
          comet.
        reflected : bool, optional
          If `True` include the reflected light model.
        thermal : bool, optional
          If `True` include the thermal emission model.
        ltt : bool, optional
          Set to `True` to correct the object's position for light
          travel time.
        unit : astropy Unit
          The return unit, must be flux density.
        
        Returns
        -------
        fluxd : Quantity

        """

        if not np.iterable(wave):
            wave = [wave.value] * wave.unit

        fluxd = np.zeros(len(wave)) * unit
        if self.Afrho1.value <= 0:
            return fluxd

        g = observer.observe(self, date, ltt=ltt)

        if reflected:
            f = self.reflected.fluxd(g, wave, rap, unit=unit)
            fluxd += f * self.Afrho1.value * g['rh'].to(u.au).value**self.k

        if thermal:
            f = self.thermal.fluxd(g, wave, rap, unit=unit)
            fluxd += f * self.Afrho1.value * g['rh'].to(u.au).value**self.k

        return fluxd

class Comet(SolarSysObject):
    """A comet.

    Parameters
    ----------
    state : State
      The location of the comet.
    Afrho1 : Quantity
      Afrho at 1 AU.
    R : Quantity
      Nucleus radius.
    Ap : float, optional
      Geometric albedo of the nucleus.
    nucleus : dict or Asteroid
      The nucleus of the comet as an `Asteroid` instance, or a
      dictionary of keywords to initialize a new `Asteroid`.
    coma : dict or Coma
      The coma of the comet as a `Coma` instance or a dictionary of
      keywords to initialize a new `Coma`.
    name : string, optional
      A name for this comet.

    Attributes
    ----------
    nucleus : The nucleus as an `Asteroid` instance.
    coma : The coma as a `Coma` instance.

    Methods
    -------
    fluxd : Total flux density as seen by an observer.

    Examples
    --------
    Create a comet with `Asteroid` and `Coma` objects.

    >>> import astropy.units as u
    >>> from mskpy import Asteroid, Coma, Comet, SpiceState
    >>> state = SpiceState('hartley 2')
    >>> Afrho1 = 302 * u.cm
    >>> R = 0.6 * u.km
    >>> Ap = 0.04
    >>> nucleus = Asteroid(state, R * 2, Ap, eta=1.0, epsilon=0.95)
    >>> coma = Coma(state, Afrho1, S=0.0, A=0.37, Tscale=1.18)
    >>> comet = Comet(state, Afrho1, R, Ap, nucleus=nucleus, coma=coma)

    Create a comet with keyword arguments.

    >>> import astropy.units as u
    >>> from mskpy import Comet, SpiceState
    >>> Afrho1 = 302 * u.cm
    >>> R = 0.6 * u.km
    >>> nucleus = dict(eta=1.0, epsilon=0.95)
    >>> coma = dict(S=0.0, A=0.37, Tscale=1.18)
    >>> comet = Comet(SpiceState('hartley 2'), Afrho1, R, nucleus=nucleus, coma=coma)

    """

    def __init__(self, state, Afrho1, R, Ap=0.04, nucleus=dict(), coma=dict(),
                 name=None):
        assert isinstance(state, State)
        self.state = state
        self.name = name

        if isinstance(nucleus, dict):
            self.nucleus = Asteroid(self.state, 2 * R, Ap, **nucleus)
        else:
            self.nucleus = nucleus

        if isinstance(coma, dict):
            self.coma = Coma(self.state, Afrho1, **coma)
        else:
            self.coma = coma

        # these properties will update nucleus and coma
        self.Afrho1 = Afrho1
        self.R = R
        self.Ap = Ap

    @property
    def R(self):
        return self.nucleus.D / 2.0

    @R.setter
    def R(self, r):
        self.nucleus.D = 2 * r

    @property
    def Ap(self):
        return self.nucleus.Ap

    @Ap.setter
    def Ap(self, p):
        self.nucleus.Ap = p

    @property
    def Afrho1(self):
        return self.coma.Afrho1

    @Afrho1.setter
    def Afrho1(self, a):
        self.coma.Afrho1 = a

    def fluxd(self, observer, date, wave, rap=1.0 * u.arcsec,
              reflected=True, thermal=True, nucleus=True, coma=True,
              ltt=False, unit=u.Unit('W / (m2 um)'), **kwargs):
        """Total flux density as seen by an observer.

        Parameters
        ----------
        observer : SolarSysObject
          The observer.
        date : string, float, astropy Time, datetime
          The time of the observation in any format acceptable to
          `observer`.
        wave : Quantity
          The wavelengths to compute `fluxd`.
        rap : Quantity, optional
          The aperture radius, angular or projected distance at the
          comet.
        reflected : bool, optional
          If `True` include the reflected light model.
        thermal : bool, optional
          If `True` include the thermal emission model.
        nucleus : bool, optional
          If `True` include the nucleus.
        coma : bool, optional
          If `True` include the coma.
        ltt : bool, optional
          Set to `True` to correct the object's position for light
          travel time.
        unit : astropy Unit
          The return unit, must be flux density.
        
        Returns
        -------
        fluxd : Quantity

        """

        fluxd = np.zeros(np.size(wave.value)) * unit

        if nucleus:
            fluxd += self.nucleus.fluxd(observer, date, wave,
                                        reflected=reflected,
                                        thermal=thermal, unit=unit)
        if coma:
            fluxd += self.coma.fluxd(observer, date, wave, rap=rap,
                                     reflected=reflected,
                                     thermal=thermal, unit=unit)

        return fluxd

def flux2Q(fgas, wave, geom, g, rap, v):
    """Convert gas emission to Q.

    Use when rho << gas photodissociation lengthscale.

    Q = 2 N v / (pi rho)

    Parameters
    ----------
    fgas : Quantity
      The total line/band emission from the gas in units of flux.
    wave : Quantity
      The wavelength of the line/band.
    geom : dict of Quantity, or ephem.Geom
      The observing circumstances (rh and delta).
    g : Quantity
      The g-factor of the line/band at 1 AU.
    rap : Quantity
      The radius of the aperture used to measure the flux.  May be an
      angle or length.
    v : Quantity
      The expansion velocity of the gas.

    Returns
    -------
    Q : Quantity
      The gas production rate.

    """

    from numpy import pi

    assert isinstance(fgas, u.Quantity)
    assert isinstance(wave, u.Quantity)
    assert isinstance(geom['delta'], u.Quantity)
    assert isinstance(geom['rh'], u.Quantity)
    assert isinstance(g, u.Quantity)
    assert isinstance(rap, u.Quantity)
    assert isinstance(v, u.Quantity)

    hc = 1.9864457e-25 * u.J * u.m

    if rap.unit.is_equivalent(u.radian):
        rho = (rap * geom['delta'].to(u.au).value
               * 725 * u.km / u.arcsec).decompose()
    elif rap.unit.is_equivalent(u.meter):
        rho = rap
    else:
        raise ValueError("rap must have angular or length units.")

    N = (4 * pi * geom['delta']**2 * fgas * wave / hc
         * geom['rh'].to(u.au).value**2 / g)

    return (2 * N * v / pi / rho).decompose()

def fluxd2afrho(wave, fluxd, rho, geom, sun=None, bandpass=None):
    """Convert flux density to A(th)frho.

    See A'Hearn et al. (1984) for the definition of Afrho.

    Parameters
    ----------
    wave : float or array
      The wavelength of flux.  [micron]
    fluxd : float or array
      The flux density of the comet.  [W/m2/um, or same units as sun
      keyword]
    rho : float
      The aperture radius.  [arcsec]
    geom : dictionary or ephem.Geom
      The observing geometry via keywords `rh`, `delta`.  [AU, AU]
    sun : float, optional
      Use this value for the solar flux density at 1 AU, or None to
      use calib.solar_flux().  [same units as flux parameter]
    bandpass : dict, optional
      Instead of using `sun`, set to a dictionary of keywords to pass,
      along with the solar spectrum, to `util.bandpass`.

    Returns
    -------
    afrho : float or ndarray
      The Afrho parameter.  [cm]

    Notes
    -----
    Farnham, Schleicher, and A'Hearn (2000), Hale-Bopp
    filter set:

      UC = 0.3449 um, qUC = 2.716e17 -> 908.9 W/m2/um
      BC = 0.4453 um, qBC = 1.276e17 -> 1934 W/m2/um
      GC = 0.5259 um, qGC = 1.341e17 -> 1841 W/m2/um
      RC = 0.7133 um, qRC = 1.975e17 -> 1250 W/m2/um

    """

    from . import util
    from . import calib
    import astropy.constants as const

    try:
        deltacm = geom['delta'].to(u.cm).value
        rh = geom['rh'].to(u.au).value
    except AttributeError:
        deltacm = geom['delta'] * const.au.to(u.cm).value
        rh = geom['rh']

    if sun is None:
        if bandpass is None:
            sun = calib.solar_flux(wave * u.um, unit=u.Unit('W/(m2 um)')).value
        else:
            sw, sf = calib.e490(smooth=True, unit=u.Unit('W/(m2 um)'))
            sun = util.bandpass(sw.micrometer, sf.value, **bandpass)[1]

    afrho = 4 * deltacm * 206265. / rho * fluxd * rh**2 / sun
    return afrho

def fluxd2efrho(wave, flux, rho, geom, Tscale=1.1):
    """Convert flux density to efrho (epsilon * f * rho).

    efrho is defined by Kelley et al. (2013, Icarus 225, 475-494).

    Parameters
    ----------
    wave : float or array
      The wavelength of flux.  [micron]
    flux : float or array
      The flux density of the comet.  [W/m2/um]
    rho : float
      The aperture radius.  [arcsec]
    geom : dictionary or ephem.Geom
      The observing geometry via keywords `rh`, `delta`.  [AU, AU]
    Tscale : float, optional
      Use a continuum temperature of `Tscale * 278 / sqrt(rh)` K.
      Kelley et al. (2013) suggest a default of 1.1.

    Returns
    -------
    efrho : float or ndarray
      The epsfrho parameter.  [cm]

    """

    from . import util
    import astropy.constants as const

    try:
        deltacm = geom['delta'].to(u.cm).value
        rh = geom['rh'].to(u.au).value
    except AttributeError:
        deltacm = geom['delta'] * const.au.to(u.cm).value
        rh = geom['rh']

    B = util.planck(wave, Tscale * 278. / np.sqrt(rh),
                    unit=u.Unit('W/(m2 um sr)'))
    B = B.value
    _rho = rho / 206265. * deltacm  # cm
    Om = np.pi * (rho / 206265.)**2  # sr
    I = flux / Om  # W/m2/um/sr
    return I * _rho / B

def m2afrho1(M1):
    """Convert JPL's absolute magnitude, M1, to Afrho at 1 AU.

    Based on an empirical correlation between M1 and Afrho as measured
    by A'Hearn et al. (1995).  There is easily a factor of 4 scatter
    about the trend line.

    Parameters
    ----------
    M1 : float
      Comet's absolute magnitude from JPL.

    Returns
    -------
    Afrho1 : float
      Afrho at 1 AU.  [cm]

    """
    return 10**(-0.208 * M1 + 4.687)

# update module docstring
from .util import autodoc
autodoc(globals())
del autodoc

