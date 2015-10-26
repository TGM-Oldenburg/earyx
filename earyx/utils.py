"""
This module provides useful helper function often used for signal genration in
psychoacoustic experiments. Implementation inspired by "Psylab" a similar
framework written in Matlab by Martin Hasen.
"""

import numpy as np
import math

def hanwin(sig,flank_len=None):
    """window signal with hanning window - the complete window or with flanks"""
    
    if flank_len is None:
        flank_len =math.floor(len(sig)/2)    
    if 2*flank_len > len(sig):
        print("warning: 2*flank_len > siglen, now flanking whole sig")
        h_window = _hanning_window(len(sig))
    else:
        han_flanks = _hanning_window(2*flank_len)
        ones = np.ones(len(sig) - 2*flank_len)
        h_window = list(han_flanks[0:flank_len+1]) + list(ones) + \
                   list(han_flanks[flank_len+1:])
    return h_window * sig

def _hanning_window(n):
    """return N point symmetric hanning window including starting and
    ending zero"""
    t = np.arange(0,n)
    return np.array(0.5 * (1 + np.cos(-math.pi+2*math.pi/(n-1)*t)))

def fft_rect_filt(signal, f1, f2, fsamp, notch=None, high_idx_offset=None):
    """ rectangular shape bandpass/notch filter via fft
    ---------------------------------------------------------------------
    Usage: y = fft_rect_filt(x, f1, f2, fsamp, notch, high_idx_offset) 

    input:  ----------
    x  input signal
    f1  lower edge freq (min.: 0,  max.:fsamp/2)
    f2  upper edge freq (min.: f1, max.:fsamp/2)
    fsamp  samplingrate of x
    notch  (optional, default 0) set to 1, to specify
    notch-filter instead of band-pass  
    high_idx_offset  (optional, default 0) offset for upper edge
    frequency index.  Set to -1 for use of fft_rect_filt
    for a filterbank purpose, so that neighbour bands
    have zero overlap samples.
    output:  ----------
    y  filtered output signal

    Filter signal x having samplingrate fsamp via FFT, so that
    frequencies between f1 and f2 (both inclusive) are passed through,
    unless notch is set ~=0, which means pass frequencies outside of
    f1 and f2.  Output to y.  The filter has rectangular shape in
    frequency domain, i.e., it has very steep slopes of approx. 300 dB
    damping within the bandwidth of 1 FFT-bin.  It is possible that
    f1==f2, resulting in a filter passing through (or notching) only 1
    single FFT-bin.  Because of the FFT, this script works fastest
    with signal lengths that are powers of 2.

    For filterbank purposes, high_idx_offset should be set to -1 to
    assure that neighbouring bands have exactly zero samples
    overlap at the common edge frequencies, see the following example: 
    a = fft_rect_filt(x,    0,  300, fs, 0, -1);
    b = fft_rect_filt(x,  300, 1000, fs, 0, -1);
    c = fft_rect_filt(x, 1000, 2000, fs, 0, -1);
    """
        
    if f1 > f2 or max(f1,f2) > (fsamp/2) or min(f1,f2) < 0:
        print(" 0 <= f1 <= f2 <= (fsamp/2) is required ")        #warning??
        
    if notch is None:
        notch = 0
        
    if high_idx_offset is None:
        high_idx_offset = 0
        
    signal = np.fft.fft(signal)
    n = len(signal)
    
    idx1 = 1+np.floor(n * f1/fsamp )
    idx2 = 1+np.floor(n * f2/fsamp ) + high_idx_offset
    idx3 = n - idx2 + 2
    idx4 = n - idx1 + 2
    
    #copy spectrum signal
    ff = signal
    
    ff[:idx1-1] = 0
    ff[idx2+1:idx3-1] = 0
    ff[idx4+1:] = 0
    
    if notch == 1:
        # make a notch instead a pass
        ff = signal - ff
    
    return np.fft.ifft(ff).real

def gensin(freq, ampl, length, phase=0, fsamp=48000):
    """Function creates sine tone with given parameters"""
    t = np.arange(0, length, (1/fsamp)).T
    y = np.array(ampl * np.sin(2*np.pi * (freq*t + phase/360)))
    return y


def rms(signal):
    """Calculate the root mean square"""
    return np.sqrt(np.mean(np.square(signal)))


def htc(ampl, fs, dur, f0, f_start, f_end, C, calib=0):
    """
    generates harmonic tone complex
    """

    start_nr = np.ceil(f_start/f0)
    end_nr = np.floor(f_end/f0)
    components = np.arange(start_nr, end_nr+1, 1)
    N = len(components)

    comp_ampl_db = 10*((ampl/10)-np.log10(N))
    ampl = np.sqrt(2)*10**((comp_ampl_db-calib)/20)

    htc_out = np.zeros(dur*fs)
    for n in components:
        phase = (C*np.pi*n*(n-1)/N)*180/np.pi
        htc_out += gensin(n*f0,ampl,dur,phase,fs)
    return htc_out
