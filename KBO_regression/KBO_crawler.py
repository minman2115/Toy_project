from selenium import webdriver
from selenium.webdriver.support.ui import Select
import pandas as pd
import time

## 크롤러 구현
class crawler:
    
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('headless')            
        self.driver = webdriver.Chrome(options=self.options)
        
    def make_season_table_df(self, season):
        
        url = 'https://www.koreabaseball.com/TeamRank/TeamRank.aspx'

        self.driver.get(url)

        select = Select(self.driver.find_element_by_name('ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$ddlYear'))
        select.select_by_visible_text(season)

        time.sleep(2)

        items = self.driver.find_elements_by_css_selector("#cphContents_cphContents_cphContents_udpRecord > table > tbody > tr")

        dict_list = []

        for item in items:
            rank = item.find_element_by_css_selector("td:nth-child(1)").text
            team = item.find_element_by_css_selector("td:nth-child(2)").text
            num_game = item.find_element_by_css_selector("td:nth-child(3)").text
            win_rate = item.find_element_by_css_selector("td:nth-child(7)").text

            data = {
                "rank" : rank,
                "team" : team,
                'num_game' : num_game, # 시즌게임수
                "win_rate" : win_rate # 승률
            }

            dict_list.append(data)

        df = pd.DataFrame(dict_list)
        df = df[['num_game',"team","rank","win_rate"]]
        df['team'] = df['team'].apply(lambda data : "{}_".format(season) + data)

        return df
    
    def make_hitter_df(self, season):

        url = 'https://www.koreabaseball.com/Record/Team/Hitter/Basic1.aspx'

        self.driver.get(url)

        select = Select(self.driver.find_element_by_name('ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$ddlSeason$ddlSeason'))
        select.select_by_visible_text(season)

        time.sleep(2)

        items = self.driver.find_elements_by_css_selector("#cphContents_cphContents_cphContents_udpContent > div.record_result > table > tbody > tr")

        dict_list = []

        for item in items:
            team = item.find_element_by_css_selector("td:nth-child(2)").text
            avg = item.find_element_by_css_selector("td:nth-child(3)").text
            r = item.find_element_by_css_selector("td:nth-child(7)").text
            h = item.find_element_by_css_selector("td:nth-child(8)").text
            double = item.find_element_by_css_selector("td:nth-child(9)").text
            triple = item.find_element_by_css_selector("td:nth-child(10)").text
            HR = item.find_element_by_css_selector("td:nth-child(11)").text
            RBI = item.find_element_by_css_selector("td:nth-child(13)").text
            SAC = item.find_element_by_css_selector("td:nth-child(14)").text
            SF = item.find_element_by_css_selector("td:nth-child(15)").text

            data = {
                "team" : team,
                "AVG" : avg, # 타율
                "scoring" : r, # 득점
                "hit" : h,
                "double" : double,
                'triple' : triple,
                'HR' : HR,
                'RBI' : RBI, # 타점
                'SAC' : SAC, # 희생번트
                'SF' : SF # 희생플라이
            }

            dict_list.append(data)

        df1 = pd.DataFrame(dict_list)
        df1 = df1[["team","AVG","scoring","hit","double",'triple','HR','RBI','SAC','SF']]
        df1['team'] = df1['team'].apply(lambda data : "{}_".format(season) + data)

        url = 'https://www.koreabaseball.com/Record/Team/Hitter/Basic2.aspx'

        self.driver.get(url)

        select = Select(self.driver.find_element_by_name('ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$ddlSeason$ddlSeason'))
        select.select_by_visible_text(season)

        time.sleep(2)

        items = self.driver.find_elements_by_css_selector("#cphContents_cphContents_cphContents_udpContent > div.record_result > table > tbody > tr")

        dict_list = []

        for item in items:
            team = item.find_element_by_css_selector("td:nth-child(2)").text
            OPS = item.find_element_by_css_selector("td:nth-child(11)").text
            RISP = item.find_element_by_css_selector("td:nth-child(13)").text
            PA_BA = item.find_element_by_css_selector("td:nth-child(14)").text

            data = {
                "team" : team,
                "OPS" : OPS,
                "RISP" : RISP, # 득점권타율
                "PA_BA" : PA_BA, # 대타타율
            }

            dict_list.append(data)

        df2 = pd.DataFrame(dict_list)
        df2 = df2[['team',"OPS","RISP","PA_BA"]]
        df2['team'] = df2['team'].apply(lambda data : "{}_".format(season) + data)

        return pd.merge(df1, df2)
    
    def make_pitcher_df(self,season):
    
        url = 'https://www.koreabaseball.com/Record/Team/Pitcher/Basic1.aspx'

        dict_list = []

        self.driver.get(url)

        select = Select(self.driver.find_element_by_name('ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$ddlSeason$ddlSeason'))
        select.select_by_visible_text(season)

        time.sleep(2)

        items = self.driver.find_elements_by_css_selector("#cphContents_cphContents_cphContents_udpContent > div.record_result > table > tbody > tr")

        for item in items:
            team = item.find_element_by_css_selector("td:nth-child(2)").text
            era = item.find_element_by_css_selector("td:nth-child(3)").text
            save = item.find_element_by_css_selector("td:nth-child(7)").text
            hold = item.find_element_by_css_selector("td:nth-child(8)").text
            PW = item.find_element_by_css_selector("td:nth-child(9)").text
            P_hitted = item.find_element_by_css_selector("td:nth-child(11)").text
            SO = item.find_element_by_css_selector("td:nth-child(15)").text
            WHIP = item.find_element_by_css_selector("td:nth-child(18)").text

            data = {
                'team' : team,
                "ERA" : era, # 평균자책점
                "save" : save,
                'hold' : hold,
                'PW' : PW, # 선발투수 승률
                'P_hitted' : P_hitted, # 피안타
                'SO' : SO, # 탈삼진
                'WHIP' : WHIP
            }

            dict_list.append(data)


        df1 = pd.DataFrame(dict_list)
        df1 = df1[["team","ERA",'save','hold','PW','P_hitted','SO','WHIP']]
        df1['team'] = df1['team'].apply(lambda data : "{}_".format(season) + data)

        url = 'https://www.koreabaseball.com/Record/Team/Pitcher/Basic2.aspx'

        dict_list = []

        self.driver.get(url)

        select = Select(self.driver.find_element_by_name('ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$ddlSeason$ddlSeason'))
        select.select_by_visible_text(season)

        time.sleep(2)

        items = self.driver.find_elements_by_css_selector("#cphContents_cphContents_cphContents_udpContent > div.record_result > table > tbody > tr")

        for item in items:
            team = item.find_element_by_css_selector("td:nth-child(2)").text
            CG = item.find_element_by_css_selector("td:nth-child(4)").text
            SHO = item.find_element_by_css_selector("td:nth-child(5)").text
            QS = item.find_element_by_css_selector("td:nth-child(6)").text
            BSV = item.find_element_by_css_selector("td:nth-child(7)").text
            NP = item.find_element_by_css_selector("td:nth-child(9)").text
            P_AVG = item.find_element_by_css_selector("td:nth-child(10)").text
            WP = item.find_element_by_css_selector("td:nth-child(16)").text

            data = {
                'team' : team,
                "CG" : CG, # 완투
                "shutout" : SHO, # 완봉
                'QS' : QS,
                'BV' : BSV,
                'PN' : NP, # 투구수
                'P_AVG' : P_AVG, # 피안타율
                'WP' : WP # 와일드피치
            }

            dict_list.append(data)

        df2 = pd.DataFrame(dict_list)
        df2 = df2[["team","CG",'shutout','QS','BV','PN','P_AVG','WP']]
        df2['team'] = df2['team'].apply(lambda data : "{}_".format(season) + data)

        return pd.merge(df1, df2)
    
    def make_defense_df(self, season):

        url = 'https://www.koreabaseball.com/Record/Team/Defense/Basic.aspx'

        dict_list = []

        self.driver.get(url)

        select = Select(self.driver.find_element_by_name('ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$ddlSeason$ddlSeason'))
        select.select_by_visible_text(season)

        time.sleep(2)

        items = self.driver.find_elements_by_css_selector("#cphContents_cphContents_cphContents_udpContent > div.record_result > table > tbody > tr")

        for item in items:
            team = item.find_element_by_css_selector("td:nth-child(2)").text
            error = item.find_element_by_css_selector("td:nth-child(4)").text

            data = {
                'team' : team,
                "error" : error
            }

            dict_list.append(data)

        df = pd.DataFrame(dict_list)
        df = df[["team","error"]]
        df['team'] = df['team'].apply(lambda data : "{}_".format(season) + data)

        return df
    
    def make_comprehensive_table(self, season):
    
        season_table = self.make_season_table_df(season)
        pitcher_table = self.make_pitcher_df(season)
        hitter_table = self.make_hitter_df(season)
        defense_table = self.make_defense_df(season)
        
        df_1 = pd.merge(season_table, pitcher_table)
        df_2 = pd.merge(hitter_table, defense_table)
        
        return pd.merge(df_1, df_2)
    
    def make_season_accumulation_df(self,start,end):
        
        temp = str(start)
        
        df = self.make_comprehensive_table(temp)
        
        for season in range(start+1,end+1):
            season = str(season)
            df2 = self.make_comprehensive_table(season)
            df = pd.concat([df,df2])
            
        return df
    
if __name__ == '__main__':
    
    crawler = crawler()
    print("Crawling start")

    startTime = time.time()

    df = crawler.make_season_accumulation_df(2001,2018)

    endTime = time.time() - startTime
    print("Crawling complete, endtime :  ", endTime) 

    df = df.reset_index()
    df.drop(['index'],axis=1,inplace=True)
    print("reset indexing complete")

    # 크롤링한 데이터 저장
    df.to_pickle("KBO_record.plk")
    print("KBO_record.plk save complete, program done!")