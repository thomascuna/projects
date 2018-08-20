from pyspark import SparkConf,SparkContext
from pyspark.streaming import StreamingContext
from pyspark.sql import Row,SQLContext
import sys
import requests


# create spark configuration
conf = SparkConf()
conf.setAppName("TwitterStreamApp")

# create spark context with the above configuration
sc = SparkContext(conf=conf)
sc.setLogLevel("ERROR")

# create the Streaming Context from the above spark context with interval size 2 seconds
ssc = StreamingContext(sc, 2)

# setting a checkpoint to allow RDD recovery
ssc.checkpoint("checkpoint_TwitterApp")

# read data from port 9090
dataStream = ssc.socketTextStream("localhost",9090)


# split each tweet into words
words = dataStream.flatMap(lambda line: line.split(" "))

# adding the count of each word to its last count
pairs = words.map(lambda word: (word,1))

windowedWordCounts = pairs.reduceByKeyAndWindow(lambda x,y: int(x) + int(y), lambda x,y: int(x) - int(y), 600, 30)
windowedWordCounts.pprint()
#windowedWordCounts.foreachRDD(process_rdd)

# do processing for each RDD generated in each interval
count_word = windowedWordCounts.transform(lambda rdd: rdd.sortBy(lambda x: x[1], False))
count_word.pprint()


# start the streaming computation
ssc.start()

# wait for the streaming to finish
ssc.awaitTermination()
