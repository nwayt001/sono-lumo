from __future__ import print_function

import sys, os
import time
from timeit import default_timer as timer
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

# Example:
# arecord -D hw:1,0 -f S16_LE -r 44100 -t raw | python -u sonolumo-main.py

# Main Class
class SonoLumo(object):
    """
    Main Sonolumo Raspberry Pi Class:
    
    This class sets up an audio stream from a usb microphone, 
    calculates a frequency spectrum and encodes maximum frequency 
    to color for pwm controlled LED strips
    """
    def __init__(self,use_sim):
        # Attributes for USB mic & Signal Processing
        self.use_sim = use_sim
        self.is_raspi = (os.uname())[1] == 'raspberrypi'
        self.inputformat = 'non-raw' # get input from stdin (e.g. arecord)
        self.USB_Name = 'hw:1,0' #change name to final USB mic
        self.SamplingRate = 44100
        self.Channels = 1
        self.chunk = 2000
        self.nfft = self.chunk
        self.maxDetectFreq = 2000.0
        self.minDetectFreq = 300.0
        self.maxThreshold = 2000.0
        self.minThreshold = 200.0
        self.starttime = 0.0
        self.endtime = 0.0
        self.debug = False
        
        self.sineIndex = 0
        self.radianArray = np.array([0, np.pi/6, np.pi/4, np.pi/3, np.pi/2, 2*np.pi/3, 3*np.pi/4, 5*np.pi/6])
        self.sineArray = np.sin(self.radianArray)
        
        # Scaling Type
        self.scaleType = 'mel'  # 'mel' or 'linear'
        
        # mel scale range
        self.melMAX =  2410.0*np.log10(1.0+(self.maxDetectFreq/625.0))
        self.melMIN =  2410.0*np.log10(1.0+(self.minDetectFreq/625.0))
  
        #intensity log scale range
        self.maxLogThresh = 10*np.log10(self.maxThreshold)
        self.minLogThresh = 10*np.log10(self.minThreshold)
        
        if(self.inputformat!='raw'):
            # Open the device in nonblocking capture mode.
            self.inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, self.USB_Name)

            # Set attributes for recording:
            self.inp.setchannels(self.Channels)
            self.SamplingRate = self.inp.setrate(self.SamplingRate)
            self.inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
            self.inp.setperiodsize(self.chunk)
        
        self.freqs = np.linspace(0.0, self.SamplingRate/2.0, self.nfft/2.0)
        self.freqmask = (self.freqs>self.minDetectFreq) & (self.freqs<self.maxDetectFreq)
        print(self.freqmask)
        #self.time_resol = (self.nfft*(1.0) / self.SamplingRate*(1.0)) *1000.0
        self.windowF = np.hamming(self.nfft)
        self.cmap = 'rainbow'
        self.colors = plt.get_cmap(self.cmap)
        self.detectedFreq = 0.0;
        self.detectedIntensity = 1000
        
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
        
        self.ring1_numtics = self.num_tics
        self.ring2_numtics = self.num_tics
        self.ring3_numtics = self.num_tics
        self.ring4_numtics = self.num_tics
        
        # parameters for tuning rgb generalized bellshaped membership functions
        self.useGBMF = True
        self.blue_a=3.0
        self.blue_b=3.0
        self.blue_c=9.0
        self.green_a=3.0
        self.green_b=3.0
        self.green_c=5.0
        self.red_a=3.0
        self.red_b=-3.0
        self.red_c=7.0
        
        # If we're not using raspi, or we want to run simulator
        if(not self.is_raspi or self.use_sim):
            self.initialize_Simulator()
            
        # Initialize the RasPi Hat (for Raspi only)
        if(self.is_raspi):
            self.pwm = PWM(0x40)
            self.pwm.setPWMFreq(500) # set to half of max frequency
            # may need to lower the frequency to get lower amplitude levels
        
        
    def __del__(self):
        try:
            print('closing...')
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
            self.pwm.setPWM(self.Ch_r1,0, (self.ring1_color[0]*self.ring1_numtics*self.num_tics).astype(int))
            self.pwm.setPWM(self.Ch_g1,0, (self.ring1_color[1]*self.ring1_numtics*self.num_tics).astype(int))
            self.pwm.setPWM(self.Ch_b1,0, (self.ring1_color[2]*self.ring1_numtics*self.num_tics).astype(int))
            
            self.pwm.setPWM(self.Ch_r2,0, (self.ring2_color[0]*self.ring2_numtics*self.num_tics).astype(int))
            self.pwm.setPWM(self.Ch_g2,0, (self.ring2_color[1]*self.ring2_numtics*self.num_tics).astype(int))
            self.pwm.setPWM(self.Ch_b2,0, (self.ring2_color[2]*self.ring2_numtics*self.num_tics).astype(int))
            
            self.pwm.setPWM(self.Ch_r3,0, (self.ring3_color[0]*self.ring3_numtics*self.num_tics).astype(int))
            self.pwm.setPWM(self.Ch_g3,0, (self.ring3_color[1]*self.ring3_numtics*self.num_tics).astype(int))
            self.pwm.setPWM(self.Ch_b3,0, (self.ring3_color[2]*self.ring3_numtics*self.num_tics).astype(int))
            
            self.pwm.setPWM(self.Ch_r4,0, (self.ring4_color[0]*self.ring4_numtics*self.num_tics).astype(int))
            self.pwm.setPWM(self.Ch_g4,0, (self.ring4_color[1]*self.ring4_numtics*self.num_tics).astype(int))
            self.pwm.setPWM(self.Ch_b4,0, (self.ring4_color[2]*self.ring4_numtics*self.num_tics).astype(int))
            
        else: #use simulated flower (for testing and debugging)
            self.ax.add_artist(plt.Circle((0.5, 0.5), self.ring4_sim, color=self.ring4_color))
            self.ax.add_artist(plt.Circle((0.5, 0.5), self.ring3_sim, color=self.ring3_color))
            self.ax.add_artist(plt.Circle((0.5, 0.5), self.ring2_sim, color=self.ring2_color))
            self.ax.add_artist(plt.Circle((0.5, 0.5), self.ring1_sim, color=self.ring1_color))
            self.ax.add_artist(plt.Circle((0.5, 0.5), self.ring0_sim, color='black'))
    #        plt.pause(0.01)
    
    def getROYGBIV(self,x):
        # convert 0-1 value to 0-12 (because the GBMF constants are based on that scale)
        x = x*12
        r_val = 1/(1+np.power(np.abs((x-self.red_c)/self.red_a),2*self.red_b))
        g_val = 1/(1+np.power(np.abs((x-self.green_c)/self.green_a),2*self.green_b))
        b_val = 1/(1+np.power(np.abs((x-self.blue_c)/self.blue_a),2*self.blue_b))
        
        lst = list()
        lst.append(np.float64(r_val))
        lst.append(np.float64(g_val))
        lst.append(np.float64(b_val))
        lst.append(np.float64(1.0))
        rgba = tuple(lst)
        
        return rgba
        
        
    def run(self):

        print(self.freqs)

        # read from device
        yf_prev = 0.0
        alpha = 0.25 #moving average
        while 1:
            if self.debug:
                self.starttime = timer()
                print()
            if(self.inputformat=='raw'):
                l=4000
                data = sys.stdin.read(l)
            else:
                l, data = self.inp.read()
            
            if l>0:
                fmt = "%dH"%(len(data)/2)
                data2 = struct.unpack(fmt, data)
                data2 = np.array(data2, dtype='h')
                data2 = self.windowF*data2        
                # Apply FFT
                yf = np.fft.rfft(data2)
                yf = 2.0/self.nfft * np.abs(yf[:self.nfft//2])
                
                # moving average
                yf = ((1.0-alpha) * yf_prev) +  (alpha * yf)
                yf_prev = yf
                
                # Find Max Freq
                self.detectedFreq = self.freqs[np.argmax(yf*self.freqmask)]
                                            
                if(self.detectedFreq>self.maxDetectFreq):
                    self.detectedFreq=self.maxDetectFreq
                if(self.detectedFreq<self.minDetectFreq):
                    self.detectedFreq=self.minDetectFreq
                                    
                # Convert frequency to mel scale
                if(self.scaleType == 'mel'):
                    mel = 2410.0*np.log10(1.0+(self.detectedFreq/625.0))                            
                    colorval = (((mel-self.melMIN)*(1.0-0.0))/(self.melMAX-self.melMIN)) 
                # or Convert frequency to linear scale                    
                elif(self.scaleType =='linear'):
                    colorval = (((self.detectedFreq - self.minDetectFreq) * (1.0-0.0)) / (self.maxDetectFreq - self.minDetectFreq))
                
                if self.debug:
                    print("Colorval %0.2f" % colorval)
                
                # Bound between 0.001 and 0.99 - this was found to work better than 0-1
                if(colorval>0.99):
                    colorval=0.99
                if(colorval<0.001):
                    colorval=0.001
                    
                # light amplitude modulation based on sound amplitude
                #self.detectedIntensity = yf[np.argmax(yf*self.freqmask)]
                # Convert intensity to log scale
                #intensityDB = 10*np.log10(self.detectedIntensity)
                #numticsval = (intensityDB - self.minLogThresh) / (2*(self.maxLogThresh - self.minLogThresh)) + 0.5
                numticsval=1.0                
    
                # Bound between 0.5 and 1    
                if(numticsval > 1.0):
                    numticsval = 1.0
                if(numticsval < 0.5):
                    numticsval = 0.5

                # Convert frequency to color
                if(self.useGBMF):
                    # Convert Frequency to color using gerneralized bellshaped membership function
                    rgba = self.getROYGBIV(colorval)
                else:
                    # Convert Frequency to Color using pyplot colormaps
                    rgba = self.colors(colorval)
                
                # Set to white if power is below threshold
                if(np.max(yf*self.freqmask)<self.minThreshold):
                    lst = list(rgba)
                    lst[0] = np.float64(0.99)
                    lst[1] = np.float64(0.99)
                    lst[2] = np.float64(0.99)
                    lst[3] = np.float64(1.0)
                    rgba = tuple(lst)                    
                else:
                    if self.debug:
                        print(np.array_str(yf[1:np.argmax(yf*self.freqmask)], precision=2, suppress_small=True))
                
                # Set/propogate colors for LED array
                self.ring4_color = self.ring3_color
                self.ring3_color = self.ring2_color
                self.ring2_color = self.ring1_color
                self.ring1_color = rgba
                                
                # Set intensities for LED array
                self.ring4_numtics = self.ring3_numtics
                self.ring3_numtics = self.ring2_numtics
                self.ring2_numtics = self.ring1_numtics
                self.ring1_numtics = numticsval

                self.setLEDcolors() # update pwm color values for LED strips
                
                if self.debug:
                    print("Numticsval %0.2f" % numticsval)
                    print("%0.2f" % self.detectedFreq + ' Hz' + ", freqbinpower=%0.2f" % np.max(yf) + ", totalpower=%0.2f" % np.sum(yf) + ", arraynum=%d" % np.argmax(yf*self.freqmask)) #show detected frequency for debugging        
                    self.endtime = timer()
                    print("Processing took %0.3f s" % (self.endtime-self.starttime))

                # short pause (use this to control timing for the color propogation...for now)
                time.sleep(0.2)

if __name__ == '__main__':
    # use_sim = False # True -> run simulator, False -> run Flower LED's
    sonolumo = SonoLumo(use_sim)
    sonolumo.run()

    
