import sys
sys.path.append('/home/minman/다운로드/DeepMoji-Python3/DeepMoji-master')
sys.path.append('/home/minman/다운로드/DeepMoji-Python3/DeepMoji-master/examples')

import findspark
findspark.init('/home/minman/다운로드/spark-2.4.0-bin-hadoop2.7')
import pyspark

from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()

from pyspark.sql.types import *
from pyspark.sql.functions import *
import re
import requests
import example_helper
import json
import numpy as np
import emoji

emoji_list = [
':joy:',
':unamused:',
':weary:',
':sob:',
':heart_eyes:',
':pensive:',
':ok_hand:',
':blush:',
':heart:',
':smirk:',
':grin:',
':notes:',
':flushed:',
':100:',
':sleeping:',
':relieved:',
':relaxed:',
':raised_hands:',
':two_hearts:',
':expressionless:',
':sweat_smile:',
':pray:',
':confused:',
':kissing_heart:',
':heart:',
':neutral_face:',
':information_desk_person:',
':disappointed:',
':see_no_evil:',
':tired_face:',
':v:',
':sunglasses:',
':rage:',
':thumbsup:',
':disappointed_relieved:',
':sleepy:',
':stuck_out_tongue:',
':triumph:',
':hand:',
':mask:',
':clap:',
':eyes:',
':gun:',
':persevere:',
':smiling_imp:',
':sweat:',
':broken_heart:',
':heartpulse:',
':headphones:',
':speak_no_evil:',
':wink:',
':skull:',
':confounded:',
':smile:',
':stuck_out_tongue_winking_eye:',
':angry:',
':no_good:',
':muscle:',
':facepunch:',
':purple_heart:',
':sparkling_heart:',
':blue_heart:',
':grimacing:',
':sparkles:']


index_to_emoji = dict(zip(range(64), emoji_list))


from deepmoji.sentence_tokenizer import SentenceTokenizer
from deepmoji.model_def import deepmoji_emojis
from deepmoji.global_variables import PRETRAINED_PATH, VOCAB_PATH

maxlen = 30

with open(VOCAB_PATH, 'r') as f:
    vocabulary = json.load(f)

def top_elements(array, k):
    ind = np.argpartition(array, -k)[-k:]
    ind2 = ind[np.argsort(array[ind])][::-1]
    return list(map(lambda e: emoji.emojize(index_to_emoji[e], use_aliases=True), ind2))

TEST_SENTENCES = [u'I love mom\'s cooking']

st = SentenceTokenizer(vocabulary, maxlen)
tokenized, _, _ = st.tokenize_sentences(TEST_SENTENCES)

print('Loading model from {}.'.format(PRETRAINED_PATH))
model = deepmoji_emojis(maxlen, PRETRAINED_PATH)
prob = model.predict(tokenized)
emoji_index = top_elements(prob[0], 1)
print(emoji_index)

class SentenceTokenizer_serializable(object): 
    st = None
    def tokenize_sentences(sentence):
        if not SentenceTokenizer_serializable.st:
            maxlen = 30
            with open(VOCAB_PATH, 'r') as f:
                vocabulary = json.load(f)
            SentenceTokenizer_serializable.st = SentenceTokenizer(vocabulary, maxlen)
        return SentenceTokenizer_serializable.st.tokenize_sentences(sentence)

class Deepmoji_serializable(object):
    model = None
    def predict(tokenized):
        maxlen = 30
        if not Deepmoji_serializable.model:
            Deepmoji_serializable.model = deepmoji_emojis(maxlen, PRETRAINED_PATH)
        return Deepmoji_serializable.model.predict(tokenized)


def sentence_to_emoji_fun(sentence):
    tokenized, _, _ = SentenceTokenizer_serializable.tokenize_sentences([sentence])
    prob = Deepmoji_serializable.predict(tokenized)
    emoji_index = top_elements(prob[0], 1) 
    return emoji_index

from pyspark.sql.types import *
get_emoji = udf(lambda s: sentence_to_emoji_fun(s)[0])

spark.sparkContext.setLogLevel("ERROR")

kafka_df = spark.readStream.format("kafka").option("kafka.bootstrap.servers", "localhost:9092").option("subscribe", "test").load()
kafka_df_string = kafka_df.select(col("key").cast("STRING").alias("key"),col("value").cast("STRING").alias("value"))

kafka_df_string_2 = kafka_df_string.select(col("value"))

def filtering(string):
    temp = string.split(' ')
    filtering_result = ''
    
    for data in temp[1:]:
        if data.isalpha() :
            if data == temp[-1]:
                filtering_result += " " + data
            else :
                filtering_result += data + " "
                
    result = " ".join(re.findall("[a-zA-Z]+", filtering_result))
                
    return result

filteringUDF = udf(filtering, StringType())
kafka_df_string_3 = kafka_df_string_2.withColumn("value", filteringUDF(col("value")))
kafka_df_string_4 = kafka_df_string_3.filter(col("value")!='')
kafka_df_string_5 = kafka_df_string_4.select(get_emoji(col('value')))

result = kafka_df_string_5.groupBy('<lambda>(value)').count().withColumnRenamed('<lambda>(value)', 'emoji').withColumnRenamed('count', 'emoji_count').orderBy(col('count').desc())

output = result.writeStream.outputMode("complete").format("console").option("truncate", "false").trigger(processingTime="5 seconds").start()

def send_df_to_dashboard(df, id):
    emoji_count = [str(t.emoji_count) for t in df.select("emoji_count").take(10)]
    emoji = [str(t.emoji) for t in df.select("emoji").take(10)]
    url = 'http://localhost:8050/update_data'
    request_data = {'emoji_count': str(emoji_count), 'emoji': str(emoji)}
    print('update dashboard')
    response = requests.post(url, data=request_data)

result.writeStream.outputMode("complete").foreachBatch(send_df_to_dashboard).trigger(processingTime="5 seconds").start()

output.awaitTermination()
