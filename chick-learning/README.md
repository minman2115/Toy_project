### [개요]

치킨이미지를 인식하여 치킨브랜드(BBQ, 네네, 교촌 등)를 분류할 수 있는 CNN(MobileNet을 fine tuning한 형태) 모델 구현 및 AWS Endpoint 배포

### [구현과정]

STEP 1) 아이디어 도출

STEP 2) 데이터수집 : 인스타그램에서 크롤러를 이용하여 치킨브랜드별로 키워드 검색하여 치킨이미지 수집

STEP 3) 모델링 : AWS Sagemaker의 Tensorflow 2.0을 이용하여 치킨이미지를 분류할 수 있는 CNN(MobileNet을 fine tuning한 형태) 구현

STEP 4) 트레이닝 및 배포

### [구현결과]

#### STEP 1) 아이디어 도출

- 인스타그램에서 크롤링한 치킨이미지 데이터를 input 값으로 넣어주면 ouput 값으로 치킨브랜드 이름을 분류하는 치믈리에 머신러닝 구현

#### STEP 2) 데이터 수집

- 인스타그램 웹크롤러를 이용한 데이터 수집


- 사용한 웹크롤러 : https://github.com/huaying/instagram-crawler


- 이슈 : 순수한 치킨 사진 외 관련 없는 사진도 수집되는 현상 식별


- 해결방안 : 순수한 치킨 사진 감별 및 불필요한 사진 데이터 제거


결론적으로 4개의 브랜드(BBQ, 굽네, 교촌, 네네), 브랜드별 170장의 치킨이미지 데이터 수집

#### STEP 3) 모델링

- 데이터 전처리


```python
import tensorflow as tf
import argparse
import numpy as np
import json
import os, sys
from PIL import Image
from sklearn.preprocessing import LabelEncoder
from sklearn.utils import shuffle
import boto3
import pandas as pd
import s3fs
from keras.utils import np_utils
import io
import pickle

## Target 데이터에 대한 라벨링을 수행하는 함수
def Label_encoding(target_data):
    le = LabelEncoder()
    le.fit(target_data)
    arget_data = le.transform(target_data)
    target_data = np_utils.to_categorical(target_data, len(brend_names))
    return target_data

## 데이터 전처리를 수행하는 함수
def process_data():
    
    brend_names = ['BBQ','goobne', 'kyochon', 'nene']

    img_data = []
    target_data = []

    # 이미지 데이터 탑재한 S3에 접근
    fs = s3fs.S3FileSystem()
    
    # 브랜드별 이미지 처리
    for brend in brend_names:

        s3_data_list = fs.ls('s3://lhw-s3-test/sagemaker_test/brend/' + brend)

        for data in s3_data_list[0:170+1]:
            with fs.open('s3://{}'.format(data)) as f:
                img = Image.open(f)

                resize_img = img.resize((240,240))
                array_of_img = np.array(resize_img)

                img_data.append(array_of_img.reshape(240,240, 3).astype('float32') / 255.0)
                target_data.append(brend)
                
    img_data = np.array(img_data)
    
    target_data = Label_encoding(target_data)
    
    # train, test split
    x, y = shuffle(img_data, target_data, random_state=42)

    x_train = x[:600+1]
    y_train = y[:600+1]

    x_test = x[600:]
    y_test = y[600:]
    
    np.save('train_data', x_train)
    np.save('train_labels', y_train)
    np.save('eval_data', x_test)
    np.save('eval_labels', y_test)
    
    
    ## s3에 전처리한 데이터를 저장
    s3 = boto3.resource('s3')
    s3.Object('lhw-s3-test', 'sagemaker_test/dataset/train_data.npy').put(Body=open('train_data.npy', 'rb'))
    s3.Object('lhw-s3-test', 'sagemaker_test/dataset/train_labels.npy').put(Body=open('train_labels.npy', 'rb'))
    s3.Object('lhw-s3-test', 'sagemaker_test/dataset/eval_data.npy').put(Body=open('eval_data.npy', 'rb'))
    s3.Object('lhw-s3-test', 'sagemaker_test/dataset/eval_labels.npy').put(Body=open('eval_labels.npy', 'rb'))
                                         
    return None

process_data()
```

- 모델링(chick_learning.py)


```python
import tensorflow as tf
import argparse
import numpy as np
import json
import os, sys
from tensorflow import keras
from tensorflow.keras import models
from tensorflow.keras import optimizers
from tensorflow.keras.preprocessing import image
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications.mobilenet import MobileNet, preprocess_input
from tensorflow.keras.layers import Conv2D, ReLU, MaxPooling2D, Dense, BatchNormalization, Softmax, GlobalAveragePooling2D

def model(x_train, y_train, x_test, y_test):
    
    learning_rate = 0.0002
    batch_size = 16
    n_train = 601
    n_class = 4
    
    conv_base = MobileNet(weights='imagenet',include_top=False,input_shape=(240, 240, 3))
    model = models.Sequential()
    model.add(conv_base)
    model.add(GlobalAveragePooling2D())
    model.add(Dense(256))
    model.add(BatchNormalization())
    model.add(ReLU())
    model.add(Dense(n_class))
    model.add(BatchNormalization())
    model.add(Softmax())
    lr_schedule = keras.optimizers.schedules.ExponentialDecay(initial_learning_rate=0.0002, 
                                                              decay_steps=n_train//batch_size*5,
                                                              decay_rate=0.5,
                                                              staircase=True)
    model.compile(optimizers.Adam(lr_schedule), loss='categorical_crossentropy', metrics=['accuracy'])
    model.fit(x_train, y_train, epochs = 10, batch_size = 10, validation_data = (x_test,y_test))
    model.evaluate(x_test, y_test)
    return model

def _load_training_data(base_dir):
    x_train = np.load(os.path.join(base_dir, 'train_data.npy'))
    y_train = np.load(os.path.join(base_dir, 'train_labels.npy'))
    return x_train, y_train


def _load_testing_data(base_dir):
    x_test = np.load(os.path.join(base_dir, 'eval_data.npy'))
    y_test = np.load(os.path.join(base_dir, 'eval_labels.npy'))
    return x_test, y_test


def _parse_args():
    parser = argparse.ArgumentParser()

    # Data, model, and output directories
    # model_dir is always passed in from SageMaker. By default this is a S3 path under the default bucket.
    parser.add_argument('--model_dir', type=str)
    parser.add_argument('--sm-model-dir', type=str, default=os.environ.get('SM_MODEL_DIR'))
    parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAINING'))
    parser.add_argument('--hosts', type=list, default=json.loads(os.environ.get('SM_HOSTS')))
    parser.add_argument('--current-host', type=str, default=os.environ.get('SM_CURRENT_HOST'))

    return parser.parse_known_args()


if __name__ == "__main__":
    args, unknown = _parse_args()
    
    train_data, train_labels = _load_training_data(args.train)
    eval_data, eval_labels = _load_testing_data(args.train)
    
    CNN_classifier = model(train_data, train_labels, eval_data, eval_labels)

    if args.current_host == args.hosts[0]:
        # save model to an S3 directory with version number '00000001'
        CNN_classifier.save(os.path.join(args.sm_model_dir, '000000001'), 'my_model.h5')
```

#### STEP 4) 트레이닝 및 배포

- 트레이닝 (Sagemaker 훈련 및 모델등록)

아래 코드를 실행하면 모델이 트레이닝되고 등록이 된다. 그리고 S3에 훈련이 완료된 모델이 저장된다


```python
from sagemaker.tensorflow import TensorFlow
import os
import sagemaker
from sagemaker import get_execution_role

sagemaker_session = sagemaker.Session()

role = get_execution_role()
region = sagemaker_session.boto_session.region_name

training_data_uri = 's3://lhw-s3-test/sagemaker_test/dataset'

CNN_estimator = TensorFlow(entry_point='chick_learning.py',
                             role=role,
                             train_instance_count=1,
                             train_instance_type='ml.p2.xlarge',
                             framework_version='2.0.0',
                             py_version='py3',
                             distributions={'parameter_server': {'enabled': True}})

CNN_estimator.fit(training_data_uri)
```

![1](https://user-images.githubusercontent.com/41605276/75853841-3a6fc280-5e32-11ea-9fa2-06fd819c68dd.png)

- 배포(Sagemaker 앤드포인트 등록)

아래 코드를 실행하면 S3에 훈련이 완료된 모델을 베이스로 Sagemaker 앤드포인트를 생성하게 된다.


```python
predictor = CNN_estimator.deploy(initial_instance_count=1, instance_type='ml.p2.xlarge')
```

![2](https://user-images.githubusercontent.com/41605276/75853869-42c7fd80-5e32-11ea-9cef-701e357161a8.png)
