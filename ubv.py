#!/usr/bin/python
# -*- coding: utf-8 -*-
from pystella.util import rf

__author__ = 'bakl'

import os
import sys
import getopt
from os.path import dirname
from os import listdir
from os.path import isfile, join
import csv
import numpy as np

import matplotlib.pyplot as plt

from pystella.model.stella import Stella
from pystella.rf import band

ROOT_DIRECTORY = dirname(dirname(os.path.abspath(__file__)))


def plot_bands(dict_mags, bands, title='', distance=10.):
    plt.title(''.join(bands) + ' filter response')

    colors = dict(U="blue", B="cyan", V="black", R="red", I="magenta",
                  UVM2="green", UVW1="red", UVW2="blue",
                  g="black", r="red", i="magenta", u="blue", z="magenta")
    lntypes = dict(U="-", B="-", V="-", R="-", I="-",
                   UVM2="-.", UVW1="-.", UVW2="-.",
                   u="--", g="--", r="--", i="--", z="--")
    band_shift = dict(U=6.9, B=3.7, V=0, R=-2.4, I=-4.7,
                      UVM2=11.3, UVW1=10, UVW2=13.6,
                      u=3.5, g=2.5, r=-1.2, i=-3.7, z=-4.2)
    band_shift = dict((k, 0) for k, v in band_shift.items())  # no y-shift

    dm = 5 * np.log10(distance) - 5  # distance module
    # dm = 0
    lims = [-12, -19]
    lims += dm
    is_auto_lim = True
    if is_auto_lim:
        lims = [0, 0]

    def lbl(b):
        shift = band_shift[b]
        l = b
        if shift > 0:
            l += '+' + str(shift)
        elif shift < 0:
            l += '-' + str(abs(shift))
        return l

    x = dict_mags['time']
    for n in bands:
        y = dict_mags[n]
        y += dm + band_shift[n]
        plt.plot(x, y, label=lbl(n), color=colors[n], ls=lntypes[n], linewidth=2.0)
        if is_auto_lim:
            if lims[0] < max(y[len(y) / 2:]) or lims[0] == 0:
                lims[0] = max(y[len(y) / 2:])
            if lims[1] > min(y) or lims[1] == 0:
                lims[1] = min(y)

    lims = np.add(lims, [1, -1])
    plt.gca().invert_yaxis()
    plt.xlim([-10, 200])
    plt.ylim(lims)
    plt.legend()
    plt.ylabel('Magnitude')
    plt.xlabel('Time [days]')
    plt.title(title)
    plt.grid()
    plt.show()


def compute_mag(name, path, bands, is_show_info=True, is_save=False):
    model = Stella(name, path=path)
    if is_show_info:
        print ''
        model.show_info()

    if not model.is_spec_data:
        print "No data for: " + str(model)
        return None

    # serial_spec = model.read_serial_spectrum(t_diff=0.)
    serial_spec = model.read_serial_spectrum(t_diff=1.05)

    mags = dict((k, None) for k in bands)

    z, distance = 0, 10.  # pc for Absolute magnitude
    # z, distance = 0.145, 687.7e6  # pc for comparison with Maria
    for n in bands:
        b = band.band_by_name(n)
        mags[n] = serial_spec.flux_to_mags(b, z=z, dl=rf.pc_to_cm(distance))

    mags['time'] = serial_spec.times * (1. + z)

    if mags is not None:
        fname = os.path.join(path, name + '.ubv')
        if is_save:
            mags_save(mags, bands, fname)
            print "Magnitudes have been saved to " + fname
        if is_show_info:
            plot_bands(mags, bands, title=name, distance=distance)
    return mags


def mags_save(dictionary, bands, fname):
    with open(fname, 'wb') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['{:^8s}'.format(x) for x in ['time'] + bands])
        for i, (row) in enumerate(zip(*[dictionary[k] for k in 'time'.split() + bands])):
            # row = row[-1:] + row[:-1]  # make time first column
            writer.writerow(['{:8.3f}'.format(x) for x in row])
            # writer.writerow(['{:3.4e}'.format(x) for x in row])


def usage():
    bands = band.band_get_names().keys()
    print "Usage:"
    print "  ubv.py [params]"
    print "  -b <bands>: string, default: U-B-V-R-I, for example U-B-V-R-I-u-g-i-r-z-UVW1-UVW2.\n" \
          "     Available: " + '-'.join(sorted(bands))
    print "  -i <model name>.  Example: cat_R450_M15_Ni007_E7"
    print "  -d <model directory>, default: ./"
    print "  -e <model extension> is used to define model name, default: tt "
    print "  -s  silence mode: no info, no plot"
    print "  -w  write magnitudes to file, default 'False'"
    print "  -h  print usage"


def main(name='', model_ext='.tt'):
    is_silence = False
    is_save_mags = False
    path = ''

    try:
        opts, args = getopt.getopt(sys.argv[1:], "swhd:e:i:b:")
    except getopt.GetoptError as err:
        print str(err)  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    if len(opts) == 0:
        usage()
        sys.exit(2)

    if not name:
        for opt, arg in opts:
            if opt == '-i':
                path = ROOT_DIRECTORY
                name = str(arg)
                break
                # if name == '':
                #     print 'Error: you should specify the name of model.'
                #     sys.exit(2)

    bands = ['U', 'B', 'V', 'R', "I"]
    # bands = ['U', 'B', 'V', 'R', "I", 'UVM2', "UVW1", "UVW2", 'g', "r", "i"]

    for opt, arg in opts:
        if opt == '-e':
            model_ext = '.' + arg
            continue
        if opt == '-b':
            bands = str(arg).split('-')
            for b in bands:
                if not band.band_is_exist(b):
                    print 'No such band: ' + b
                    sys.exit(2)
            continue
        if opt == '-s':
            is_silence = True
            continue
        if opt == '-w':
            is_save_mags = True
            continue
        if opt == '-d':
            path = str(arg)
            if not (os.path.isdir(path) and os.path.exists(path)):
                print "No such directory: " + path
                sys.exit(2)
            continue
        elif opt == '-h':
            usage()
            sys.exit(2)

    if name != '':
        compute_mag(name, path, bands, is_show_info=not is_silence, is_save=is_save_mags)

    elif path != '':  # run for whole path
        names = []
        files = [f for f in listdir(path) if isfile(join(path, f)) and f.endswith(model_ext)]
        for f in files:
            names.append(os.path.splitext(f)[0])
        if len(names) > 0:
            for name in names:
                compute_mag(name, path, bands, is_show_info=not is_silence, is_save=is_save_mags)
        else:
            print "There are no models in the directory: %s with extension: %s " % (path, model_ext)


if __name__ == '__main__':
    main()
    # main(name="cat_R1000_M15_Ni007_E15")