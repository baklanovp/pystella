import csv
import numpy as np
import os

import matplotlib.pyplot as plt

import pystella.rf.rad_func as rf
from pystella.model.stella import Stella
from pystella.rf import band
from pystella.rf.lc import SetLightCurve, LightCurve

__author__ = 'bakl'

colors = band.bands_colors()

lntypes = dict(U="-", B="-", V="-", R="-", I="-",
               UVM2="-.", UVW1="-.", UVW2="-.",
               F125W="--", F160W="-.", F140W="--", F105W="-.", F435W="--", F606W="-.", F814W="--",
               u="--", g="--", r="--", i="--", z="--")

markers = {u'D': u'diamond', 6: u'caretup', u's': u'square', u'x': u'x',
           5: u'caretright', u'^': u'triangle_up', u'd': u'thin_diamond', u'h': u'hexagon1',
           u'+': u'plus', u'*': u'star', u'o': u'circle', u'p': u'pentagon', u'3': u'tri_left',
           u'H': u'hexagon2', u'v': u'triangle_down', u'8': u'octagon', u'<': u'triangle_left'}
markers = markers.keys()


def lbl(b, band_shift):
    shift = band_shift[b]
    l = b
    if shift > 0:
        l += '+' + str(shift)
    elif shift < 0:
        l += '-' + str(abs(shift))
    return l


def plot_ubv_models(ax, models_dic, bands, band_shift, xlim=None, ylim=None, is_time_points=False):
    is_compute_x_lim = xlim is None
    is_compute_y_lim = ylim is None

    t_points = [0.2, 1, 2, 3, 4, 5, 10, 20, 40, 80, 150]

    lw = 1.
    mi = 0
    ib = 0
    x_max = []
    y_mid = []
    lc_min = {}
    for mname, mdic in models_dic.iteritems():
        mi += 1
        for bname in bands:
            ib += 1
            x = mdic['time']
            y = mdic[bname]
            bcolor = colors[bname]
            ax.plot(x, y, label='%s  %s' % (lbl(bname, band_shift), mname), color=bcolor, ls="-", linewidth=lw)
            # ax.plot(x, y, marker=markers[mi % (len(markers) - 1)], label='%s  %s' % (lbl(bname, band_shift), mname),
            #         markersize=4, color=bcolor, ls="-", linewidth=lw)

            if is_time_points:
                integers = [np.abs(x - t).argmin() for t in t_points]  # set time points
                for (X, Y) in zip(x[integers], y[integers]):
                    ax.annotate('{:.0f}'.format(X), xy=(X, Y), xytext=(-10, 20), ha='right',
                                textcoords='offset points', color=bcolor,
                                arrowprops=dict(arrowstyle='->', shrinkA=0))
            idx = np.argmin(y)
            lc_min[bname] = [x[idx], y[idx]]
            if is_compute_x_lim:
                x_max.append(np.max(x))
            if is_compute_y_lim:
                y_mid.append(np.min(y))

    if is_compute_x_lim:
        xlim = [-10, np.max(x_max) + 10.]
    if is_compute_y_lim:
        ylim = [np.min(y_mid) + 7., np.min(y_mid) - 2.]

    ax.invert_yaxis()
    # if is_x_lim:
    ax.set_xlim(xlim)
    # if is_y_lim:
    ax.set_ylim(ylim)

    return lc_min


def plot_models_curves(ax, models_dic, bands, band_shift, xlim=None, ylim=None, is_time_points=False):
    is_compute_x_lim = xlim is None
    is_compute_y_lim = ylim is None

    t_points = [0.2, 1, 2, 3, 4, 5, 10, 20, 40, 80, 150]

    lw = 1.
    mi = 0
    ib = 0
    x_max = []
    y_mid = []
    lc_min = {}
    for mname, curves in models_dic.iteritems():
        mi += 1
        for bname in bands:
            ib += 1
            x = curves.TimeDef
            y = curves[bname].Mag
            bcolor = colors[bname]
            ax.plot(x, y, label='%s  %s' % (lbl(bname, band_shift), mname), color=bcolor, ls="-", linewidth=lw)
            # ax.plot(x, y, marker=markers[mi % (len(markers) - 1)], label='%s  %s' % (lbl(bname, band_shift), mname),
            #         markersize=4, color=bcolor, ls="-", linewidth=lw)

            if is_time_points:
                integers = [np.abs(x - t).argmin() for t in t_points]  # set time points
                for (X, Y) in zip(x[integers], y[integers]):
                    ax.annotate('{:.0f}'.format(X), xy=(X, Y), xytext=(-10, 20), ha='right',
                                textcoords='offset points', color=bcolor,
                                arrowprops=dict(arrowstyle='->', shrinkA=0))
            idx = np.argmin(y)
            lc_min[bname] = [x[idx], y[idx]]
            if is_compute_x_lim:
                x_max.append(np.max(x))
            if is_compute_y_lim:
                y_mid.append(np.min(y))

    if is_compute_x_lim:
        xlim = [-10, np.max(x_max) + 10.]
    if is_compute_y_lim:
        ylim = [np.min(y_mid) + 7., np.min(y_mid) - 2.]

    ax.invert_yaxis()
    # if is_x_lim:
    ax.set_xlim(xlim)
    # if is_y_lim:
    ax.set_ylim(ylim)

    return lc_min


def plot_bands(dict_mags, bands, title='', fname='', distance=10., is_time_points=True):
    plt.title(''.join(bands) + ' filter response')

    # colors = band.bands_colors()
    # colors = dict(U="blue", B="cyan", V="black", R="red", I="magenta",
    #               J="blue", H="cyan", K="black",
    #               UVM2="green", UVW1="red", UVW2="blue",
    #               g="black", r="red", i="magenta", u="blue", z="magenta")
    # band_shift = dict(U=6.9, B=3.7, V=0, R=-2.4, I=-4.7,
    #                   UVM2=11.3, UVW1=10, UVW2=13.6,
    #                   u=3.5, g=2.5, r=-1.2, i=-3.7, z=-4.2)
    band_shift = dict((k, 0) for k, v in colors.items())  # no y-shift

    t_points = [2, 5, 10, 20, 40, 80, 150]

    dm = 5 * np.log10(distance) - 5  # distance module
    # dm = 0
    xlims = [-10, 200]
    ylims = [-12, -19]
    ylims += dm
    is_auto_lim = True
    if is_auto_lim:
        ylims = [0, 0]

    x = dict_mags['time']
    is_first = True
    for n in bands:
        y = dict_mags[n]
        y += dm + band_shift[n]
        plt.plot(x, y, label=lbl(n, band_shift), color=colors[n], ls=lntypes[n], linewidth=2.0, marker='s')
        if is_time_points and is_first:
            is_first = False
            integers = [np.abs(x - t).argmin() for t in t_points]  # set time points
            for (X, Y) in zip(x[integers], y[integers]):
                plt.annotate('{:.0f}'.format(X), xy=(X, Y), xytext=(10, -30), ha='right',
                             textcoords='offset points',
                             arrowprops=dict(arrowstyle='->', shrinkA=0))

        if is_auto_lim:
            if ylims[0] < max(y[len(y) / 2:]) or ylims[0] == 0:
                ylims[0] = max(y[len(y) / 2:])
            if ylims[1] > min(y) or ylims[1] == 0:
                ylims[1] = min(y)

    ylims = np.add(ylims, [1, -1])
    plt.gca().invert_yaxis()
    plt.xlim(xlims)
    plt.ylim(ylims)
    plt.legend()
    plt.ylabel('Magnitude')
    plt.xlabel('Time [days]')
    plt.title(title)
    plt.grid()
    if fname != '':
        plt.savefig("ubv_%s.png" % fname, format='png')
    plt.show()
    # plt.close()


def compute_mag(name, path, bands, ext=None, z=0., distance=10., magnification=1., is_show_info=True, is_save=False):
    """
        Compute magnitude in bands for the 'name' model.
    :type ext: extinction
    :param name: the name of a model and data files
    :param path: the directory with data-files
    :param bands: photometric bands
    :param z: redshift, default 0
    :param distance: distance to star in parsec, default 10 pc
    :param magnification: gravitational lensing magnification
    :param is_show_info: flag to write some information, default True
    :param is_save: flag to save result in file, default False
    :return: dictionary with keys = bands, value = star's magnitudes
    """
    model = Stella(name, path=path)
    if is_show_info:
        print ''
        model.show_info()

    if not model.is_spec_data:
        model.show_info()
        print "Error: No data for: " + str(model)
        return None

    # serial_spec = model.read_serial_spectrum(t_diff=0.)
    serial_spec = model.read_serial_spectrum(t_diff=1.05)
    mags = serial_spec.compute_mags(bands, z=z, dl=rf.pc_to_cm(distance), magnification=magnification)

    if mags is not None:
        fname = os.path.join(path, name + '.ubv')
        if is_save:
            mags_save(mags, bands, fname)
            print "Magnitudes have been saved to " + fname

    if is_show_info:
        # print the time of maximum LC
        tmin = 2.0
        t = mags['time']
        for n in bands:
            t_min = t[t > tmin][mags[n][t > tmin].argmin()]
            print "t_max(%s) = %f" % (n, t_min)

    if ext is not None:
        # add extinction
        for n in bands:
            mags[n] = mags[n] + ext[n]

    return mags


def compute_curves(name, path, bands, ext=None, z=0., distance=10., magnification=1., is_show_info=True, is_save=False):
    """
        Compute magnitude in bands for the 'name' model.
    :type ext: extinction
    :param name: the name of a model and data files
    :param path: the directory with data-files
    :param bands: photometric bands
    :param z: redshift, default 0
    :param distance: distance to star in parsec, default 10 pc
    :param magnification: gravitational lensing magnification
    :param is_show_info: flag to write some information, default True
    :param is_save: flag to save result in file, default False
    :return: dictionary with keys = bands, value = star's magnitudes
    """
    if len(bands) == 0:
        raise ValueError("Error: No data for: " + str(name))

    model = Stella(name, path=path)
    if is_show_info:
        print ''
        model.show_info()

    if not model.is_spec_data:
        model.show_info()
        raise ValueError("Error: No data for: " + str(model))

    # serial_spec = model.read_serial_spectrum(t_diff=0.)
    serial_spec = model.read_serial_spectrum(t_diff=1.05)
    curves = SetLightCurve(name)
    for n in bands:
        b = band.band_by_name(n)
        mags = serial_spec.flux_to_mags(b, z=z, dl=rf.pc_to_cm(distance), magnification=magnification)
        time = serial_spec.times * (1. + z)
        lc = LightCurve(b, time, mags)
        curves.add(lc)

    if is_save:
        fname = os.path.join(path, name + '.ubv')
        curves.save(fname)
        print "Magnitudes have been saved to " + fname

    if is_show_info:
        # print the time of maximum LC
        tmin = 2.0
        t = curves.TimeDef
        for n in bands:
            t_min = t[t > tmin][curves[n][t > tmin].argmin()]
            print "t_max(%s) = %f" % (n, t_min)

    if ext is not None:
        # add extinction
        for n in bands:
            curves[n].mshift = curves[n].mshift + ext[n]  # TODO check plus-minus

    return curves


def mags_save(dictionary, bands, fname):
    with open(fname, 'wb') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['{:^8s}'.format(x) for x in ['time'] + bands])
        for i, (row) in enumerate(zip(*[dictionary[k] for k in 'time'.split() + bands])):
            # row = row[-1:] + row[:-1]  # make time first column
            writer.writerow(['{:8.3f}'.format(x) for x in row])
            # writer.writerow(['{:3.4e}'.format(x) for x in row])