# ---------------------------------------------- #
########   ENERGY CONSUMPTION GENERATOR   ########
# ---------------------------------------------- #

'''
The script generates random consumption value for a specific customer - intended
as a household or a business.
The values are in KWh form and are generated every second.
'''

### LIBRARIES ###
import socket
import sys
import requests
import requests_oauthlib
#import json
import random
import time
import datetime
import numpy as np

### GENERATOR ###
'''
The function generates random normal values around a centre and a sd to simulate 
a typical household consumption
'''

def consumption_generator(tcp_connection):
    while True:
        try:
            # generate random customer consumption
            # based on normal distribution ~ N(centre, sd)
            consumption = round(np.random.normal(centre,sd),2)

            # string with generated value
            #customer_consumption = str(consumption) + ' KWh'
            customer_consumption = str(consumption)

            # print generated value and timestamp on screen
            # retrieve timestamp
            ts = time.time()
            st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            print("---------- " + st + " ----------") # print timestamp
            print("Meter ID: " + meter_ID) # print meter_ID
            print("Live consumption: " + customer_consumption + ' KWh') # print customer_consumption
            print("-----------------------------------------") # print separator
            print("")

            # send string to TCP
            tcp_connection.send(customer_consumption + "," + meter_ID + '\n')

            # generate value every second
            time.sleep(2)

        # Dealing with eventual errors
        except:
            e = sys.exc_info()[0]
            print("Error: %s" % e)


### VARIABLES ###
# user input to generate values
centre = int(raw_input("Centre: "))
sd = int(raw_input("Sd: "))

meter_ID = "SM_239067"

# pre-defined values
# centre = 45 # mean of the distribution
# sd = 5 # standard deviation


### CONNECTION ###
# TCP IP and port:
TCP_IP = "localhost"
TCP_PORT = 2002

# connection:
conn = None

# socket:
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

# wait for connection
print("Waiting for TCP connection...")

# accept connection
conn, addr = s.accept()

# print confirmation
print("Connected... Start generating values...")

# generate consumption values
consumption_generator(conn)
