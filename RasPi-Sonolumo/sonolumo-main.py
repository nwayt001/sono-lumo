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
        self.maxDetectFreq = 1000.0
        self.minDetectFreq = 300.0
        self.threshold = 200.0

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
        self.detectedFreq = 0.0;
    
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
                if(self.maxFreq<self.minDetectFreq):
                    self.maxFreq = self.minDetectFreq
                    
                colorval = self.maxFreq/self.maxDetectFreq
                colorval = (colorval - self.minDetectFreq/self.maxDetectFreq) / (1- self.minDetectFreq/self.maxDetectFreq)
                
                if(colorval>0.99):
                    colorval=0.99
                    
                if(self.useGBMF):
                    # Convert Frequency to color using gerneralized bellshaped membership function
                    rgba = self.getROYGBIV(colorval)
                else:
                    # Convert Frequency to Color using pyplot colormaps
                    rgba = self.colors(colorval)
                
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

    
