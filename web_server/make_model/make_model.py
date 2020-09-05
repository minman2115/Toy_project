from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import pandas as pd
import pickle

# 기사 데이터 프레임 로드
article_df = pd.read_pickle("naver_article.plk")

# x,y 분류
x_train = article_df.content
y_train = article_df.category

# vectorizer와 classification algorithm 설정
clf = Pipeline([
    ('vect', TfidfVectorizer()), 
    ('clf', MultinomialNB(alpha=0.01)) 
])

# 모델 생성
model = clf.fit(x_train, y_train) 

# 객체를 pickled binary file 형태로 저장한다 
file_name = 'classification_model.pkl' 
with open(file_name, 'wb') as file_name:
    pickle.dump(model, file_name)

print('job done!')