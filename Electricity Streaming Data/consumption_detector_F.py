# ---------------------------------------------- #
########   ENERGY CONSUMPTION DETECTOR   #########
# ---------------------------------------------- #

'''
The script receives data from the consumption_generator.py and analyzes it
'''

### ----------- LIBRARIES ----------- ###
from pyspark import SparkConf,SparkContext
from pyspark.streaming import StreamingContext
from pyspark.sql import Row,SQLContext
import sys
import requests
import time
import datetime

### ----------- FUNCTIONS ----------- ###
# Function to get sql context
def get_sql_context_instance(spark_context):
    if ('sqlContextSingletonInstance' not in globals()):
        globals()['sqlContextSingletonInstance'] = SQLContext(spark_context)
    return globals()['sqlContextSingletonInstance']

'''
The analyze_consumption function takes as input the data sent from the consumption_generator.py 
and analyzes the energy consumption pattern to dectect anomalies. 
In particular: 
- if the consumption is ABOVE the nominal_value of a certain interval (%) for an extended
period of time an alert is raised to notify a possible IP hack or illegal grid attachment. 
- otherwise no alert is raised
All the observations are saved in a log file. 
'''

def analyze_consumption(rdd):

    try:
        ## --- Initial settings: --- ##
        # Get SQL Context
        sql_context = get_sql_context_instance(rdd.context)

        # Map each value to a row
        vals = rdd.map(lambda x: Row(row = x))

        # Create a dataframe whith the mapped rows
        vals_df = sql_context.createDataFrame(vals)

        # extract consumption value and the meter ID
        cons = float(vals_df.collect()[0].row) # customer consumption
        meter_ID = str(vals_df.collect()[1].row) # meter ID

        # Time
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

        # Opening/creating the Log file in append mode
        log = open("consumption_log.txt", "a+")

        # if the consumption is ABOVE the nominal_value of a certain interval (%) -> raise alert
        if cons >= T:

            # Alert counter
            global alert_count
            alert_count += 1

            # Consecutive Alert counter
            global alert_count_cons
            alert_count_cons += 1

            # Observation counter
            global obs
            obs += 1

            # write info to log file
            #log.write(meter_ID + ", " + "1" + ", " + str(st) + ", " + str(obs.value) + ", " + str(alert_count.value) + ", " + str(alert_count_cons.value) + ", " + str(cons) + ", " + str(cons-T) + "\n")
            log.write(meter_ID + ", " + "1" + ", " + str(st) + ", " + str(obs.value) + ", " + str(alert_count.value) + ", " + str(cons) + ", " + str(cons-T) + "\n")
            
            # print status and information
            print('Possible threat: ' + str(alert_count_cons))
            #print("Meter ID: " + meter_ID + " | " + "Status: ALERT" + " | " + str(st) + " | " + "Obs. no.: " + str(obs.value) + " | " + "Alert no.: " + str(alert_count.value) + " | " + "Cons Alert no.: " + str(alert_count_cons.value) + " | " + "Consumption: " + str(cons) + " | " + "Delta: " + str(cons-T) + "\n")     
            print("Meter ID: " + meter_ID + " | " + "Status: ALERT" + " | " + str(st) + " | " + "Obs. no.: " + str(obs.value) + " | " + "Alert no.: " + str(alert_count.value) + " | " + "Consumption: " + str(cons) + " | " + "Delta: " + str(cons-T) + "\n")                   

            # if the number of consecutive alerts is more than n --> FRAUD
            if alert_count_cons >= 3:
                print("-----------------------------------------")
                print("FRAUD DETECTED")
                print("Meter ID: " + meter_ID)
                print("-----------------------------------------")
                print("")
                return()

        else: 

            # observations counter
            global obs
            obs += 1

            # reset consecutive alert counter
            global alert_count_cons
            alert_count_cons = 0

            # write info to log file
            #log.write(meter_ID + ", " + "0" + ", " + str(st) + ", " + str(obs.value) + ", " + str(alert_count.value) + ", " + str(alert_count_cons.value) + ", " + str(cons) + ", " + str(cons-T) + "\n")
            log.write(meter_ID + ", " + "0" + ", " + str(st) + ", " + str(obs.value) + ", " + str(alert_count.value) + ", " + str(cons) + ", " + str(cons-T) + "\n")
            
            # print status and information
            print('All OK')
            #print("Meter ID: " + meter_ID + " | " + "Status: OK" + " | " + str(st) + " | " + "Obs. no.: " + str(obs.value) + " | " + "Alert no.: " + str(alert_count.value) + " | " + "Cons Alert no.: " + str(alert_count_cons.value) + " | " + "Consumption: " + str(cons) + " | " + "Delta: " + str(cons-T) + "\n")
            print("Meter ID: " + meter_ID + " | " + "Status: OK" + " | " + str(st) + " | " + "Obs. no.: " + str(obs.value) + " | " + "Alert no.: " + str(alert_count.value) + " | " + "Consumption: " + str(cons) + " | " + "Delta: " + str(cons-T) + "\n")

        # close log file
        log.close()

    # Dealing with eventual errors
    except:
        e = sys.exc_info()[0]
        print(e)



### ----------- SPARK SETTINGS ----------- ###
# Create spark configuration
conf = SparkConf()
conf.setAppName("GridSecurity")

# Create spark context
sc = SparkContext(conf=conf)
sc.setLogLevel("ERROR")

# Create the Streaming Context from the above spark context with interval size 2 seconds
ssc = StreamingContext(sc, 2)

# Setting a checkpoint to allow RDD recovery
ssc.checkpoint("GS_checkpoint")

### ----------- VARIABLES ----------- ###
alert_count = sc.accumulator(0) # alert counter
alert_count_cons = sc.accumulator(0) # consecutive alert counter
obs = sc.accumulator(0) # observation counter

# Treshold values
nominal_value = 45 # nominal consumption value for the meter
interval = 0.1 # confidence interval for proper consumption
T = nominal_value*(1+interval) # calculate treshold

# assign column names to log file
log = open("consumption_log.txt", "a+")
#log.write("Meter_ID, Status, Timestamp, Obs_N, Alert_N, Cons_Alert_N, Consumption, Delta" + "\n")
log.write("Meter_ID, Status, Timestamp, Obs_N, Alert_N, Consumption, Delta" + "\n")

### ----------- STREAMING ----------- ###
# read data from port
dataStream = ssc.socketTextStream("localhost",2002)

# split data values by commas
values = dataStream.flatMap(lambda line: line.split(','))

# apply function to values
values.foreachRDD(analyze_consumption)

# start
ssc.start()

# finish
ssc.awaitTermination()
