##  트위터 스트리밍 데이터 실시간 감성분석 시스템 구현결과

> 카프카를 이용한 트위터 스트리밍 데이터 처리 및 감성분석, 시각화 파이프라인 구축

### 1. 개요

#### 1.1. 아이디어

- 트위터 스트리밍 데이터를 실시간으로 처리하는 카프카 시스템 구축 아이디어 구상


- 데이터를 처리하는 방식은 기존에 감성분석 training이 되어있는 딥러닝 모델을 차용하여 트위터 스트리밍 데이터에 적용


- Dash를 이용하여 스트리밍 데이터 처리결과에 대한 시각화 구현


#### 1.2.  프로젝트 구현 아키텍처

![1](https://user-images.githubusercontent.com/41605276/58776015-75269f00-8603-11e9-8e12-d8be03ede159.png)

#### 1.3. 기술스텍

0) 시스템 구현 환경 : 우분투 리눅스, 파이썬 3.7

1) 트위터 스트리밍 데이터 API와 Kafka 연결 : Kafka Connect Twitter packages

- URL : https://github.com/Eneco/kafka-connect-twitter

2) 트위터 스트리밍 데이터 처리 및 모니터링 : Kafka


- 버전 : 2.2.0


3) Kafka로 부터 트위터 스트리밍 데이터를 받아서 Batch 단위로 모델링 적용 및 처리 : Spark streaming


- 버전 : 2.4.0


4) 감성분석 모델 적용 : DeepMoji

- 예측하는 감성에 맞는 이모티콘을 Return 하는 딥러닝 모델


- URL : https://github.com/bfelbo/DeepMoji


- 버전 : 0.4.5

5) 모델링 적용 결과 시각화 : Dash


6) 기타 필요한 패키지

- keras 2.0.9


- h5py


- numpy


- scikit-learn


- tensorflow 1.13.1


- text-unidecode 1.0


### 2. 시스템 구동방법

step 1) kafka server 구동

step 2) kafka connect twitter package 실행

- twitter streaming data API에서 kafka 연결


- step 2)까지 수행결과 트위터 스트리밍 데이터가 카프카 콘솔로 실시간 전시되는 것을 확인

![2](https://user-images.githubusercontent.com/41605276/58776025-7ce64380-8603-11e9-83d5-b25994d31785.png)

step 3) opear_dash.py를 실행하여 Dash 서버 구동


step 4) Deepmoji 패키지 다운 및 setup.py 실행


- setup.py 실행 전 아래와 같은 내용으로 수정필요

![3](https://user-images.githubusercontent.com/41605276/58776030-840d5180-8603-11e9-9288-b7f42d19e629.png)

- setup.py 실행 시 명령어 : python setup.py install

step 4) apply_model.py를 실행

- 감성분석 모델 적용 및 데이터 처리, Dash로 전송


- 실행 시 명령어


```python
./spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.0 apply_model.py
```

### 3. 시스템 구동결과

1) ./spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.0 apply_model.py 실행한 터미널

![4](https://user-images.githubusercontent.com/41605276/58776041-8b345f80-8603-11e9-8611-0851256eb434.png)

5초마다 위와같은 데이터프레임 형식의 batch 업데이트 수행

2) 웹브라우저로 접속한 Dash 로컬 서버

![5](https://user-images.githubusercontent.com/41605276/58776049-9091aa00-8603-11e9-9062-8c7114e0fcd9.png)

5초마다 위와같은 데이터프레임 형식의 batch 업데이트 되면서 동시에 위와 같은 대시보드도 실시간으로 변동된다.

3) opear_dash.py 실행 콘솔

![6](https://user-images.githubusercontent.com/41605276/58776059-97202180-8603-11e9-9182-eab70267e9b6.png)


### 4. 프로젝트 로드맵 및 수행경과

#### STEP 1) 문제정의 및 프로젝트 계획 구상

- 아이디어 도출 


- 프로젝트 구현 아키텍처 구상


- 프로젝트 시행 계획 수립 -> 아키텍처 부분별 단계적인 구현


#### STEP 2) Kafka를 이용한 데이터 스트리밍 데이터 수집


- Kafka Connect Twitter package를 이용한 트위터 스트리밍 데이터 API와 Kafka 연결


#### STEP 3) 트위터 스트리밍 데이터 실시간 대시보드 구현


- 트위터 스트밍 데이터 중 헤시테그로 시작하는 문장을 word counting하여 Dash로 시각화 구현

-> step 4)에서 '헤시테그로 시작하는 문장을 word counting'하는 부분을 emoji model을 적용하는 것으로 응용

- step 3) 구현결과

![7](https://user-images.githubusercontent.com/41605276/58776398-6e009080-8605-11e9-9b84-0ef85f2c1350.png)

#### STEP 4) emoji 모델을 적용한 스트리밍 데이터 처리 실시간 대시보드 구현

- step 4) 구현 간 주요이슈 

1) emoji 모델 구현환경이 python 버전 2 베이스로 3.7에서는 적용불가

-> emoji 패키지에서 python 버전 2 부분을 3 버전으로 적용할 수 있도록 일부 파일 수정

트러블 슈팅 시 참고한 URL : https://github.com/zzsza/DeepMoji-Python3

2) 미니멀한 데이터프레임에 Deepmoji 적용 시 프로그램 구동효율 최적화 문제

-> apply_model.py에서 st, model을 class화 하여 모델이 호출될때 broadcasting 할 수 있도록 구현
