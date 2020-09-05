##  텍스트 데이터 토픽 분류 서비스를 제공하는 웹서버 구현결과

> 특정 텍스트를 입력받아 정치, 경제, 과학/기술 등의 토픽으로 예측하여 결과값을 리턴하는 나이브베이즈 모델 서빙 웹서버 구현

### 1. 개요

#### 1.1. 기술스텍

1) 텍스트 처리(TFIDF)

2) 나이브 베이즈 모델

3) Flask

4) Nginx

5) html, css

6) AWS EC2

7) highcharts

#### 1.2.  프로젝트 구현 아키텍처

![0](https://user-images.githubusercontent.com/41605276/59682712-bcbb4680-9211-11e9-9373-62f4a55c5205.png)

### 2. 웹서버 구동방법

#### step 1) 사전에 수집한 텍스트 데이터(naver_article.plk)를 이용하여 TF-IDF기법을 적용한 나이브베이즈 모형(classification_model.pkl)구현

- 수집한 텍스트 데이터(naver_article.plk) 내용

x_value = article_df['content'] / 아래그림 빨간박스

y_value = article_df['category'] / 아래그림 파란박스

![0-1](https://user-images.githubusercontent.com/41605276/59682730-c5138180-9211-11e9-902b-ece30511e81b.png)

- 모델링 관련 상세내용 make_model.py 참고

#### step 2) flask를 이용한 웹어플리케이션 구현 

상세내용 flask_app.py, index.html 참고

#### step 3) flask_app.py, classification_model.pkl, index.html 등 AWS EC2 탑재

#### step 4) Nginx 초기 설정 및 flask 어플리케이션 실행

1) sudo vi /etc/nginx/sites-available/default 명령어로 default 파일 실행

2) default 내용에서 아래의 코드의 80을 9999로 수정

listen 80 default_server;

listen [::]:80 default_server;

3) default 내용 최하단에 다음과 같이 코드를 추가

`
server {
    listen 80;
    location / {
        proxy_pass http://localhost:5000;
    }
}
`

4) 저장 및 파일 수정종료

5) sudo systemctl restart nginx 명령어로 Nginx 재시작 및 설정파일 적용

6) python flask_app.py 명령어로 flask 어플리케이션 실행

7) 클라이언트 browser에 `http://<public_ip>/`로 접속

### 3. 웹서버 구동결과

1) 클라이언트 browser에 `http://<public_ip>/`로 접속시 최초화면

![0-2](https://user-images.githubusercontent.com/41605276/59682741-cba1f900-9211-11e9-8526-f91797cd759f.png)

2) 검색창에 '올바른 머신러닝 모델 구현을 위해 데이터 전처리를 잘 해줘야 한다.' 문장 입력 후 prediction 클릭 시 결과

![1](https://user-images.githubusercontent.com/41605276/59682754-d3619d80-9211-11e9-80ce-5298970a427f.png)

3) 브라우저 검색창에 `http://<public_ip>/predic?sentence=data` 검색 시 결과

=> json 형태로 모델 prediction값 return

![3](https://user-images.githubusercontent.com/41605276/59682764-d9577e80-9211-11e9-8174-43e6b3f5dfde.png)

4) 리눅스 콘솔 상 flask 실행화면

![2](https://user-images.githubusercontent.com/41605276/59682779-deb4c900-9211-11e9-9c79-5d3c299ad9ac.png)
