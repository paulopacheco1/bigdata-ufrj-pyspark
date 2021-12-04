from pyspark import SparkContext, SparkConf
import time

time.sleep(10)

sc = SparkContext('local[*]')

# conf = SparkConf()
# conf.setMaster('spark://spark:7077')
# sc = SparkContext(conf=conf)

rdd = sc.parallelize(range(1000))

f = open("out.txt", "w")
f.write('\n'.join(str(e) for e in rdd.takeSample(False, 50)))
f.close()

while True:
  pass