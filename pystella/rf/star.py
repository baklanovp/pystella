from scipy import interpolate
import numpy as np
from scipy.integrate import simps as integralfunc

from pystella.util.phys_var import phys

__author__ = 'bakl'


class Star:
    def __init__(self, name, spec=None):
        """Creates a Spectrum instance.  Required parameters:  name."""
        self.name = name
        self._sp = spec
        self.radius_ph = None
        self.z = None
        self.distance = None

    def set_radius_ph(self, radius):
        self.radius_ph = radius

    def set_distance(self, distance):
        self.distance = distance

    @property
    def IsRedshift(self):
        return self.z is not None and self.z > 0.

    @property
    def IsRadius(self):
        return self.radius_ph is not None

    @property
    def IsDistance(self):
        return self.distance is not None

    @property
    def IsRadiusDist(self):
        return self.IsRadius and self.IsDistance

    @property
    def Freq(self):
        if self._sp is None:
            raise ValueError("Spectrum has not been defined. ")
        if self.IsRedshift:
            return self._sp.freq * (1. + self.z)  # redshift the flux
        else:
            return self._sp.freq

    @property
    def Wl(self):
        if self._sp is None:
            raise ValueError("Spectrum has not been defined. ")
        return phys.c / self.Freq

    @property
    def Flux(self):
        if self._sp is None:
            raise ValueError("Spectrum has not been defined. ")
        if self.IsRedshift:
            return Star.flux_to_redshift(self._sp.freq, self._sp.flux, self.z)
        else:
            return self._sp.flux

    @property
    def Flux_wl(self):
        return self.Flux * self.Freq ** 2 / phys.c  # flux [erg/cm^2/cm) ]

    @property
    def Luminosity(self):
        if self.radius_ph is None:
            raise ValueError("Photospheric radius has not been defined. ")

        return 4.*np.pi * self.radius_ph**2 * self.Flux

    @property
    def FluxObs(self):
        if self.IsRadiusDist:
            return self.Luminosity / (4*np.pi * self.distance**2)
        elif self.IsDistance:
            return self.Flux / (4*np.pi * self.distance**2)
        else:
            return self.Flux

    @property
    def FluxWlObs(self):
        if self.IsRadiusDist:
            return self.Flux_wl * (self.radius_ph/self.distance)**2
        elif self.IsDistance:
            return self.Flux_wl / (4*np.pi * self.distance**2)
        else:
            return self.Flux_wl

    def _response(self, band, is_b_spline=True):
        """
        Compute response flux using provided spectral band
        :param band:  photometric band
        :param is_b_spline:  the method of interpolation
        :return: :raise ValueError:
        """
        wl = self.Wl
        if min(wl) > band.wl[0] or max(wl) < band.wl[-1]:
            raise ValueError("Spectrum must be wider then band: " + str(band))

        flux = self.FluxWlObs / phys.cm_to_angs  # to flux [erg/cm^2/A) ]
        wl_s = wl * phys.cm_to_angs
        wl_b = band.wl * phys.cm_to_angs

        if is_b_spline:
            tck = interpolate.splrep(wl_s, flux, s=0)
            flux_spline = interpolate.splev(wl_b, tck, der=0)
        else:
            flux_spline = np.interp(wl_b, wl_s, flux, 0, 0)  # One-dimensional linear interpolation.

        a = integralfunc(flux_spline * band.resp * wl_b, wl_b) / (phys.c * phys.cm_to_angs) / phys.h
        return a

    def set_redshift(self, z):  # shift spectrum to rest frame
        self.z = z

    def flux_to_mag(self, band):
        conv = self._response(band)
        if conv <= 0:
            return None
        else:
            mag = -2.5 * np.log10(conv) + band.zp
            return mag

    def flux_to_magAB(self, band):
        conv = self._response(band)
        if conv <= 0:
            return None
        else:
            mag = -2.5 * np.log10(conv) + phys.ZP_AB
            return mag

    def flux_to_AB(self):
        return -2.5 * np.log10(self.FluxObs) + phys.ZP_AB

    def k_cor(self, band_r, band_o, z=0.):
        """
        Compute K-correction for observed and rest-frame bands.

       Args:
          band_r: Rest-frame band.
          band_o: Observed band.
          z:     redshift

       Returns:
          * K: K-correction
          * If failed return None
       """
        # todo make k-correction with b-splinesec

        if z > 0:
            self.set_redshift(z)

        z_o = z
        if self.IsRedshift:
            z_o = self.z

        self.set_redshift(0.)
        resp_0 = self._response(band_r, is_b_spline=False)

        self.set_redshift(z_o)
        resp_z = self._response(band_o, is_b_spline=False)

        if resp_0 < 0 or resp_z <= 0:
            return None
        else:
            kcor = -2.5 * np.log10(resp_z / resp_0 / (1 + z_o)) + band_r.zp - band_o.zp
            return kcor

    @staticmethod
    def flux_to_redshift(freq, flux, z):   # todo(bakl): check redshift, * F(nu*(1+Z))/F(nu)
        if z <= 0.:
            return flux
        flux_z = np.interp(freq*(1.+z), freq, flux)
        flux *= (1.+z) * flux_z/flux
        return flux