import json
import logging

import pandas

from pystella.rf import band
from pystella.rf.lc import SetLightCurve, LightCurve
from pystella.rf.spectrum import SeriesSpectrum, Spectrum

# from pandas.io import json

__author__ = 'bakl'

logging.basicConfig()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SneSpace:
    def __init__(self):
        """Creates a SneSpace model instance.  Required parameters:  name."""
        self._name = None
        self._fname = None
        self._data = None
        self._serial_spec = None

    @property
    def data(self):
        return self._data

    @property
    def Name(self):
        if self._name is not None:
            return self._name
        if self.data is None:
            return None
        self._name = next(iter(self.data.keys()))
        return self._name

    @property
    def photometry(self):
        return self.property('photometry')

    @property
    def spectra(self):
        return self.property('spectra')

    @property
    def lumdist(self):
        l = self.property('lumdist')
        if l is not None:
            d = float(l[0]['value'])
            u = l[0]['u_value'].lower()
            if u == 'mpc':
                d *= 1.e6
            return d
        return None

    @property
    def comovingdist(self):
        l = self.property('comovingdist')
        if l is not None:
            dd = 0.
            for node in l:
                d = float(node['value'])
                u = node['u_value'].lower()
                if u == 'mpc':
                    d *= 1.e6
                dd += d
            return dd / len(l)
        return None

    def property(self, name):
        if self.data is None:
            return None
        return self._data[self.Name][name]

    def __str__(self):
        return "%s, path: %s" % (self.Name, self._fname)

    def __repr__(self):
        return "%s, path: %s" % (self.Name, self._fname)

    def load(self, fname):
        try:
            with open(fname, 'r') as f:
                self._data = json.loads(f.read())
        except ValueError as e:
            logger.error("Could not parse {0} due to {1}.".format(fname, e))
            return False
        else:
            self._fname = fname
        return True

    def to_curves(self):
        ph = pandas.DataFrame.from_dict(self.photometry)

        def add(d, k, v):
            if k in d:
                d[k].append(v)
            else:
                d[k] = [v]

        times = {}
        mags = {}
        err = {}
        for b, t, m, e in zip(ph.band, ph.time, ph.magnitude, ph.e_magnitude):
            add(times, b, t)
            add(mags, b, m)
            add(err, b, e)

        bands = list(times.keys())

        band.Band.load_settings()
        curves = SetLightCurve(self.Name)
        for bname in bands:
            if band.band_is_exist(bname):
                tt = list(map(float, times[bname]))
                mm = list(map(float, mags[bname]))
                ee = list(map(float, err[bname]))
                lc = LightCurve(bname, tt, mm, ee)
                curves.add(lc)

        return curves

    def to_spectra(self):
        series = SeriesSpectrum(self.Name)

        def to_pystella_spec(name, tbl):
            lmd = []
            flux = []
            for x in tbl:
                lmd.append(float(x[0]))
                flux.append(float(x[1]))
            if len(lmd) > 0:
                sp = Spectrum.from_lambda(name, lmd, flux, u_lmd="A")
                return sp
            return None

        for i, item in enumerate(self.spectra):
            tbl = item
            # filter bad spectra
            if "u_fluxes" not in tbl:
                continue
            # if tbl["u_fluxes"].lower() == 'Uncalibrated'.lower():
            #     continue
            # tbl = pandas.DataFrame.from_dict(item)
            if 'time' in tbl:
                t = float(tbl['time'])
                name = tbl['filename']
                # take flux in "erg/s/cm^2/Angstrom" ?
                spec = to_pystella_spec(name, tbl['data'])
                if spec is not None:
                    series.add(t, spec)

        return series