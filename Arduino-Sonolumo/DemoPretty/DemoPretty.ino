#include <Adafruit_NeoPixel.h>
//define length of transform window
#define FHT_N 256 
//set linear output on, other option is LOG_OUT 1
#define LIN_OUT 1
//includ FHT library. Must come after above definitions
#include <FHT.h>


//microphone being read into A0
int MicSensorIn = 0 ; 
//number of repeated samples to take
int numsamps = 8;
//microsecond delay to create desired sampling frequency
int samprate = 500;
int prevcolor = 0;

//take the samples to average together, both the bin and value, with size numsamps
int frequencies[8];
int frequenciesval[8];

#define PIN1 10
#define PIN2 11

Adafruit_NeoPixel strip1 = Adafruit_NeoPixel(28, PIN1, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel strip2 = Adafruit_NeoPixel(47, PIN2, NEO_GRB + NEO_KHZ800);

void setup() 
{
//Set mic input 
pinMode(MicSensorIn, INPUT);
//Stream data at baud rate of 115200
Serial.begin(115200);
strip1.begin();
strip1.show();
strip2.begin();
strip2.show();
}

void loop() 
{

//initialize the frequency variables to 0 each time
memcpy(frequencies, 0, numsamps);
memcpy(frequenciesval, 0, numsamps);
int avgfreq = 0;
int totfreq = 0; 
int avgfreqval = 0;
int totfreqval = 0; 

//take multiple samples of 256 point FHTs
for (int b=0; b< numsamps; b=b+1)
{
for (int x=0; x < FHT_N; x=x+1)
{
//fht_input is defined by the FHT library and is the length of FHT_N
fht_input[x] = analogRead(MicSensorIn);
//250 microseconds is approximately 4000hz (not including clock cycles for analogread, etc)
delayMicroseconds(samprate);
}

//the following compute the FHT, the window command is possibly unneeded
//fht_window();
fht_reorder();
fht_run();
fht_mag_lin();

//send the output, the nyquist freq to determine the frequency bin with the largest value
maxFreq(fht_lin_out, FHT_N/2, frequencies, b, frequenciesval);

}

// add and average the samples
for(int i=0; i<numsamps; i++)
{
totfreqval = frequenciesval[i] + totfreqval;
totfreq = frequencies[i]+totfreq; 
}
avgfreq = totfreq / numsamps;
avgfreqval = totfreqval / numsamps;

//print the average and delay 
Serial.println(avgfreq);
Serial.println(avgfreqval);
//if reading is above noise floor, create a color based on frequency
//
if (prevcolor ==0)
{
    for(int r=1; r<48; r++)
  {
strip2.setPixelColor(r, strip2.Color(150, 150,150 ));
  }
}

if (prevcolor ==1)
{
    for(int r=1; r<48; r++)
  {
strip2.setPixelColor(r, strip2.Color(0, 0,255 ));
  }
}

  if (prevcolor ==2)
{
    for(int r=1; r<48; r++)
  {
strip2.setPixelColor(r, strip2.Color(0, 204,204));
  }
}

    if (prevcolor ==3)
{
    for(int r=1; r<48; r++)
  {
strip2.setPixelColor(r, strip2.Color(102, 0,204 ));
  }

}
  

if (avgfreqval > 5)
{
//blue for lowest frequency
if (avgfreq< 30)
{
  for(int r=1; r<29; r++)
  {
strip1.setPixelColor(r, strip1.Color(0, 0,255 ));
  }
  prevcolor = 1;
  
Serial.println("red");
}


//aqua for middle band
if (avgfreq >= 30 && avgfreq < 60)
{
  for(int r=1; r<29; r++)
  {
strip1.setPixelColor(r, strip1.Color(0,204,204));
  }

  prevcolor = 2;
    
Serial.println("green");
}


//Blue for highest frequency
if (avgfreq >= 60)
{
  for(int r=1; r<29; r++)
  {
strip1.setPixelColor(r, strip1.Color(102,0,204));
  }

  prevcolor = 3;
    
Serial.println("blue");
   
}
}

//Otherwise be white
else
{
  for(int r=1; r<29; r++)
  {
strip1.setPixelColor(r, strip1.Color(150,150,150));
  }

  prevcolor = 0;
  
}



strip1.show();
strip2.show();
//delay(1000);

}


//function finds the index of the largest frequency magnitude. The first two
//seem to be dominated by DC component and are excluded
int maxFreq(uint16_t fhtout[], int n, int frequencies[], int b, int frequenciesval[])
{
int h = 3;

//Serial.println(b);
for (int z = 4; z<n; z++)
{
  if (fhtout[z] > fhtout[h])
 {
 h = z;
 }

}
frequenciesval[b] = fhtout[h];
frequencies[b] = h; 
}

