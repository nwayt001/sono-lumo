from __future__ import print_function

import sys
import time
import alsaaudio
import struct
import numpy as np
import numpy as numpy
from Adafruit_PWM_Servo_Driver import PWM
import matplotlib.pyplot as plt

# Parameters for USB mic Sound Processing
USB_Name = 'hw:CARD=C920' #change name to final USB mic
SamplingRate = 44100
Channels = 1
chunk = 2000
nfft = 2*chunk
freqs = np.linspace(0.0,1.0/(2.0*(1.0/SamplingRate)),nfft/2.0)
time_resol = (nfft*(1.0) / SamplingRate*(1.0)) *1000.0
windowF = np.hamming(nfft)
cmap = 'rainbow'
colors = plt.get_cmap(cmap)

# Parms for RasPi Hat
Ch_r1 = 1
Ch_b1 = 2
Ch_g1 = 3
Ch_r2 = 5
Ch_b2 = 6
Ch_g2 = 7
Ch_r3 = 9
Ch_b3 = 10
Ch_g3 = 11
Ch_r4 = 13
Ch_b4 = 14
Ch_g4 = 15
pulse_width = 0.5
num_tics = 4096.0

ring1_color=colors(0)
ring2_color=colors(0)
ring3_color=colors(0)
ring3_color=colors(0)

# Initialize the RasPi Hat (for Raspi only)
pwm = PWM(0x40)
pwm.setPWMFreq(1000) # set to max frequency


# Open the device in nonblocking capture mode. 
inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, USB_Name)

# Set attributes for recording:
inp.setchannels(Channels)
inp.setrate(SamplingRate)
inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
inp.setperiodsize(chunk)


def setColorChain():
    tmp = ring1_color[0]*num_tics
    pwm.setPWM(Ch_r1,0, (ring1_color[0]*num_tics).astype(int))
    pwm.setPWM(Ch_g1,0, (ring1_color[1]*num_tics).astype(int))
    pwm.setPWM(Ch_b1,0, (ring1_color[2]*num_tics).astype(int))
    
    pwm.setPWM(Ch_r2,0, (ring2_color[0]*num_tics).astype(int))
    pwm.setPWM(Ch_g2,0, (ring2_color[1]*num_tics).astype(int))
    pwm.setPWM(Ch_b2,0, (ring2_color[2]*num_tics).astype(int))
    
    pwm.setPWM(Ch_r3,0, (ring3_color[0]*num_tics).astype(int))
    pwm.setPWM(Ch_g3,0, (ring3_color[1]*num_tics).astype(int))
    pwm.setPWM(Ch_b3,0, (ring3_color[2]*num_tics).astype(int))
    
    pwm.setPWM(Ch_r4,0, (ring4_color[0]*num_tics).astype(int))
    pwm.setPWM(Ch_g4,0, (ring4_color[1]*num_tics).astype(int))
    pwm.setPWM(Ch_b4,0, (ring4_color[2]*num_tics).astype(int))

    
# read from device
while 1:
    l, data = inp.read()
    
    if l>0:
        fmt = "%dH"%(len(data)/2)
        data2 = struct.unpack(fmt, data)
        data2 = np.array(data2, dtype='h')
        data2 = windowF*data2        
        # Apply FFT
        yf = np.fft.rfft(data2)
        yf = 2.0/nfft * np.abs(yf[:nfft//2])
        
        # Find Max Freq
        maxFreq = freqs[np.argmax(yf)]
        
        # Convert Frequency to Color
        rgba = colors(maxFreq/freqs[freqs.size-1])
        
        # Set colors for LED array
        ring4_color = ring3_color
        ring3_color = ring2_color
        ring2_color = ring1_color
        ring1_color = rgba
        setColorChain()
        
        # short pause (use this to control timing for now)
        time.sleep(0.2)
