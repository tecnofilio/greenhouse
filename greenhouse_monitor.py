import plotly.plotly as py
import json
import psutil

import serial
import re
import datetime

from gpiozero import LED

#from subprocess import call
#from os import system as sys
import pygame.camera
import pygame.image

pygame.camera.init()
cam = pygame.camera.Camera(pygame.camera.list_cameras()[0])
cam.start()

def capture():
    dt=datetime.datetime.now()
    #dtime = dt[0:4]+dt[5:7]+dt[8:10]+dt[11:13]+dt[14:16]+dt[17:19]
    dtime = str(dt)[0:10]+'_'+str(dt)[11:19]
    #pygame.camera.init()
    #cam = pygame.camera.Camera(pygame.camera.list_cameras()[0])
    #cam.start()
    img = cam.get_image()
    pygame.image.save(img, dtime + '.jpg')
    #pygame.camera.quit()
    print('---Image saved '+ dtime + ' ---')
    #call(["fswebcam", "-d","/dev/video0", "-r", "640x480", "--no-banner", "./%s.jpeg" % dtime])
    #sys("fswebcam " + dtime + ".jpg")


#import matplotlib.pyplot as plt

#set up GPIO for night light
led = LED(26)
led.off()


#Create plotly scatter graph
with open('./config.json') as config_file:
    plotly_user_config = json.load(config_file)

    py.sign_in(plotly_user_config["plotly_username"], plotly_user_config["plotly_api_key"])

url = py.plot([
    {
        'x': [], 'y': [], 'type': 'scatter',
        'stream': {
            'token': plotly_user_config['plotly_streaming_tokens'][0],
            'maxpoints': 20000
        }
    }], filename='Basil greenhouse streaming values')

stream = py.Stream(plotly_user_config['plotly_streaming_tokens'][0])
stream.open()




# Open serial port
try:
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout = 1)
except:
    print("Could not open USB port")
mstart = datetime.datetime.now()
temp_s1_vector = []
temp_s2_vector = []
light_vector = []
time_vector = []
logfilename = 'log_' + str(datetime.datetime.now())[0:16] + '.txt'
prog=0
light=0

def update_progress(progress):
    print('\r[{0}] {1}%'.format('#'*int((progress/10)), progress))

    
# Continously read USB port where Arduino is connected 
try:
    while True:
        x = ser.readline()
        
        #------------------
        #Set night lighting
        now=datetime.datetime.now()
        if (now.hour>=0)and(now.hour<16)and(light>400):                     
            led.off()
            #print('light off')
        else:
            led.on()
            #print('light on')
        #-----------------
        
		#match = re.search(r': \d+ \| ', x)
        #match = re.search(r'( \d+)\.?(\d+)',x)
        #if match is not None:
        if len(re.findall(r'(\d+)\.?(\d+)',str(x)))>0:
            print("")
            print(str(datetime.datetime.now())) #print ('found', match.group())
            #print('found ', str(x))
            numbers = re.findall(r'(\d+)\.?(\d+)',str(x))
            #print(numbers)
            states = re.findall(r' \d ', str(x))
            temp_s1 = float(numbers[0][0] + '.' + numbers[0][1])
            temp_s2 = float(numbers[1][0] + '.' + numbers[1][1])
            light = float((numbers[-1][0] + '.' + numbers[-1][1]))
            print('T1: ', temp_s1, ' T2: ', temp_s2, 'light: ', light)
            temp_s1_vector.append(temp_s1)
            temp_s2_vector.append(temp_s2)
            light_vector.append(light)
            time_vector.append(datetime.datetime.now())
            
            prog=0
            print(psutil.virtual_memory())
            print('LED lighting: ', led.is_active)
            print('')
            #plt.plot(time_vector[-300:-1], temp_s2_vector[-300:-1], hold = False)
            #plt.ion()
            #plt.grid(True)
            #plt.show()
            #plt.pause(0.0001)
            try:
                stream.write({'x': time_vector[-1], 'y': temp_s2_vector[-1]})
            except Exception as e:
                ser.close()
                stream.close()
                print("plotly stream error!!!")
                f = open(logfilename,'w')
                for i in range(len(temp_s2_vector)):
                    f.write(str(time_vector[i]) + ' '+str(temp_s2_vector[i]) + '\n')
                    f.close()
            capture()



        else:
            #print('.', end=" ")
            prog+=100/45
            #update_progress(prog)

except KeyboardInterrupt:
    
    pygame.camera.quit()
    ser.close()
    mend = datetime.datetime.now()
    print("Good bye!!!")
    #f = open('logfile_'+str(mstart.year)+str(mstart.month)+str(mstart.day)+str(mstart.hour)+str(mstart.minute)+'_'+str(mend.year)+str(mend.month)+str(mend.day)+str(mend.hour)+str(mend.minute) +'.txt','w')
    f = open('logfile_'+str(mstart)+'_'+str(mend)+'.txt','w')
    for i in range(len(temp_s2_vector)):
        f.write(str(time_vector[i]) + ' '+str(temp_s1_vector[i]) +' '+str(temp_s2_vector[i]) + ' '+str(light_vector[i]) + '\n')
    f.close()
