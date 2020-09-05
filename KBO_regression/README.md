##  프로야구팀 시즌승률 예측을 위한 선형회귀모델 구현결과

> KBO 홈페이지에서 01 ~ 18 시즌 팀기록을 웹크롤링하여 수집한 데이터를 기반으로 팀승률을 종속변수로하는 선형회귀모델 구현

### 1. 개요

#### 1.1. 아이디어

- 2019 시즌 응원하는 팀의 시즌 승률을 예측할 수 있는 방법이 있을까하는 아이디어에서 출발


- KBO 홈페이지에서 팀기록을 크롤링하여 선형회귀 분석모델을 구현해보자는 구상

#### 1.2.  프로젝트 목적

- KBO 홈페이지에서 2001 ~ 2018 시즌 팀기록을 웹크롤링하여 수집한 데이터를 기반으로 팀승률을 종속변수로하는 선형회귀모델 구현


#### 1.3. 기술스텍

- 파이썬 프로그래밍, 웹크롤링, 선형회귀분석, 데이터 전처리 등

### 2. 프로젝트 수행결과 요약

#### STEP 1) 문제정의 및 프로젝트 계획 구상

- 아이디어 도출


- 프로젝트 시행 계획 수립


#### STEP 2) 데이터 수집


- KBO 공식 홈페이지 'https://www.koreabaseball.com/TeamRank/TeamRank.aspx' 크롤러 파이썬 코드구현


- 데이터 수집결과

팀명, 승률, 팀 방어율, 팀 타율 등 데이터 수집


#### STEP 3) 데이터 탐색

- 결측치 확인


- 피쳐별 변수치우침 여부 확인


- 피쳐별 이상치 확인


- 피쳐 간 상관관계 확인

#### STEP 4) 데이터 전처리

1) error(팀실책), P_hitted(팀 피안타) 변수 등을 각각 num_game(시즌 총 경기수) 변수로 나누어서 각각 경기당 팀실책, 경기당 팀피안타 등으로 전처리

- 사유 : model prediction 시 편의성 도모


2) feature selection 기법적용

일부 변수 간 조합으로 가장 높은 퍼포먼스를 보여주는 변수추출


#### STEP 5) 모델링 및 모델평가

1) 실제 데이터와 모델 예측값 비교

2) 잔차정규성 검정

3) Kfold 교차검증


### 3. 프로젝트 수행결과 상세

#### STEP 2) 데이터 수집

1) 웹크롤러 구현 및 데이터 수집결과

- 웹크롤러는 KBO_crawler.py에 구현


```python
## 필요한 모듈 임포트
%matplotlib inline
%config InlineBackend.figure_format = 'retina'
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import scale
import statsmodels.api as sm
from sklearn.feature_selection import *
from sklearn.model_selection import train_test_split
import pandas as pd
import itertools
from sklearn.metrics import * 
from sklearn.model_selection import KFold
from statsmodels.graphics import utils
from statsmodels.stats.outliers_influence import variance_inflation_factor
```

- 웹크롤러 실행결과

KBO 공식홈페이지 팀기록 파트 https://www.koreabaseball.com/TeamRank/TeamRank.aspx 크롤링 및 수집한 데이터 KBO_record.plk로 저장


```python
! python KBO_crawler.py
```

    Crawling start
    Crawling complete, endtime :   362.8636794090271
    reset indexing complete
    KBO_record.plk save complete, program done!
    


```python
# 저장한 데이터 로드
df = pd.read_pickle("KBO_record.plk")
```

![1](https://user-images.githubusercontent.com/41605276/59484877-8c407900-8eae-11e9-832f-4d6c2ecaba08.png)

컬럼설명

- rank : 순위, num_game : 시즌 게임수, win_rate : 승률, AVG : 팀타율, scoring : 팀득점 , "hit" : h, 팀 1루타 수


- "double" : double, 팀 2루타 수, 'triple' : triple, 팀 3루타 수, 'HR' : 팀 홈런수, 'RBI' : 팀 타점, 'SAC' : 팀 희생번트수


- 'SF' : 팀 희생플라이수, "RISP" : 팀 득점권타율, "PA_BA" : 팀 대타타율, "ERA" : 팀 평균자책점, "save" : 팀 세이브 수


- 'hold' : 팀 홀드수,'PW' : 팀 선발투수 승률,'P_hitted' : 팀 피안타,'SO' : 팀 탈삼진,'WHIP' : 팀 WHIP


- "CG" : 팀 완투, "shutout" : 팀 완봉, 'QS' : 팀 퀄리티 스타트 수, 'BV' : 팀 블론세이브 수, 'PN' : 팀 투구수


- 'P_AVG' : 팀 피안타율, 'WP' : 팀 와일드피치, "error" : 팀 실책수

#### STEP 3) 데이터 탐색 및 전처리

1) error(팀실책), P_hitted(팀 피안타) 변수를 각각 num_game(시즌 총 경기수) 변수로 나누어서 각각 경기당 팀실책, 경기당 팀피안타로 전처리

- 사유 : model prediction 시 편의성 도모


```python
df['num_game'] = df['num_game'].apply(lambda data: float(data))
# num_game 컬럼 float 형태의 데이터로 변경

for column in list(df.columns[2:]):
    df[column] = df[column].apply(lambda data: float(data))

for columns in ['error','P_hitted']:
    df[columns] = df[columns] / df['num_game']
```

2) 컬럼별 결측값 확인


```python
total = df.isnull().sum().sort_values(ascending=False)
percent = (df.isnull().sum()/df.isnull().count()).sort_values(ascending=False)
missing_data = pd.concat([total, percent], axis=1, keys=['Total', 'Percent'])
missing_data
```

![2](https://user-images.githubusercontent.com/41605276/59484936-cdd12400-8eae-11e9-8dd9-21b94c033555.png)

3) 피쳐별 변수치우침 여부 확인


```python
## skew 절대값이 1.5인 컬럼 확인
abs(df[df.columns[4:]].skew()) > 1.5
```

![3](https://user-images.githubusercontent.com/41605276/59484977-f3f6c400-8eae-11e9-9e70-f1915d77941a.png)


4) 모델의 일반화를 위한 피쳐별 이상치 확인

- 모델의 일반화를 위해 IOR Rule을 기준으로 일반분포에서 크게 벗어나는 레코드 삭제


- IOR = 3사분위수 - 1사분위수


- IOR Rule : Q3 +1.5 * IQR 보다 크거나 Q1-1.5 * IQR 보다 작으면 이상치라고 판단

=> 총 22개의 이상치 레코드 제거


```python
df_temp = pd.DataFrame(columns=df.columns)

for column in df.columns[4:]:           
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    condition1 = Q1 - 1.5*IQR < df[column]
    condition2 = Q3 + 1.5*IQR > df[column]
    total_condition = np.logical_and(condition1, condition2)
    
    df_temp = pd.concat([df_temp,df[total_condition==False]])
    
    # 이상치 데이터 제외
    df = df[total_condition]
    
# 이상치 데이터만 모아놓은 데이터 프레임
df_temp
```

![4](https://user-images.githubusercontent.com/41605276/59485028-22749f00-8eaf-11e9-9403-ea09d59029dd.png)

5) 변수간 상관관계 확인

- 모든변수간에 조합해서 비교하는 것은 상당히 경우의 수가 많기 때문에 생략하고, target value에 대한 다른 변수들간 상관관계 확인

결론 : 선발투수 승률은 곧 승률과 같기 때문에 선발투수와 승률간의 상관관계가 거의 일치함. 따라서 PW(선발투수 승률) 칼럼은 제거


```python
## target value에 대한 변수간 상관관계 확인
temp = df[list(df.columns)[3:]].corr()
temp['win_rate'].sort_values(ascending=[False])
```




    win_rate    1.000000
    PW          0.998553
    save        0.615544
    OPS         0.476335
    scoring     0.401554
    RBI         0.393169
    AVG         0.386213
    shutout     0.380451
    RISP        0.364409
    QS          0.295634
    HR          0.289986
    hold        0.260972
    SO          0.210495
    hit         0.198183
    SF          0.195622
    triple      0.147323
    double      0.144657
    PA_BA       0.039216
    SAC         0.002161
    BV         -0.092802
    CG         -0.095758
    PN         -0.119596
    error      -0.191001
    WP         -0.287580
    P_hitted   -0.425930
    P_AVG      -0.506351
    WHIP       -0.552409
    ERA        -0.552462
    Name: win_rate, dtype: float64



6) 아웃라이어 데이터 식별 및 제거

레버리지와 잔차의 크기가 모두 큰 데이터들을 아웃라이어로 판단하고자 하는데 통상 잔차와 레버리지를 동시에 보기위한 기준으로는 Cook's Distance가 있다. 결론적으로 Cook's Distance 지표를 이용하여 Fox' Outlier Recommendation를 적용하여 아래 수식을 충족하는 데이터를 아웃라이어로 판단

![7](https://user-images.githubusercontent.com/41605276/59485708-cc552b00-8eb1-11e9-8f50-236392a216c7.png)


```python
dfX = df[['ERA', 'save', 'hold', 'P_hitted', 'SO', 'WHIP', 'CG', 'shutout',
           'QS', 'BV', 'PN', 'P_AVG', 'WP', 'AVG', 'scoring', 'hit', 'double',
           'triple', 'HR', 'RBI', 'SAC', 'SF', 'OPS', 'RISP', 'PA_BA', 'error']]
dfX = sm.add_constant(dfX)
dfy = df[["win_rate"]]

model = sm.OLS(dfy, dfX)
result = model.fit()
pred = result.predict(dfX)

influence = result.get_influence()
cooks_d2, pvals = influence.cooks_distance
K = influence.k_vars
fox_cr = 4 / (len(dfy) - K - 1)
idx = np.where(cooks_d2 > fox_cr)[0]

print("아웃라이어 인덱스 번호 : " , idx)

## 아웃라이어 제거
df = df.drop(idx)
dfX = df[['ERA', 'save', 'hold', 'P_hitted', 'SO', 'WHIP', 'CG', 'shutout',
           'QS', 'BV', 'PN', 'P_AVG', 'WP', 'AVG', 'scoring', 'hit', 'double',
           'triple', 'HR', 'RBI', 'SAC', 'SF', 'OPS', 'RISP', 'PA_BA', 'error']]
dfX = sm.add_constant(dfX)
dfy = df[["win_rate"]]

len(dfX)
```

    아웃라이어 인덱스 번호 :  [  5  37  66  73 108 110 117]
    




    125



7) feature selection 기법적용

일부 변수 간 조합으로 가장 높은 퍼포먼스를 보여주는 변수추출

- 모든변수를 모델에 반영했을때 퍼포먼스 확인

=> 과적합 및 다중공선성 증상 확인, 확률론적 선형회귀모델을 준수하지 않는 현상(잔차정규성 통과미달) 확인


```python
dfX_all = df[['ERA', 'save', 'hold', 'PW', 'P_hitted', 'SO', 'WHIP', 'CG', 'shutout',
           'QS', 'BV', 'PN', 'P_AVG', 'WP', 'AVG', 'scoring', 'hit', 'double',
           'triple', 'HR', 'RBI', 'SAC', 'SF', 'OPS', 'RISP', 'PA_BA', 'error']]

dfX_all = sm.add_constant(dfX_all)
dfy = df[["win_rate"]]

new_df = pd.concat([dfy, dfX_all], axis=1)

scores = np.zeros(3)
cv = KFold(3, shuffle=True, random_state=0)
for i, (idx_train, idx_test) in enumerate(cv.split(new_df)):
    df_train = df.iloc[idx_train]
    df_test = df.iloc[idx_test]
    
    model = sm.OLS(df_train.win_rate, df_train[['ERA', 'save', 'hold', 'PW', 'P_hitted', 'SO', 
                                            'WHIP', 'CG', 'shutout', 'QS', 'BV', 'PN', 'P_AVG', 
                                            'WP', 'AVG', 'scoring', 'hit', 'double', 'triple', 
                                            'HR', 'RBI', 'SAC', 'SF', 'OPS', 'RISP', 'PA_BA', 'error']])
    result = model.fit()

    pred = result.predict(df_test[['ERA', 'save', 'hold', 'PW', 'P_hitted', 'SO', 
                                    'WHIP', 'CG', 'shutout', 'QS', 'BV', 'PN', 'P_AVG', 
                                    'WP', 'AVG', 'scoring', 'hit', 'double', 'triple', 
                                    'HR', 'RBI', 'SAC', 'SF', 'OPS', 'RISP', 'PA_BA', 'error']])
    
    rss = ((df_test.win_rate - pred) ** 2).sum()
    tss = ((df_test.win_rate - df_test.win_rate.mean()) ** 2).sum()
    rsquared = 1 - rss / tss
    
    scores[i] = rsquared
    print("train R2 = {:.8f}, test R2 = {:.8f}".format(result.rsquared, rsquared))
    
    plt.figure(figsize=(8, 5))
    sp.stats.probplot(result.resid, plot=plt)
    plt.show()
    
    plt.figure(figsize=(8, 5))
    plt.scatter(df_test.win_rate, pred)
    plt.xlabel('real value')
    plt.ylabel('predicted value')
    plt.show()
    
    test = sm.stats.omni_normtest(result.resid)
    for xi in zip(['Chi^2', 'P-value'], test):
        print("%-12s: %6.3f" % xi)
```

    train R2 = 0.99996084, test R2 = 0.99517618
    


<img width="523" alt="프로야구 팀시즌 승률예측을 위한 선형회귀모델 구현결과_19_1" src="https://user-images.githubusercontent.com/41605276/59485104-68316780-8eaf-11e9-9b60-06ef858310dc.png">

<img width="510" alt="프로야구 팀시즌 승률예측을 위한 선형회귀모델 구현결과_19_2" src="https://user-images.githubusercontent.com/41605276/59485110-6e274880-8eaf-11e9-8063-f8f131476119.png">

    Chi^2       : 57.721
    P-value     :  0.000
    train R2 = 0.99997788, test R2 = 0.99064025
    

<img width="523" alt="프로야구 팀시즌 승률예측을 위한 선형회귀모델 구현결과_19_4" src="https://user-images.githubusercontent.com/41605276/59485129-7aaba100-8eaf-11e9-9f5c-faeb7c1f22b3.png">


<img width="510" alt="프로야구 팀시즌 승률예측을 위한 선형회귀모델 구현결과_19_5" src="https://user-images.githubusercontent.com/41605276/59485139-8303dc00-8eaf-11e9-87f3-bbbff06c5c38.png">

    Chi^2       : 37.272
    P-value     :  0.000
    train R2 = 0.99993617, test R2 = 0.99729660
    


<img width="523" alt="프로야구 팀시즌 승률예측을 위한 선형회귀모델 구현결과_19_7" src="https://user-images.githubusercontent.com/41605276/59485151-8b5c1700-8eaf-11e9-9e01-04b36d789168.png">


<img width="510" alt="프로야구 팀시즌 승률예측을 위한 선형회귀모델 구현결과_19_8" src="https://user-images.githubusercontent.com/41605276/59485160-92832500-8eaf-11e9-8395-183ed7d13fc8.png">


    Chi^2       : 58.570
    P-value     :  0.000
    

- 결정계수 퍼포먼스에 가장 영향을 끼치는 피쳐 추출

1) 도메인 지식 상 변수간 상관관계가 강한 데이터 셋이기 때문에 VIF 지수로 다중공선성을 최소화 하여 변수를 추출

수비와 공격 각각의 지표에서 두개이상 지표가 섞일경우 VIF 지수가 매우 높아지는 현상 식별, 최소한의 피쳐선택으로 다중공선성 및 condition number 급증 현상을 줄이고자 하는 의도

2) 수비지표에서는 ERA(팀 방어율)와 save(팀 세이브)가 승률에 강하게 영향을 주는 것으로 확인

3) 공격지표에서는 scoring(팀득점), RBI(팀타점), OPS(팀OPS)가 승률에 강하게 영향을 주는 것으로 확인 

#### ㅇ 결론적으로 모델을 구성하기 위한 피쳐로 수비지표에서는 ERA는 공격지표에서는 OPS를 선택


```python
X_train, X_test, y_train, y_test = train_test_split(dfX, dfy, test_size = 0.2, random_state = 101)

for L in range(1, 3+1):
    for subset in itertools.combinations(dfX.columns[1:], L): # dfX.columns에서 L개를 선택하는 모든 조합
        
        columns = list(subset)
        columns.append('const')
        
        new_x_train = X_train[columns] # X[tuple]은 작동하지 않아서, X[list]형태로 바꿔준 것
        new_x_test = X_test[columns]
        
        model = sm.OLS(y_train,new_x_train).fit()
        pred = model.predict(new_x_test)
        pred = pd.DataFrame(pred, columns=['win_rate'])
        
        rss = ((y_test - pred) ** 2).sum()[0]
        tss = ((y_test - y_test.mean()) ** 2).sum()[0]
        rsquared = 1 - rss / tss
    
        base_accuracy = 0.8
        if rsquared > base_accuracy:
            print(list(subset), '\t', rsquared) 
```

    ['ERA', 'scoring'] 	 0.836221079671827
    ['ERA', 'RBI'] 	 0.8276125405540665
    ['ERA', 'OPS'] 	 0.8208170219146089
    ['ERA', 'save', 'scoring'] 	 0.8913522785437897
    ['ERA', 'save', 'RBI'] 	 0.8905377074886883
    ['ERA', 'save', 'OPS'] 	 0.8896006074179582
    ['ERA', 'hold', 'scoring'] 	 0.8359198260523067
    ['ERA', 'hold', 'RBI'] 	 0.8256593047124634
    ['ERA', 'hold', 'OPS'] 	 0.8240213448208071
    ['ERA', 'P_hitted', 'scoring'] 	 0.8497375884000019
    ['ERA', 'P_hitted', 'RBI'] 	 0.8397440901782567
    ['ERA', 'P_hitted', 'OPS'] 	 0.8202915169276047
    ['ERA', 'SO', 'scoring'] 	 0.8391082956798452
    ['ERA', 'SO', 'RBI'] 	 0.8298688980826551
    ['ERA', 'SO', 'OPS'] 	 0.8287152946760252
    ['ERA', 'WHIP', 'scoring'] 	 0.8362333079347508
    ['ERA', 'WHIP', 'RBI'] 	 0.8274799149192051
    ['ERA', 'WHIP', 'OPS'] 	 0.8209242294706027
    ['ERA', 'CG', 'scoring'] 	 0.8207416103212224
    ['ERA', 'CG', 'RBI'] 	 0.8071967040988538
    ['ERA', 'CG', 'OPS'] 	 0.8124505390660526
    ['ERA', 'shutout', 'scoring'] 	 0.8357913623238215
    ['ERA', 'shutout', 'RBI'] 	 0.8268324786820498
    ['ERA', 'QS', 'scoring'] 	 0.8512467634847811
    ['ERA', 'QS', 'RBI'] 	 0.8402753549384359
    ['ERA', 'QS', 'OPS'] 	 0.8231692278751404
    ['ERA', 'BV', 'scoring'] 	 0.84892328484598
    ['ERA', 'BV', 'RBI'] 	 0.8405889863514837
    ['ERA', 'BV', 'OPS'] 	 0.8205273640833928
    ['ERA', 'PN', 'scoring'] 	 0.8612436770117389
    ['ERA', 'PN', 'RBI'] 	 0.8483630346152548
    ['ERA', 'PN', 'OPS'] 	 0.8259998620157489
    ['ERA', 'P_AVG', 'scoring'] 	 0.8508674477478133
    ['ERA', 'P_AVG', 'RBI'] 	 0.8415335162143451
    ['ERA', 'P_AVG', 'OPS'] 	 0.8219915217154634
    ['ERA', 'WP', 'scoring'] 	 0.8412075709598011
    ['ERA', 'WP', 'RBI'] 	 0.8310875180096117
    ['ERA', 'WP', 'OPS'] 	 0.8260344490624982
    ['ERA', 'AVG', 'scoring'] 	 0.8332769448393799
    ['ERA', 'AVG', 'RBI'] 	 0.8257542988809843
    ['ERA', 'AVG', 'OPS'] 	 0.8243568525966402
    ['ERA', 'scoring', 'hit'] 	 0.8826802161427909
    ['ERA', 'scoring', 'double'] 	 0.8456115592421629
    ['ERA', 'scoring', 'triple'] 	 0.8362520780288176
    ['ERA', 'scoring', 'HR'] 	 0.8354477841983444
    ['ERA', 'scoring', 'RBI'] 	 0.8367189008860673
    ['ERA', 'scoring', 'SAC'] 	 0.8362802892471072
    ['ERA', 'scoring', 'SF'] 	 0.8249504096067013
    ['ERA', 'scoring', 'OPS'] 	 0.8552013510018583
    ['ERA', 'scoring', 'RISP'] 	 0.8302279617089319
    ['ERA', 'scoring', 'PA_BA'] 	 0.8383147621895177
    ['ERA', 'scoring', 'error'] 	 0.8464512455607343
    ['ERA', 'hit', 'RBI'] 	 0.8626959120116637
    ['ERA', 'hit', 'OPS'] 	 0.8233535692276284
    ['ERA', 'double', 'RBI'] 	 0.8332791559635457
    ['ERA', 'double', 'OPS'] 	 0.8194088258264416
    ['ERA', 'triple', 'RBI'] 	 0.8272014444916562
    ['ERA', 'triple', 'OPS'] 	 0.8264960092360525
    ['ERA', 'HR', 'RBI'] 	 0.8275287837560293
    ['ERA', 'HR', 'OPS'] 	 0.8321614561293101
    ['ERA', 'RBI', 'SAC'] 	 0.8280322610343791
    ['ERA', 'RBI', 'SF'] 	 0.8193037519763745
    ['ERA', 'RBI', 'OPS'] 	 0.8500481796318611
    ['ERA', 'RBI', 'RISP'] 	 0.8212200773236721
    ['ERA', 'RBI', 'PA_BA'] 	 0.8294653208899325
    ['ERA', 'RBI', 'error'] 	 0.8428687271629773
    ['ERA', 'SAC', 'OPS'] 	 0.8193710615751697
    ['ERA', 'SF', 'OPS'] 	 0.82706631495376
    ['ERA', 'OPS', 'RISP'] 	 0.8302907976561682
    ['ERA', 'OPS', 'PA_BA'] 	 0.8153607470159444
    ['ERA', 'OPS', 'error'] 	 0.8206411489325748
    ['save', 'P_hitted', 'AVG'] 	 0.8048941498190019
    ['save', 'P_hitted', 'scoring'] 	 0.8435790358142813
    ['save', 'P_hitted', 'RBI'] 	 0.8394660402270857
    ['save', 'WHIP', 'scoring'] 	 0.8226969751811254
    ['save', 'WHIP', 'RBI'] 	 0.826837586936176
    ['save', 'WHIP', 'OPS'] 	 0.83770211967181
    ['save', 'P_AVG', 'AVG'] 	 0.833675779191964
    ['save', 'P_AVG', 'scoring'] 	 0.843404247227208
    ['save', 'P_AVG', 'RBI'] 	 0.8412233945434199
    ['save', 'P_AVG', 'OPS'] 	 0.8254545921952229
    

- correlation heatmap으로 종속변수와 독립변수 간 상관관계 확인


```python
plt.figure(figsize=(5,5))
sns.heatmap(data = df[['win_rate','ERA', 'OPS']].corr(), annot = True)
plt.show()
```


<img width="316" alt="프로야구 팀시즌 승률예측을 위한 선형회귀모델 구현결과_23_0" src="https://user-images.githubusercontent.com/41605276/59485175-9f077d80-8eaf-11e9-95b5-f0a747238ea2.png">


- 독립변수 간 VIF 지수 점검

VIF 지수 : 특정 독립변수가 다른 독립변수에 얼마나 의존적인지 숫자로 표현한 지수. 통상적으로 10을 기준으로 의존적이다, 의존적이지 않다 판단

VIF 지수가 다소 높게 측정되었으나 예측성능과 condition number에 큰 영향을 주지 않는 것으로 보아 다중공선성이 없는 것으로 판단


```python
df2 = df[['ERA', 'OPS']]

vif = pd.DataFrame()
vif["VIF Factor"] = [variance_inflation_factor(df2.values, i) for i in range(df2.shape[1])]
vif["features"] = df2.columns
vif.sort_values(["VIF Factor"], ascending=[False])
```

![6](https://user-images.githubusercontent.com/41605276/59485404-ab400a80-8eb0-11e9-8e9b-720eddb1be6a.png)

#### STEP 5) 모델링 및 모델평가

1) 모델 구현


```python
X = dfX[['ERA', 'OPS','const']]
y = dfy[["win_rate"]]

model = sm.OLS(y, X)
result = model.fit()
result.summary()
```

![5](https://user-images.githubusercontent.com/41605276/59485205-c52d1d80-8eaf-11e9-95b1-072f5ddd55c9.png)


2) 부분회귀로 각각의 독립변수로 종속변수에 대해서 실질적인 회귀성능 점검


```python
fig = plt.figure(figsize=(10, 10))
sm.graphics.plot_partregress_grid(result, fig=fig)
fig.suptitle("")
plt.show()
```


<img width="711" alt="프로야구 팀시즌 승률예측을 위한 선형회귀모델 구현결과_29_0" src="https://user-images.githubusercontent.com/41605276/59485221-d37b3980-8eaf-11e9-96dd-84ec091645d8.png">


3) 실제 데이터와 모델 예측값 비교


```python
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 101)

plt.figure(figsize=(8, 5))
plt.scatter(y_test, result.predict(X_test))
plt.xlabel('real value')
plt.ylabel('predicted value')
plt.show()
```


<img width="510" alt="프로야구 팀시즌 승률예측을 위한 선형회귀모델 구현결과_31_0" src="https://user-images.githubusercontent.com/41605276/59485228-dc6c0b00-8eaf-11e9-8465-8b397016a0f3.png">


- 2019 시즌데이터 적용


```python
kiwoom = result.predict([4.08,0.757,1])
doosan = result.predict([3.31,0.757,1])
sk = result.predict([3.53,0.716,1])
KIA = result.predict([4.85,0.724,1])
NC = result.predict([4.08,0.781,1])
SAMSUNG = result.predict([4.24,0.736,1])

print("순서       : 키움, 두산, SK, 기아 NC 삼성")
print("모델예측치 :", round(kiwoom[0],3), round(doosan[0],3), round(sk[0],3), round(KIA[0],3), round(NC[0],3), round(SAMSUNG[0],3))
print("실제       : 0.543 0.623 0.657 0.418 0.537 0.433")
```

    순서       : 키움, 두산, SK, 기아 NC 삼성
    모델예측치 : 0.537 0.611 0.539 0.422 0.567 0.496
    실제       : 0.543 0.623 0.657 0.418 0.537 0.433
    

4) 잔차정규성 검정

- QQ Plot 드로잉 시 잔차정규성 가정을 만족하는 빨간색 대각선과 유사


- 카이제곱 검정 시 p-value 70%로 잔차정규성 통과하는 것으로 판단

=> 잔차정규성을 충족하여 확률론적 선형회귀모형의 가정을 올바르게 충족한다고 판단


```python
plt.figure(figsize=(8, 5))
sp.stats.probplot(result.resid, plot=plt)
plt.show()
```


<img width="517" alt="프로야구 팀시즌 승률예측을 위한 선형회귀모델 구현결과_35_0" src="https://user-images.githubusercontent.com/41605276/59485233-e68e0980-8eaf-11e9-9059-c0335d9e0cee.png">



```python
test = sm.stats.omni_normtest(result.resid)
for xi in zip(['Chi^2', 'P-value'], test):
    print("%-12s: %6.3f" % xi)
```

    Chi^2       :  0.713
    P-value     :  0.700
    

5) Kfold 교차검증


```python
df = pd.concat([X,y],axis=1)

scores = np.zeros(5)
cv = KFold(5, shuffle=True, random_state=0)
for i, (idx_train, idx_test) in enumerate(cv.split(df)):
    df_train = df.iloc[idx_train]
    df_test = df.iloc[idx_test]
    
    model = sm.OLS(df_train.win_rate, df_train[['OPS', 'ERA','const']])
    result = model.fit()

    pred = result.predict(df_test[['OPS', 'ERA','const']])
    rss = ((df_test.win_rate - pred) ** 2).sum()
    tss = ((df_test.win_rate - df_test.win_rate.mean()) ** 2).sum()
    rsquared = 1 - rss / tss
    
    scores[i] = rsquared
    print("train R2 = {:.8f}, test R2 = {:.8f}".format(result.rsquared, rsquared))
    
print("test 퍼포먼스 평균 : ", scores.mean())
```

    train R2 = 0.80075343, test R2 = 0.92721464
    train R2 = 0.83360177, test R2 = 0.86415957
    train R2 = 0.84976854, test R2 = 0.77054431
    train R2 = 0.84717910, test R2 = 0.79771835
    train R2 = 0.86177633, test R2 = 0.70430950
    test 퍼포먼스 평균 :  0.8127892746444972