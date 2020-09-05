##  스케쥴러를 이용한 네이버 실시간 검색어 순위 데이터수집 AWS 서버 구현결과

> 네이버 실시간 검색어 순위 데이터를 스케쥴러(크론탭)를 이용하여 정기적으로 웹크롤링, DB 저장, slack 알림을 수행하는 AWS EC2 서버구축

### 1. 개요

#### 1.1. 기술스텍

1) SQL활용

2) crontab

3) 리눅스

4) AWS EC2

5) python 프로그래밍

6) slack webhooks

#### 1.2.  프로젝트 구현 아키텍처

![0](https://user-images.githubusercontent.com/41605276/59611215-de56f800-9155-11e9-9d2f-324f697a2208.png)

### 2. 시스템 구동방법

주요 시스템 구동 관련 내용은 keywords.py 참고

step 1) 아래와 같이 EC2 리눅스에서 환경변수 설정

![0-1](https://user-images.githubusercontent.com/41605276/59611230-e4e56f80-9155-11e9-8ba4-f2c752716b33.png)

step 2) 아래와 같이 네이버 실시간 검색어 순위 데이터 저장을 위한 SQL 데이터베이스 및 테이블 생성

![1](https://user-images.githubusercontent.com/41605276/59611243-eadb5080-9155-11e9-88b8-a9873bd20e55.png)

step 3) 크론탭 설정 및 실행

1) 아래와 같이 타임존 한국시간으로 설정

![1-1](https://user-images.githubusercontent.com/41605276/59611260-f0389b00-9155-11e9-8ed0-4aac3fccb5cd.png)

2) 크론탭 스케쥴러 설정 (crontab -e)

=> 설정완료 시 매 2분 간격으로 keywords.py 실행

![1-2](https://user-images.githubusercontent.com/41605276/59611272-f62e7c00-9155-11e9-98aa-8befa9a2884c.png)

- 위와 같이 설정 후 저장 시 결과

![1-3](https://user-images.githubusercontent.com/41605276/59611278-fb8bc680-9155-11e9-93f5-79a2aa6e89c2.png)

### 3. 시스템 구동결과

#### 1) slack

![4](https://user-images.githubusercontent.com/41605276/59611285-021a3e00-9156-11e9-90b3-b83eb5493c14.jpg)

#### 2) mysql

![2](https://user-images.githubusercontent.com/41605276/59611298-08101f00-9156-11e9-8850-7cc0c8a9502e.png)

#### 3) nosql

![3](https://user-images.githubusercontent.com/41605276/59611310-0e9e9680-9156-11e9-9792-f70dd31d4393.png)
