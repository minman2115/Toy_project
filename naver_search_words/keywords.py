# -*- coding: utf-8 -*- 

import os
import sys
sys.path.append(os.path.abspath("/home/ubuntu/.pyenv/versions/python3/lib/python3.6/site-packages/"))

import requests
import json
import pymongo
from bs4 import BeautifulSoup
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

base = declarative_base()
# SQLalchemy 사용을 위한 매핑선언

class sqlalchemy_mapping(base):
    __tablename__ = "naver"

    id = Column(Integer, primary_key=True)
    rank = Column(Integer, nullable=False)
    keyword = Column(String(50), nullable=False)
    rdate = Column(TIMESTAMP, nullable=False)

    def __init__(self, rank, keyword):
        self.rank = rank
        self.keyword = keyword

    def __repr__(self):
        return "<NaverKeyword {}, {}>".format(self.rank, self.keyword)

class NaverKeywords:
    
    def __init__(self, ip, base):
        self.mysql_client = create_engine("mysql://root:{}@{}/naver_keywords?charset=utf8".format(os.environ["pw"],ip))
        self.mongo_client = pymongo.MongoClient('mongodb://{}:27017'.format(ip))
        self.datas = None
        self.base = base
        
    def naver_crawling(self):
        response = requests.get("https://www.naver.com/")
        dom = BeautifulSoup(response.content, "html.parser")
        keywords = dom.select(".ah_roll_area > .ah_l > .ah_item")
        datas = []
        for keyword in keywords:
            rank = keyword.select_one(".ah_r").text
            keyword = keyword.select_one(".ah_k").text
            datas.append((rank, keyword))
        self.datas = datas
    
    
    def mysql_save(self):
        
        # make table
        self.base.metadata.create_all(self.mysql_client)
        
        # parsing keywords
        keywords = [sqlalchemy_mapping(rank, keyword) for rank, keyword in self.datas]

        # make session
        maker = sessionmaker(bind=self.mysql_client)
        session = maker()

        # save datas
        session.add_all(keywords)
        session.commit()

        # close session
        session.close()
        
    def mongo_save(self):
        
        rdate = datetime.utcnow()
        
        # parsing querys
        keywords = [{"rank":rank, "keyword":keyword, "rdate": rdate} for rank, keyword in self.datas]
        
        # insert keyowrds
        self.mongo_client.naver_crawling.naver_keywords.insert(keywords)
        
    def send_slack(self, msg, channel="#dss", username="minman_bot" ):
        webhook_URL = "https://hooks.slack.com/services/<슬랙웹훅토큰>"
        payload = {
            "channel": channel,
            "username": username,
            "icon_emoji": ":provision:",
            "text": msg,
        }
        response = requests.post(
            webhook_URL,
            data = json.dumps(payload),
        )
    
    def run(self):
        self.naver_crawling()
        self.mysql_save()
        self.mongo_save()
        self.send_slack("naver crawling done!")
        print("execute done!")

nk = NaverKeywords(os.environ["id"], base)
nk.run()