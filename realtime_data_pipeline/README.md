[구현목표 아키텍처]


![image](https://user-images.githubusercontent.com/41605276/92443972-352e6e80-f1ed-11ea-91cd-f882c4baa80e.png)

- 로컬 피시의 cpu/memory 메트릭을 실시간으로 csv 파일로 저장해서 매 1분마다 s3로 업로드하면 위와 같은 파이프라인을 거쳐 ES에 적재되 kibana로 시각화까지하는 아키텍처


- S3에 업로드 된 csv 파일을 소스로 사용하여 fluentd가 SQS의 이벤트 트리거(s3에 csv파일이 업로드 되었다는)를 받아서 kinesis에 데이터를 json 포맷으로 전송


- kinesis streams에 들어온 데이터를 lambda가 받아서 ES에 적재 후 시각화

#### STEP 0. 사전작업

위와 같은 데이터 파이프라인 구현을 위해 필요한 AWS 인프라에 대해서 미리 콘솔에서 Set up 해야 합니다.

(network 인프라, s3, sqs, ec2, kinesis, lambda, es, 보안그룹 설정, iam role 등)


#### STEP 1. LocalPC to S3 실시간 데이터 전송 파이프라인 구축

- local PC의 cpu/memory 메트릭을 수집하는 파이썬 코드

메트릭을 수집해서 실시간으로(1초마다) 저장하고, 매분마다 s3 버킷에 csv형태의 파일로 업로드 시킴


```python
import time
import threading
import pandas as pd
import psutil
import datetime
import boto3
import os

def get_computer_metric():
    """
    get cpu/memory metric with dictionary
    """
    computer_stat = dict(psutil.cpu_stats()._asdict())
    computer_stat['timestamp_for_kibana'] = (datetime.datetime.now() - datetime.timedelta(hours=9)).strftime('%Y-%m-%dT%H:%M:%SZ')
    computer_stat['timestamp'] = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    computer_stat['cpu_usage_percent'] = psutil.cpu_percent()
    computer_stat['cpu_ctx_switches'] = computer_stat.pop('ctx_switches')
    computer_stat['cpu_interrupts'] = computer_stat.pop('interrupts')
    computer_stat['cpu_soft_interrupts'] = computer_stat.pop('soft_interrupts')
    computer_stat['cpu_syscalls'] = computer_stat.pop('syscalls')


    mem_stat = dict(psutil.virtual_memory()._asdict())
    mem_stat['mem_total'] = mem_stat.pop('total')
    mem_stat['mem_available'] = mem_stat.pop('available')
    mem_stat['mem_percent'] = mem_stat.pop('percent')
    mem_stat['mem_used'] = mem_stat.pop('used')
    mem_stat['mem_free'] = mem_stat.pop('free')

    computer_stat.update(mem_stat)
    
    return computer_stat


computer_stat = get_computer_metric()
df = pd.DataFrame([computer_stat], columns=computer_stat.keys())

time.sleep(1)

starttime=time.time()
count = 1
while True:
    df = df.append(get_computer_metric(), ignore_index=True)
    time.sleep(1)
    
    if count == 60:
        # write csv to local
        filename = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        df.to_csv("{}.csv".format(filename), mode='w', index=False,header=None)
        
        # csv file in local to s3
        s3 = boto3.resource(service_name='s3')
        data = open(filename+'.csv', 'rb')
        s3.Bucket('[bucketname]').put_object(Key='realtime_architecture/'+filename+'.csv',Body=data)
        data.close()
        
        # delete local csv file
        os.remove("{}.csv".format(filename))
        
        print(filename+".csv file upload finish")
        
        # pandas dataframe reset
        df = pd.DataFrame(columns=computer_stat.keys())
        
        count-=60
        
    count+=1
```

#### STEP 2. AWS SQS 생성

AWS SQS 역할 : 특정 S3 경로에 데이터가 업로드 되면 Fluentd에게 event notification

따라서 특정 s3 버킷경로에 .csv 파일이 업로드 되면  " s3:ObjectCreated:* " event가 발동하도록 설정해줘야 한다.


#### STEP 3. EC2에서 Fluentd agent 설정

- fluentd 서버에서 fluentd config 설정

fluentd 설치시 fluentd 기본 plugin list에 S3만 있으므로 kinesis plugin 설치필요

input plugin : s3, output plugin : kinesis

S3에 객체 생성이되면 sqs를 통해 td-agent가 S3로부터 객체 획득, kinesis data stream으로 전송

[주의사항]

fluentd td-agent가 행 단위로 data를 인식하기 때문에 csv 파일에 header나 index가 있을경우 data로 인식( header skip 불가)

제공되는 csv 파일의 data를 정확히 인식하고 있어야 변환하는 json의 key value를 매칭 시킬수 있음

fluentd td-agent config 파일에 credential을 작성

csv header skip 기능 없음(s3 plugin)

- ec2에 fluentd 설치 및 configuration

(참고자료 : https://github.com/awslabs/aws-fluent-plugin-kinesis, https://github.com/fluent/fluent-plugin-s3)


```python
# yum update
[ec2-user@ip-10-88-0-200 etc]$  sudo yum update -y

# td-agent v4 설치
[ec2-user@ip-10-88-0-200 etc]$  curl -L https://toolbelt.treasuredata.com/sh/install-amazon2-td-agent4.sh | sh

# kinesis plugin 설치
[ec2-user@ip-10-88-0-200 etc]$  sudo td-agent-gem install fluent-plugin-kinesis

# td-agent config file 수정
[ec2-user@ip-10-88-0-200 etc]$ sudo vim /etc/td-agent/td-agent.conf
  <source>
    @type s3
    s3_bucket [bucketname]
    s3_region ap-northeast-2
    add_object_metadata false
    store_as "json"
    tag stream_data
    aws_key_id xxxxxxxxxxxxxxxxxxxxxxx
    aws_sec_key xxxxxxxxxxxxxxxxxxxxxxx
    <parse>
      @type csv
      keys timestamp_for_kibana, timestamp, cpu_usage_percent, cpu_ctx_switches, cpu_interrupts, cpu_soft_interrupts, cpu_syscalls, mem_total, mem_available, mem_percent, mem_used, mem_free
    </parse>
    <sqs>
      queue_name [SQSname]
    </sqs>
  </source>
  <match stream_data>
    @type kinesis_streams
    region ap-northeast-2
    stream_name [kinesisname]
    aws_key_id xxxxxxxxxxxxxxxxxxxxxxx
    aws_sec_key xxxxxxxxxxxxxxxxxxxxxxx
    <format>
      @type "json"
    </format>
  </match>


# td-agent 시작
[ec2-user@ip-10-88-0-200 etc]$ sudo systemctl start td-agent.service

# td-agent 상태 정보
[ec2-user@ip-10-88-0-200 etc]$ sudo systemctl status td-agent.service

# td-agent 로그확인
[ec2-user@ip-10-88-0-200 ~]$ tail -f /var/log/td-agent/td-agent.log
      @type "json"
    </format>
  </match>
</ROOT>
2020-09-01 07:35:40 +0000 [info]: starting fluentd-1.11.1 pid=2734 ruby="2.7.1"
2020-09-01 07:35:40 +0000 [info]: spawn command to main:  cmdline=["/opt/td-agent/bin/ruby", "-Eascii-8bit:ascii-8bit", "/opt/td-agent/bin/fluentd", "--log", "/var/log/td-agent/td-agent.log", "--daemon", "/var/run/td-agent/td-agent.pid", "--under-supervisor"]
2020-09-01 07:35:40 +0000 [info]: adding match pattern="stream_data" type="kinesis_streams"
2020-09-01 07:35:41 +0000 [info]: adding source type="s3"
2020-09-01 07:35:41 +0000 [info]: #0 starting fluentd worker pid=2744 ppid=2741 worker=0
2020-09-01 07:35:41 +0000 [info]: #0 fluentd worker is now running worker=0

# td-agent 중지
[ec2-user@ip-10-88-0-200 etc]$ sudo systemctl stop td-agent.service
```

- td-agent config 파일양식


```python
# s3 input plugin
  <source>
    @type s3
    # bucket 정보 등록
    s3_bucket [bucket_name]
    # region 정보 등록
    s3_region [region]
    # meta data를 log에 포함여부
    add_object_metadata false
    # 저장 format
    store_as "json"
    # tag 정보 등록( tag로 output이 input 정보를 받아올 수 있음)
    tag [tag_name]
    # 계정 정보 등록
    aws_key_id xxxxxx
    aws_sec_key xxxxxx
    # 파싱 정보 등록
    <parse>
      @type csv
      # csv 컬럼명 등록
      keys [key_names]
    </parse>
    # sqs 정보 등록(필수)
    <sqs>
      queue_name [sqs_name]
    </sqs>
  </source>
  # output plugin
  <match [tag_name]>
    @type kinesis_streams
    # region 정보 등록
    region [region]
    # kinesis data stream 정보 등록
    stream_name [kinesis_stream_name]
    # 계정 정보 등록
    aws_key_id xxxxxx
    aws_sec_key xxxxxx
    <format>
      @type "json"
    </format>
  </match>
```

#### STEP 4. kinesis streams 구성

- 생성한 kinesis 정보는 아래와 같다


```python
! aws kinesis describe-stream --stream-name=[kinesisname]

{
    "StreamDescription": {
        "Shards": [
            {
                "ShardId": "shardId-000000000000",
                "HashKeyRange": {
                    "StartingHashKey": "0",
                    "EndingHashKey": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                },
                "SequenceNumberRange": {
                    "StartingSequenceNumber": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                }
            }
        ],
        "StreamARN": "arn:aws:kinesis:ap-northeast-2:xxxxxxxxxxx:stream/xxxxxxx",
        "StreamName": "xxxxxxxxxxxx",
        "StreamStatus": "ACTIVE",
        "RetentionPeriodHours": 48,
        "EnhancedMonitoring": [
            {
                "ShardLevelMetrics": [
                    "IncomingBytes",
                    "OutgoingRecords",
                    "IteratorAgeMilliseconds",
                    "IncomingRecords",
                    "ReadProvisionedThroughputExceeded",
                    "WriteProvisionedThroughputExceeded",
                    "OutgoingBytes"
                ]
            }
        ],
        "EncryptionType": "NONE",
        "KeyId": null,
        "StreamCreationTimestamp": 1598842426.0
    }
}
```

#### STEP 5. Kinesis to ES 파이프라인 구축을 위한 Lambda 개발

- 먼저 lambda function 생성 후 script에 필요한 라이브러리를 추가해야 한다.

step 1) requirements.txt 작성


```python
boto
elasticsearch
requests
requests_aws4auth
```

step 2) `pip install -r requirements.txt -t python` 명령어 python이라는 폴더에 라이브러리들을 다운로드

realtime폴더가 있고 그 폴더 안에 다음의 두개의 파일이 있어야 한다.

lambda_function.py

python(폴더)

그리고 realtime 폴더 상위로 이동해서 realtime 폴더를 zip파일로 만들어준다.

그 다음에 아래와 같은 터미널 명령어로 realtime.zip을 s3에 업로드하고, 그거를 lambda function에 업데이트 해준다.


```python
aws s3 cp ./realtime.zip s3://[bucketname]/realtime_architecture_lambda/realtime.zip
aws lambda update-function-code --function-name [lambdaname] --s3-bucket [bucketname] --s3-key realtime_architecture_lambda/realtime.zip
```

#### 위와 같은 방법으로 하면 적용이 안될 것이다. 

라이브러리 용량이 3MB 이하라면 인라인 코드 편집이 가능하지만, 3MB를 초과할 경우 아래와 같이 비활성화된다.

#### 라이브러리 크기가 3mb가 넘으면 lambda에 layer에 라이브러리를 등록해서 사용하도록 하자

다음과 같이 해주면 된다.

python 폴더를 python.zip으로 만든다음에

lambda 메뉴 이동 --> layer 메뉴 이동 --> create layer --> layer 생성 클릭


name : iac_libs --> upload a zip file로 python.zip을 업로드 --> runtimes pyhon 3.7 --> create 클릭


그런 다음에 작업하는 lambda function으로 이동 후 layers 클릭 --> 하단에 add a layer 클릭 --> 위에서 생성한 layer 등록



#### ** 주의사항 : 반드시 람다에 layer로 넣을 라이브러리들의 폴더이름은 python으로 해야한다 안그러면 인식을 못한다.


#### 폴더구조도 python.zip 파일을 클릭해서 조회하면 python 폴더가 보여야지 라이브러리들이 바로 보이면 안된다.


#### python.zip --> python --> 라이브러리들 .. (O)


#### python.zip --> 라이브러리들.. (X)

- lambda_function.py 내용


```python
import json
from boto import kinesis
import time
from elasticsearch import Elasticsearch,RequestsHttpConnection
import requests
from requests_aws4auth import AWS4Auth
import base64

# connection session to ES
host = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.ap-northeast-2.es.amazonaws.com' #without 'https'
YOUR_ACCESS_KEY = 'xxxxxxxxxxxxxxxxxxxxxxx'
YOUR_SECRET_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxx'
REGION = 'ap-northeast-2' 
awsauth = AWS4Auth(YOUR_ACCESS_KEY, YOUR_SECRET_KEY, REGION, 'es')
es = Elasticsearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)
    
def lambda_handler(event,context):
    global es

    for record in event["Records"]:
        decoded_data = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
        json_data = json.loads(decoded_data)
        
        es_id = json_data["timestamp"]
        del(json_data["timestamp"])
        
        json_data["timestamp"] = json_data.pop('timestamp_for_kibana')
        json_data['cpu_usage_percent'] = float(json_data['cpu_usage_percent'])
        json_data['cpu_ctx_switches'] = float(json_data['cpu_ctx_switches'])
        json_data['cpu_interrupts'] = float(json_data['cpu_interrupts'])
        json_data['cpu_soft_interrupts'] = float(json_data['cpu_soft_interrupts'])
        json_data['cpu_syscalls'] = float(json_data['cpu_syscalls'])
        json_data['mem_total'] = float(json_data['mem_total'])
        json_data['mem_available'] = float(json_data['mem_available'])
        json_data['mem_percent'] = float(json_data['mem_percent'])
        json_data['mem_used'] = float(json_data['mem_used'])
        json_data['mem_free'] = float(json_data['mem_free'])

        es.index(index="computer_metric", doc_type="header_data", id=es_id, body=json_data)
        
        print(es_id, json_data, "success")
        
    return 'batch_job_done'
```

- lambda function 실행결과 발생하는 1개의 데이터 예시


```python
2020-09-03T16:11:41Z {'cpu_usage_percent': 14.4, 'cpu_ctx_switches': 555991280.0, 'cpu_interrupts': 2798016401.0, 'cpu_soft_interrupts': 0.0, 'cpu_syscalls': 1867281113.0, 'mem_total': 17084211200.0, 'mem_available': 4082380800.0, 'mem_percent': 76.1, 'mem_used': 13001830400.0, 'mem_free': 4082380800.0, 'timestamp': '2020-09-03T07:11:41Z'} success
```

- 만약에 람다가 아니라 로컬에서 kinesis to Elasticsearch를 하고자 한다면 아래와 같이 하면된다.


```python
import json
from boto import kinesis
import time
from elasticsearch import Elasticsearch,RequestsHttpConnection
import requests
from requests_aws4auth import AWS4Auth

# connection session to ES
host = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.ap-northeast-2.es.amazonaws.com' #without 'https'
YOUR_ACCESS_KEY = 'xxxxxxxxxxxxxxxxxxxxxxx'
YOUR_SECRET_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxx'
REGION = 'ap-northeast-2' 
awsauth = AWS4Auth(YOUR_ACCESS_KEY, YOUR_SECRET_KEY, REGION, 'es')
es = Elasticsearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

# connection session to kinesis
kinesis_auth = {"aws_access_key_id": YOUR_ACCESS_KEY, "aws_secret_access_key": YOUR_SECRET_KEY}
kinesis = kinesis.connect_to_region('ap-northeast-2',**kinesis_auth)
    
    
shard_it = kinesis.get_shard_iterator('iac-kds', 'shardId-000000000000', 'LATEST')['ShardIterator']
    
for i in range(1,1000):
    record = kinesis.get_records(shard_it, limit=2)

    if record['Records']:
        data = record['Records'][0]['Data'][0:-1]
        json_data = json.loads(data)

        es_id = json_data["timestamp"]
        del(json_data["timestamp"])

        json_data["timestamp"] = json_data.pop('timestamp_for_kibana')
        json_data['cpu_usage_percent'] = float(json_data['cpu_usage_percent'])
        json_data['cpu_ctx_switches'] = float(json_data['cpu_ctx_switches'])
        json_data['cpu_interrupts'] = float(json_data['cpu_interrupts'])
        json_data['cpu_soft_interrupts'] = float(json_data['cpu_soft_interrupts'])
        json_data['cpu_syscalls'] = float(json_data['cpu_syscalls'])
        json_data['mem_total'] = float(json_data['mem_total'])
        json_data['mem_available'] = float(json_data['mem_available'])
        json_data['mem_percent'] = float(json_data['mem_percent'])
        json_data['mem_used'] = float(json_data['mem_used'])
        json_data['mem_free'] = float(json_data['mem_free'])

        es.index(index="computer_metric", doc_type="header_data", id=es_id, body=json_data)

        print(es_id, json_data, "success")

        shard_it = record['NextShardIterator']

    else :
        pass

    time.sleep(0.2)
```

여기까지 완료하면 LocalPC to ES 실시간 데이터 파이프라인을 구성완료한 것이다.

ES kibana에서 데이터를 조회하면 실시간으로 데이터가 들어오는 것을 확인할 수 있다.

#### STEP 6. Kibana에서 대시보드 만들기

- 그 다음에 프라이빗 subnet에 있는 ES를 베스천 서버를 통해서 local port forwarding으로 접근하여 키바나에 접속할 수 있도록하자.

접근을 시도하는 로컬PC에서 아래와 같은 명령어로 터널링


```python
ssh -i [keyname].pem ec2-user@[베스천PublicIP] -L 9200:vpc-xxxx-rtd-cluster-xxxxxxxxxx.ap-northeast-2.es.amazonaws.com:443  # https:// 부분 빼고
```

크롬을 열고 아래와 같은 주소로 접근

`https://localhost:9200/_plugin/kibana/`

키바나로 접근후, index 설정하고 시각화 대시보드를 만들어주면 된다.

- 키바나에 적재되는 데이터 예시

![kibana result](https://user-images.githubusercontent.com/41605276/92083565-30d70f80-ee01-11ea-9740-08d57d1aa07e.png)
