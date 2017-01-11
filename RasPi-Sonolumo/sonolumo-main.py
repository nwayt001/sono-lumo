from __future__ import print_function

import sys, os
import time
import alsaaudio
import struct
import numpy as np
import numpy as numpy
import matplotlib.pyplot as plt
if (os.uname())[1] == 'raspberrypi':
    from Adafruit_PWM_Servo_Driver import PWM
    use_sim = False
else:
    use_sim = True


# Main Class
class SonoLumo(object):
    """
    Main Sonnolumo Raspberry Pi Class:
    
    This class sets up an audio stream from a usb microphone, 
    calculates a frequency spectrum and encodes maximum frequency 
    to color for pwm controlled LED strips
    """
    def __init__(self,use_sim):
        # Attributes for USB mic & Signal Processing
        self.use_sim = use_sim
        self.is_raspi = (os.uname())[1] == 'raspberrypi'
        self.USB_Name = 'hw:CARD=Device' #change name to final USB mic
        self.SamplingRate = 16000
        self.Channels = 1
        self.chunk = 2000
        self.nfft = self.chunk
        self.maxDetectFreq = 4000
	self.threshold = 900.0
        # Open the device in nonblocking capture mode.
        self.inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, self.USB_Name)

        # Set attributes for recording:
        self.inp.setchannels(self.Channels)
        self.SamplingRate = self.inp.setrate(self.SamplingRate)
        self.inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self.inp.setperiodsize(self.chunk)
        
        self.freqs = np.linspace(0.0,1.0/(2.0*(1.0/self.SamplingRate)),self.nfft/2.0)
        self.time_resol = (self.nfft*(1.0) / self.SamplingRate*(1.0)) *1000.0
        self.windowF = np.hamming(self.nfft)
        self.cmap = 'rainbow'
        self.colors = plt.get_cmap(self.cmap)
        self.maxFreq = 0.0;
    
        # Attributes for RasPi Hat
        self.Ch_r1 = 0
        self.Ch_g1 = 1
        self.Ch_b1 = 2
        self.Ch_r2 = 4
        self.Ch_g2 = 5
        self.Ch_b2 = 6
        self.Ch_r3 = 8
        self.Ch_g3 = 9
        self.Ch_b3 = 10
        self.Ch_r4 = 12
        self.Ch_g4 = 13
        self.Ch_b4 = 14
        self.pulse_width = 0.5
        self.num_tics = 4096.0
        
        self.ring1_color=self.colors(0)
        self.ring2_color=self.colors(0)
        self.ring3_color=self.colors(0)
        self.ring4_color=self.colors(0)
    
        # If we're not using raspi, or we want to run simulator
        if(not self.is_raspi or self.use_sim):
            self.initialize_Simulator()
            
        # Initialize the RasPi Hat (for Raspi only)
        if(self.is_raspi):
            self.pwm = PWM(0x40)
            self.pwm.setPWMFreq(1000) # set to max frequency
        
        
        
    def __del__(self):
        try:
            self.inp.close()
        except ValueError:
            print('error when closing audio stream')

    def initialize_Simulator(self):
        self.cax = plt.imshow(np.random.rand(50,50),cmap=self.cmap) #<-to get a colorbar
        self.fig, (self.ax) = plt.subplots()
        
        self.ring0_sim = 0.03 # ring radius for the simulated flower
        self.ring1_sim = 0.1
        self.ring2_sim = 0.2
        self.ring3_sim = 0.3
        self.ring4_sim = 0.4

        self.ax.add_artist(plt.Circle((0.5, 0.5), self.ring4_sim, color='black'))
        self.ax.add_artist(plt.Circle((0.5, 0.5), self.ring3_sim, color='gray'))
        self.ax.add_artist(plt.Circle((0.5, 0.5), self.ring2_sim, color='black'))
        self.ax.add_artist(plt.Circle((0.5, 0.5), self.ring1_sim, color='gray'))
        self.ax.add_artist(plt.Circle((0.5, 0.5), self.ring0_sim, color='black'))
        
        self.cbar = self.fig.colorbar(self.cax, ticks=[-1, 0, 1])
        
    def setLEDcolors(self):
        if(self.is_raspi and not self.use_sim): #use real flower
            self.pwm.setPWM(self.Ch_r1,0, (self.ring1_color[0]*self.num_tics).astype(int))
            self.pwm.setPWM(self.Ch_g1,0, (self.ring1_color[1]*self.num_tics).astype(int))
            self.pwm.setPWM(self.Ch_b1,0, (self.ring1_color[2]*self.num_tics).astype(int))
            
            self.pwm.setPWM(self.Ch_r2,0, (self.ring2_color[0]*self.num_tics).astype(int))
            self.pwm.setPWM(self.Ch_g2,0, (self.ring2_color[1]*self.num_tics).astype(int))
            self.pwm.setPWM(self.Ch_b2,0, (self.ring2_color[2]*self.num_tics).astype(int))
            
            self.pwm.setPWM(self.Ch_r3,0, (self.ring3_color[0]*self.num_tics).astype(int))
            self.pwm.setPWM(self.Ch_g3,0, (self.ring3_color[1]*self.num_tics).astype(int))
            self.pwm.setPWM(self.Ch_b3,0, (self.ring3_color[2]*self.num_tics).astype(int))
            
            self.pwm.setPWM(self.Ch_r4,0, (self.ring4_color[0]*self.num_tics).astype(int))
            self.pwm.setPWM(self.Ch_g4,0, (self.ring4_color[1]*self.num_tics).astype(int))
            self.pwm.setPWM(self.Ch_b4,0, (self.ring4_color[2]*self.num_tics).astype(int))
			
        else: #use simulated flower (for testing and debugging)
            self.ax.add_artist(plt.Circle((0.5, 0.5), self.ring4_sim, color=self.ring4_color))
            self.ax.add_artist(plt.Circle((0.5, 0.5), self.ring3_sim, color=self.ring3_color))
            self.ax.add_artist(plt.Circle((0.5, 0.5), self.ring2_sim, color=self.ring2_color))
            self.ax.add_artist(plt.Circle((0.5, 0.5), self.ring1_sim, color=self.ring1_color))
            self.ax.add_artist(plt.Circle((0.5, 0.5), self.ring0_sim, color='black'))
            plt.pause(0.1)
            print("%0.2f" % self.maxFreq + ' Hz') #show detected frequency for debugging
            
    def run(self):
        # read from device
        while 1:
            l, data = self.inp.read()
            
            if l>0:
                fmt = "%dH"%(len(data)/2)
                data2 = struct.unpack(fmt, data)
                data2 = np.array(data2, dtype='h')
                data2 = self.windowF*data2        
                # Apply FFT
                yf = np.fft.rfft(data2)
                yf = 2.0/self.nfft * np.abs(yf[:self.nfft//2])

                # Find Max Freq
                self.maxFreq = self.freqs[np.argmax(yf)]
                
                # Convert Frequency to Color
                rgba = self.colors(self.maxFreq/self.maxDetectFreq)
                
                if(np.max(yf)<self.threshold):
                    lst = list(rgba)
                    lst[0] = np.float64(0.99)
                    lst[1] = np.float64(0.99)
                    lst[2] = np.float64(0.99)
                    lst[3] = np.float64(1.0)
                    rgba = tuple(lst)
                
                # Set colors for LED array
                self.ring4_color = self.ring3_color
                self.ring3_color = self.ring2_color
                self.ring2_color = self.ring1_color
                self.ring1_color = rgba
                                
                self.setLEDcolors() # update pwm color values for LED strips
        
                # short pause (use this to control timing for the color propogation...for now)
                time.sleep(0.2)

if __name__ == '__main__':
    # use_sim = False # True -> run simulator, False -> run Flower LED's
    sonolumo = SonoLumo(use_sim)
    sonolumo.run()

    
