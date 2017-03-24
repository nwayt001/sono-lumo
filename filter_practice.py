#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 22 17:18:14 2017

@author: nicholas
"""

import wave
import struct
import numpy as np
import matplotlib.pyplot as plt
import hilbert
from scipy.signal import hilbert
waveFile = wave.open('short.wav', 'r')


length = waveFile.getnframes()
data = []
for i in range(0,length):
    waveData = waveFile.readframes(1)
    data.append( struct.unpack("<h", waveData))
    #print(int(data[0]))    
signal = np.array(data)
t = np.linspace(0.0, 60, length)

fig = plt.figure()
ax= fig.add_subplot(111)
# plot raw signal
ax.plot(t,signal)


# compute envelop
analytic_signal = hilbert(signal^2)
amplitude_envelope = np.abs(analytic_signal)
ax.plot(t,amplitude_envelope)


signal2 = signal^2



from scipy.signal import butter, lfilter
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import freqz


def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y

    
fs=waveFile.getframerate()
lowcut = 250.0
highcut = 1000.0

fs = 5000.0
lowcut = 500.0
highcut = 1250.0

# Plot the frequency response for a few different orders.
plt.figure(1)
plt.clf()
for order in [3, 6, 9, 50]:
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    w, h = freqz(b, a, worN=2000)
    plt.plot((fs * 0.5 / np.pi) * w, abs(h), label="order = %d" % order)

plt.plot([0, 0.5 * fs], [np.sqrt(0.5), np.sqrt(0.5)],
         '--', label='sqrt(0.5)')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Gain')
plt.grid(True)
plt.legend(loc='best')


 # Filter a noisy signal.
T = 0.05
nsamples = T * fs
t = np.linspace(0, T, nsamples, endpoint=False)
a = 0.02
f0 = 600.0
x = 0.1 * np.sin(2 * np.pi * 1.2 * np.sqrt(t))
x += 0.01 * np.cos(2 * np.pi * 312 * t + 0.1)
x += a * np.cos(2 * np.pi * f0 * t + .11)
x += 0.03 * np.cos(2 * np.pi * 2000 * t)

plt.figure(2)
plt.clf()
plt.plot(t, signal, label='Noisy signal')

plt.figure(3)
plt.clf()
y = butter_bandpass_filter(signal, lowcut, highcut, fs, order=3)
plt.plot(t, y, label='Filtered signal (%g Hz)' % f0)
plt.xlabel('time (seconds)')
plt.hlines([-a, a], 0, T, linestyles='--')
plt.grid(True)
plt.axis('tight')
plt.legend(loc='upper left')

plt.show()